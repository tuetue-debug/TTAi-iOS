jQuery(document).ready(function($) {
    const chatCard = $('.ttai-chat-card');
    const messagesContainer = $('#ttai-messages');
    const userInput = $('#ttai-user-input');
    const sendButton = $('#ttai-send-button');
    const sessionCountEl = $('#ttai-session-count');
    const statusText = $('.status-text');
    const ajaxEndpoint = resolveAjaxUrl();
    const ICONS = {
        user: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.6"/><path d="M5 20c0-3.314 3.134-6 7-6s7 2.686 7 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
        ai: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3l2.472 4.968L20 9.27l-4 3.858.944 5.5L12 16.9 7.056 18.628 8 12.87 4 9.27l5.528-1.302z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
    };
    if (window.console) {
        console.debug('TTAi ajax endpoint', ajaxEndpoint);
    }

    let userId = localStorage.getItem('ttai_user_id');
    if (!userId) {
        userId = 'free_user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('ttai_user_id', userId);
    }

    bindEvents();
    initTheme();
    updateConversationCount();
    welcomeTips();

    function bindEvents() {
        userInput.on('input', autoResize);
        userInput.on('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        sendButton.on('click', sendMessage);
    }

    function autoResize() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    }

    function initTheme() {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        applyTheme(prefersDark.matches ? 'dark' : 'light');
        prefersDark.addEventListener('change', e => applyTheme(e.matches ? 'dark' : 'light'));
    }

    function applyTheme(mode) {
        chatCard.attr('data-theme', mode);
    }

    function sendMessage() {
        const message = userInput.val().trim();
        if (!message) { return; }
        userInput.prop('disabled', true);
        sendButton.prop('disabled', true);
        addMessage(message, 'user');
        userInput.val('');
        autoResize.call(userInput[0]);
        const loadingId = 'loading-' + Date.now();
        addLoadingIndicator(loadingId);
        scrollToBottom();
        $.ajax({
            url: ajaxEndpoint,
            type: 'POST',
            data: {
                action: 'ttai_chat',
                nonce: ttai_ajax.nonce,
                message: message,
                user_id: userId
            },
            dataType: 'json',
            timeout: 90000,
            success: function(response) {
                $('#' + loadingId).remove();
                if (response.success) {
                    addMessage(response.data.response, 'ai', response.data);
                    updateStatus(`Phản hồi ${response.data.processing_time.toFixed(2)}s · ${response.data.model_used}`);
                    logInteraction(message, response.data);
                } else {
                    addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.', 'ai');
                    updateStatus('Lỗi kết nối');
                }
            },
            error: function(xhr, status) {
                $('#' + loadingId).remove();
                if (status === 'timeout') {
                    addMessage('Yêu cầu đang xử lý hơi lâu. Hệ thống đang tối ưu hoá router!', 'ai');
                    updateStatus('Đang xử lý...');
                    return;
                }
                let fallbackMessage = null;
                try {
                    if (xhr.responseText) {
                        const parsed = JSON.parse(xhr.responseText);
                        if (parsed?.data?.response) {
                            fallbackMessage = parsed.data.response;
                        } else if (typeof parsed?.data === 'string') {
                            fallbackMessage = parsed.data;
                        } else if (parsed?.message) {
                            fallbackMessage = parsed.message;
                        }
                    }
                } catch (parseErr) {
                    console.warn('Không parse được response JSON:', parseErr);
                }
                if (fallbackMessage) {
                    addMessage(fallbackMessage, 'ai');
                } else {
                    addMessage('Không thể kết nối đến TTAi ngay lúc này. Thử lại sau nhé.', 'ai');
                }
                updateStatus('Lỗi kết nối');
                if (window.console) {
                    console.error('TTAi chat AJAX error', status, xhr.status, xhr.responseText);
                }
            },
            complete: function() {
                userInput.prop('disabled', false);
                sendButton.prop('disabled', false);
                userInput.focus();
                scrollToBottom();
            }
        });
    }

    function addMessage(text, type, metadata = {}) {
        const timestamp = new Date().toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const actorLabel = type === 'ai' ? 'Tuệ Tuệ AI' : 'Bạn';
        const wrapper = $(`
            <div class="message ${type}-message">
                <div class="message-body">
                    <span class="message-icon">${type === 'ai' ? ICONS.ai : ICONS.user}</span>
                    <div class="message-content ttai-markdown"></div>
                </div>
                <div class="message-meta">
                    <span class="message-actor">${actorLabel}</span>
                    <span class="meta-dot">•</span>
                    <span class="message-time">${timestamp}</span>
                </div>
            </div>
        `);
        messagesContainer.append(wrapper);
        const contentBox = wrapper.find('.message-content');
        if (type === 'ai') {
            renderAIContent(contentBox, text);
        } else {
            const safeHtml = text.split(/\n/).map(line => `<span>${escapeHtml(line)}</span>`).join('<br>');
            contentBox.html(safeHtml);
        }
        if (metadata.processing_time) {
            wrapper.attr('data-processing', metadata.processing_time);
            wrapper.attr('data-model', metadata.model_used);
        }
        scrollToBottom();
    }

    function renderAIContent(target, rawText) {
        const segments = buildSegments(rawText);
        target.empty();
        const queue = [];
        segments.forEach(segmentText => {
            const paragraph = $('<p></p>').addClass('ttai-type-line');
            paragraph.data('full', segmentText);
            paragraph.text('');
            target.append(paragraph);
            queue.push(paragraph);
        });
        if (queue.length === 0) {
            target.text(rawText);
            return;
        }
        typeSequential(queue, 0);
    }

    function typeSequential(queue, index) {
        if (index >= queue.length) {
            scrollToBottom();
            return;
        }
        const element = queue[index];
        const text = element.data('full');
        let charIndex = 0;
        (function typeChar() {
            if (charIndex <= text.length) {
                element.text(text.slice(0, charIndex));
                scrollToBottom();
                charIndex++;
                setTimeout(typeChar, 18);
            } else {
                typeSequential(queue, index + 1);
            }
        })();
    }

    function buildSegments(text) {
        const lines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
        const segments = [];
        lines.forEach(line => {
            if (/^\d+\./.test(line)) {
                segments.push(line);
            } else if (/^[-*•]/.test(line)) {
                segments.push(`• ${line.replace(/^[-*•]\s*/, '')}`);
            } else {
                segments.push(line);
            }
        });
        return segments.length ? segments : [text];
    }

    function addLoadingIndicator(id) {
        const timestamp = new Date().toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const loadingHtml = `
            <div class="message ai-message" id="${id}">
                <div class="message-body">
                    <span class="message-icon">${ICONS.ai}</span>
                    <div class="message-content">
                        <span class="ttai-typing-indicator">
                            <span></span><span></span><span></span>
                        </span>
                    </div>
                </div>
                <div class="message-meta">
                    <span class="message-actor">Tuệ Tuệ AI</span>
                    <span class="meta-dot">•</span>
                    <span class="message-time">${timestamp}</span>
                </div>
            </div>
        `;
        messagesContainer.append(loadingHtml);
    }

    function updateStatus(text) {
        statusText.text(text);
        setTimeout(() => statusText.text('Đang trực tuyến'), 5000);
    }

    function logInteraction(question, response) {
        const entry = {
            timestamp: new Date().toISOString(),
            userId: userId,
            question: question,
            responseLength: response.response.length,
            processingTime: response.processing_time,
            modelUsed: response.model_used
        };
        let history = JSON.parse(localStorage.getItem('ttai_chat_history') || '[]');
        history.push(entry);
        if (history.length > 50) {
            history = history.slice(-50);
        }
        localStorage.setItem('ttai_chat_history', JSON.stringify(history));
        updateConversationCount(history.length);
    }

    function updateConversationCount(count) {
        const total = typeof count === 'number' ? count : JSON.parse(localStorage.getItem('ttai_chat_history') || '[]').length;
        sessionCountEl.text(total);
    }

    function scrollToBottom() {
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    function welcomeTips() {
        const history = JSON.parse(localStorage.getItem('ttai_chat_history') || '[]');
        if (history.length === 0) {
            setTimeout(() => {
                addMessage('💡 Mẹo: Bạn có thể hỏi tôi về kế hoạch chiến dịch, code, hay yêu cầu tài liệu nội bộ — tôi sẽ tự chọn mô hình phù hợp.', 'ai');
            }, 1500);
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function resolveAjaxUrl() {
        try {
            const parsed = new URL(ttai_ajax.ajax_url, window.location.origin);
            parsed.protocol = window.location.protocol;
            parsed.host = window.location.host;
            return parsed.toString();
        } catch (error) {
            console.warn('Không parse được ajax_url, fallback relative', error);
            return `${window.location.origin}/wp-admin/admin-ajax.php`;
        }
    }
});
