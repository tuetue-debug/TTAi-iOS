"""Chat v2 API routes — conversations, streaming messages, memory, projects.

Streaming flow:
  Browser → /chat-api/.../messages (cookie auth)
    → check_quota_allowance (billing_store)
    → query_classifier.classify()
    → load_balancer.select_provider()  ← real model selection + fallback
    → ollama_service.stream_chat()     ← real SSE to browser
    → _log_usage() background          ← usage_events.jsonl
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from billing_store import check_quota_allowance
from chat_store import (
    GUEST_MESSAGE_LIMIT,
    add_message,
    create_conversation,
    create_project,
    delete_conversation,
    delete_project,
    delete_user_memory,
    export_feedback_jsonl,
    get_conversation,
    get_or_create_guest_session,
    get_user_memory,
    guest_limit_reached,
    increment_guest_count,
    list_conversations,
    list_messages,
    list_projects,
    save_feedback_sample,
    set_user_memory,
    touch_conversation,
    update_conversation_title,
    update_feedback_vote,
    update_project,
)
from load_balancer import load_balancer, ProviderType
from ollama_service import ollama_service
from query_classifier import query_classifier
from web_search_service import web_search_service
from rag_service import (
    build_system_prompt_async,
    extract_memory_from_conversation,
    generate_conversation_title,
    init_vector_table,
)
from user_auth import USER_REPOSITORY, verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

PORTAL_SESSION_COOKIE = "ttai_portal_session"
_DATA_DIR = Path(__file__).resolve().parent / "data"
_USAGE_EVENTS_PATH = _DATA_DIR / "usage_events.jsonl"


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _get_portal_user(
    portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE),
) -> dict | None:
    if not portal_session:
        return None
    try:
        payload = verify_token(portal_session)
        user = USER_REPOSITORY.get_user_by_id(str(payload.get("sub")))
        if user and user.get("is_active"):
            return user
    except Exception:
        pass
    return None


def _require_user(user=Depends(_get_portal_user)) -> dict:
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


# ── Models endpoint ────────────────────────────────────────────────────────────

@router.get("/chat-api/models")
async def get_models(user=Depends(_get_portal_user)):
    """Return available providers from the load balancer."""
    try:
        names = [
            p.name
            for pt, plist in load_balancer.providers.items()
            for p in plist
            if p.enabled and pt.value in ("ollama_local", "ollama_remote")
        ]
        if names:
            return {"models": names}
    except Exception as e:
        logger.warning("Could not list providers from load_balancer: %s", e)
    return {"models": ["gemma3:4b-remote"]}


# ── Conversations ──────────────────────────────────────────────────────────────

class NewConversationRequest(BaseModel):
    model: str = "auto"
    project_id: str | None = None


@router.get("/chat-api/conversations")
async def get_conversations(
    request: Request,
    user=Depends(_get_portal_user),
):
    guest_header = request.headers.get("x-guest-session")
    if user:
        convs = list_conversations(user_id=str(user["id"]))
    elif guest_header:
        convs = list_conversations(session_id=guest_header)
    else:
        convs = []
    return {"conversations": convs}


@router.post("/chat-api/conversations")
async def new_conversation(
    body: NewConversationRequest,
    request: Request,
    user=Depends(_get_portal_user),
):
    guest_header = request.headers.get("x-guest-session")
    cid = create_conversation(
        user_id=str(user["id"]) if user else None,
        session_id=guest_header if not user else None,
        model=body.model,
        project_id=body.project_id if user else None,
    )
    return {"id": cid, "model": body.model}


@router.get("/chat-api/conversations/{conv_id}")
async def get_conversation_detail(conv_id: str, user=Depends(_get_portal_user), request: Request = None):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    _assert_access(conv, user, request)
    msgs = list_messages(conv_id)
    return {"conversation": conv, "messages": msgs}


@router.delete("/chat-api/conversations/{conv_id}")
async def remove_conversation(conv_id: str, user=Depends(_get_portal_user), request: Request = None):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    _assert_access(conv, user, request)
    delete_conversation(conv_id)
    return {"ok": True}


def _assert_access(conv: dict, user, request):
    if user:
        if conv.get("user_id") and str(conv["user_id"]) != str(user["id"]):
            raise HTTPException(403, "Access denied")
    else:
        guest_id = request.headers.get("x-guest-session") if request else None
        if conv.get("session_id") and conv["session_id"] != guest_id:
            raise HTTPException(403, "Access denied")


# ── Streaming chat ─────────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    content: str
    model: str | None = None  # ignored — load_balancer auto-selects


@router.post("/chat-api/conversations/{conv_id}/messages")
async def send_message(
    conv_id: str,
    body: SendMessageRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    user=Depends(_get_portal_user),
):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")

    guest_header = request.headers.get("x-guest-session")

    # Guest rate limiting
    if not user:
        if not guest_header:
            raise HTTPException(401, "Guest session required")
        get_or_create_guest_session(guest_header, request.client.host if request.client else "unknown")
        if guest_limit_reached(guest_header):
            raise HTTPException(
                429,
                f"Guest limit reached ({GUEST_MESSAGE_LIMIT} messages). Please sign up to continue.",
            )

    # Build conversation history
    history = list_messages(conv_id)
    is_first_message = len(history) == 0

    # Build system prompt with memory + RAG context
    memory = get_user_memory(str(user["id"])) if user else {}
    project_id = conv.get("project_id")
    system_prompt = await build_system_prompt_async(
        memory, project_id, str(user["id"]) if user else None, query=body.content
    )

    # Assemble messages for Ollama /api/chat format
    ollama_messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-30:]:
        ollama_messages.append({"role": msg["role"], "content": msg["content"]})
    ollama_messages.append({"role": "user", "content": body.content})

    # Save user message immediately
    add_message(conv_id, "user", body.content)
    touch_conversation(conv_id)

    if is_first_message:
        background_tasks.add_task(_set_title_bg, conv_id, body.content)

    return StreamingResponse(
        _stream_response(
            conv_id=conv_id,
            content=body.content,
            messages=ollama_messages,
            user_id=str(user["id"]) if user else None,
            guest_session=guest_header if not user else None,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_response(
    conv_id: str,
    content: str,
    messages: list,
    user_id: str | None,
    guest_session: str | None,
    background_tasks: BackgroundTasks,
) -> AsyncIterator[str]:
    effective_uid = user_id or f"guest:{guest_session}"

    # Quota check
    try:
        quota = check_quota_allowance(user_id=effective_uid, api_key_id=None)
        if not quota.get("allowed"):
            yield _sse({"type": "error", "content": f"Quota exceeded: {quota.get('reason', 'limit reached')}"})
            return
    except Exception as e:
        logger.warning("Quota check error (continuing): %s", e)

    # Provider selection via load balancer
    provider = None
    try:
        classification = query_classifier.classify(content)
        provider = await load_balancer.select_provider(
            classification,
            request_id=str(uuid.uuid4()),
            query=content,
        )
    except Exception as e:
        logger.error("Provider selection failed: %s", e)

    if not provider:
        yield _sse({"type": "error", "content": "No AI provider available. Please try again later."})
        return

    # Base URL from provider endpoint (strip /api/... suffix)
    base_url = (
        provider.endpoint.rsplit("/api/", 1)[0]
        if "/api/" in provider.endpoint
        else provider.endpoint
    )

    # ── AI-driven search decision + injection ─────────────────────────────────
    # Step 1: LLM quyết định có cần search không và query nào
    yield _sse({"type": "status", "content": "Đang phân tích câu hỏi..."})
    ai_decision = await _ai_search_decision(content, base_url, provider.model)

    # Fallback sang keyword classifier nếu LLM decision thất bại/timeout
    if ai_decision is None:
        search_needed = bool(classification and classification.needs_realtime)
        search_query  = content
        logger.info("Search decision: keyword fallback → needs_realtime=%s", search_needed)
    else:
        search_needed = ai_decision["search"]
        search_query  = ai_decision["query"]
        logger.info("Search decision: AI → search=%s query=%r", search_needed, search_query)

    # Step 2: Thực hiện search nếu cần
    if search_needed:
        try:
            yield _sse({"type": "status", "content": f"🔍 Đang tìm: {search_query}..."})
            search_docs = await web_search_service.search(search_query, max_results=8)
            if search_docs:
                top_docs = web_search_service.bm25_rerank(search_query, search_docs, top_k=5)
                ctx = web_search_service.build_context_block(search_query, search_docs)
                sources = [
                    {"index": i + 1, "title": d["title"], "url": d["url"]}
                    for i, d in enumerate(top_docs)
                ]
                yield _sse({"type": "sources", "sources": sources})
                # Step 3: Inject context — yêu cầu LLM tổng hợp từ bài báo
                messages[-1]["content"] = (
                    f"Đọc kỹ các đoạn văn bản báo chí dưới đây và TÓM TẮT thông tin để trả lời câu hỏi.\n"
                    f"Yêu cầu bắt buộc:\n"
                    f"- Trích xuất TẤT CẢ các con số cụ thể: giá (đồng/lít, đồng/chỉ, VNĐ/USD...), "
                    f"phần trăm thay đổi, ngày điều chỉnh.\n"
                    f"- Ghi rõ đơn vị: xăng → đồng/lít, vàng → đồng/chỉ hoặc triệu/lượng, "
                    f"ngoại tệ → VNĐ/USD.\n"
                    f"- Trích dẫn nguồn [1],[2]... sau mỗi con số.\n"
                    f"- KHÔNG bịa số liệu — chỉ tóm tắt những gì có trong văn bản.\n"
                    f"Câu hỏi: {content}\n\n"
                    f"--- Nội dung bài báo ---\n{ctx}"
                )
            else:
                yield _sse({"type": "status", "content": "Không tìm thấy kết quả phù hợp, trả lời từ kiến thức..."})
        except Exception as e:
            logger.warning("Web search failed (continuing without): %s", e)
            yield _sse({"type": "status", "content": "Tìm kiếm thất bại, trả lời từ kiến thức..."})
    else:
        # Không cần search — xóa status "Đang phân tích..." bằng cách emit rỗng
        yield _sse({"type": "status", "content": ""})

    full_response: list[str] = []
    try:
        async for chunk in ollama_service.stream_chat(
            model=provider.model,
            messages=messages,
            base_url=base_url,
        ):
            text = chunk.get("message", {}).get("content", "")
            if text:
                full_response.append(text)
                yield _sse({"type": "content", "content": text})

            if chunk.get("done"):
                break

        complete = "".join(full_response)
        if complete:
            msg_id = add_message(conv_id, "assistant", complete)
            touch_conversation(conv_id)
            yield _sse({"type": "done", "message_id": msg_id, "conv_id": conv_id, "model": provider.name})

            if user_id and len(complete) > 100:
                background_tasks.add_task(extract_memory_from_conversation, user_id, conv_id)

            background_tasks.add_task(_log_usage, effective_uid, provider, content, complete)
            background_tasks.add_task(
                save_feedback_sample,
                message_id=msg_id,
                conv_id=conv_id,
                user_id=user_id,
                question=content,
                response=complete,
                model_used=provider.model,
                provider=provider.name,
            )

        if guest_session:
            increment_guest_count(guest_session)

    except Exception as e:
        logger.error("Stream error: %s", e)
        complete = "".join(full_response)
        if complete:
            msg_id = add_message(conv_id, "assistant", complete)
            touch_conversation(conv_id)
            yield _sse({"type": "done", "message_id": msg_id, "conv_id": conv_id})
        else:
            yield _sse({"type": "error", "content": "Connection error. Please try again."})


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ── AI-driven search decision ──────────────────────────────────────────────────

_DECISION_SYSTEM = """Bạn là agent quyết định tìm kiếm. Phân tích câu hỏi và trả về JSON.

Cần tìm kiếm web khi câu hỏi hỏi về:
- Giá cả thời gian thực: xăng, vàng, đô, tỷ giá, chứng khoán, gas, điện
- Tin tức, sự kiện, kết quả mới nhất (hôm nay, tuần này, mới nhất...)
- Thời tiết, dịch bệnh, thông tin cập nhật liên tục

KHÔNG cần tìm kiếm khi:
- Câu hỏi lý thuyết, giải thích khái niệm, lịch sử
- Lập trình, toán học, viết lách, sáng tạo
- Câu hỏi về hệ thống, cài đặt

Chỉ trả về JSON (không giải thích thêm):
{"search": true, "query": "câu truy vấn tối ưu tiếng Việt cho search engine"}
hoặc
{"search": false, "query": ""}"""


async def _ai_search_decision(
    content: str,
    base_url: str,
    model: str,
    timeout: float = 6.0,
) -> dict | None:
    """
    Gọi LLM nhanh (non-streaming) để quyết định có cần search không và query nào.
    Trả về {"search": bool, "query": str} hoặc None nếu thất bại/timeout.
    """
    import aiohttp

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _DECISION_SYSTEM},
            {"role": "user",   "content": content},
        ],
        "stream": False,
        "options": {"num_predict": 100, "temperature": 0},
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                raw = data.get("message", {}).get("content", "").strip()
                # Strip markdown code fences if any
                raw = raw.strip("```json").strip("```").strip()
                parsed = json.loads(raw)
                return {
                    "search": bool(parsed.get("search", False)),
                    "query":  str(parsed.get("query", content)).strip() or content,
                }
    except Exception as e:
        logger.warning("AI search decision failed (%s) — falling back to keyword classifier", e)
        return None


def _log_usage(user_id: str, provider, input_text: str, output_text: str) -> None:
    def _est(t: str) -> int:
        return max(1, len(t) // 4)

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": "chat_v2",
        "user_id": user_id,
        "provider": provider.name,
        "model": provider.model,
        "provider_type": provider.provider_type.value,
        "input_tokens_est": _est(input_text),
        "output_tokens_est": _est(output_text),
        "total_tokens_est": _est(input_text) + _est(output_text),
    }
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_USAGE_EVENTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("Usage log error: %s", e)


async def _set_title_bg(conv_id: str, first_message: str):
    title = await generate_conversation_title(first_message)
    if title:
        update_conversation_title(conv_id, title)


# ── Memory ─────────────────────────────────────────────────────────────────────

class MemoryUpdateRequest(BaseModel):
    facts: dict


@router.get("/chat-api/memory")
async def get_memory(user=Depends(_require_user)):
    facts = get_user_memory(str(user["id"]))
    return {"facts": facts}


@router.put("/chat-api/memory")
async def update_memory(body: MemoryUpdateRequest, user=Depends(_require_user)):
    set_user_memory(str(user["id"]), body.facts)
    return {"ok": True}


@router.delete("/chat-api/memory")
async def clear_memory(user=Depends(_require_user)):
    delete_user_memory(str(user["id"]))
    return {"ok": True}


# ── Projects ───────────────────────────────────────────────────────────────────

class ProjectRequest(BaseModel):
    name: str
    context: str = ""


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    context: str | None = None


@router.get("/chat-api/projects")
async def get_projects(user=Depends(_require_user)):
    projects = list_projects(str(user["id"]))
    return {"projects": projects}


@router.post("/chat-api/projects")
async def create_new_project(body: ProjectRequest, user=Depends(_require_user)):
    pid = create_project(str(user["id"]), body.name, body.context)
    return {"id": pid}


@router.put("/chat-api/projects/{project_id}")
async def update_existing_project(
    project_id: str, body: ProjectUpdateRequest, user=Depends(_require_user)
):
    update_project(project_id, str(user["id"]), body.name, body.context)
    return {"ok": True}


@router.delete("/chat-api/projects/{project_id}")
async def remove_project(project_id: str, user=Depends(_require_user)):
    delete_project(project_id, str(user["id"]))
    return {"ok": True}


# ── Guest info ─────────────────────────────────────────────────────────────────

@router.get("/chat-api/guest/status")
async def guest_status(request: Request):
    guest_id = request.headers.get("x-guest-session")
    if not guest_id:
        return {"remaining": GUEST_MESSAGE_LIMIT, "limit": GUEST_MESSAGE_LIMIT}
    gs = get_or_create_guest_session(guest_id, request.client.host if request.client else "unknown")
    remaining = max(0, GUEST_MESSAGE_LIMIT - gs["message_count"])
    return {"remaining": remaining, "limit": GUEST_MESSAGE_LIMIT}


# ── Feedback ───────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    message_id: str
    thumbs_up: bool


@router.post("/chat-api/feedback")
async def submit_feedback(body: FeedbackRequest, user=Depends(_get_portal_user)):
    update_feedback_vote(body.message_id, body.thumbs_up)
    return {"ok": True}


@router.post("/chat-api/feedback/export")
async def export_feedback(user=Depends(_require_user), date: str | None = None):
    try:
        path = export_feedback_jsonl(date)
        return {"ok": True, "path": path}
    except Exception as e:
        raise HTTPException(500, f"Export failed: {e}")
