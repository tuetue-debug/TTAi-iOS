"""
Ollama Service Module for TTAi FastAPI
Handles async Ollama API calls with proper timeout and error handling
"""
import asyncio
import aiohttp
import logging
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaService:
    """Service for handling Ollama API calls with async support"""
    
    def __init__(self, base_url: str = "http://localhost:11434", max_workers: int = 2, timeout_seconds: int = 30):
        self.base_url = base_url.rstrip("/")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.request_timeout = timeout_seconds
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        
    async def generate(self, model: str, prompt: str, stream: bool = False, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate response from Ollama model
        
        Args:
            model: Ollama model name (e.g., "gemma3:4b")
            prompt: Input prompt
            stream: Whether to stream response
            
        Returns:
            Dict containing response data
        """
        target_base_url = (base_url or self.base_url).rstrip("/")
        url = f"{target_base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._sync_generate,
                url,
                payload
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama timeout for model {model}")
            raise HTTPException(status_code=504, detail="Ollama request timeout")
        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ollama service error: {str(e)}")
    
    def _sync_generate(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version for thread pool execution"""
        import requests
        import json
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.request_timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama request timeout")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama request failed: {str(e)}")
    
    async def chat(self, model: str, messages: list, stream: bool = False) -> Dict[str, Any]:
        """
        Chat completion using Ollama (if model supports chat format)
        
        Args:
            model: Ollama model name
            messages: List of message dicts with role/content
            stream: Whether to stream response
            
        Returns:
            Dict containing response data
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._sync_chat,
                url,
                payload
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama chat timeout for model {model}")
            raise HTTPException(status_code=504, detail="Ollama chat timeout")
        except Exception as e:
            logger.error(f"Ollama chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ollama chat error: {str(e)}")
    
    def _sync_chat(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous chat version for thread pool execution"""
        import requests
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.request_timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama chat timeout")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama chat failed: {str(e)}")
    
    async def embed(self, model: str, text: Optional[str] = None, input_data: Optional[Any] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Create embeddings using Ollama /api/embed."""
        target_base_url = (base_url or self.base_url).rstrip("/")
        url = f"{target_base_url}/api/embed"

        payload: Dict[str, Any] = {"model": model}
        if input_data is not None:
            payload["input"] = input_data
        elif text is not None:
            payload["input"] = text
        else:
            raise HTTPException(status_code=400, detail="Embedding input is required")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._sync_embed,
                url,
                payload
            )
            return response

        except asyncio.TimeoutError:
            logger.error(f"Ollama embed timeout for model {model}")
            raise HTTPException(status_code=504, detail="Ollama embed timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ollama embed error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ollama embed error: {str(e)}")

    def _sync_embed(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous embedding version for thread pool execution."""
        import requests

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.request_timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama embed timeout")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama embed failed: {str(e)}")

    async def list_models(self) -> list:
        """Get list of available Ollama models"""
        url = f"{self.base_url}/api/tags"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    else:
                        raise Exception(f"Failed to list models: {response.status}")
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=False)

# Global Ollama service instance configured from environment
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MAX_WORKERS = int(os.getenv("OLLAMA_MAX_WORKERS", os.getenv("MAX_WORKERS", "2")))
DEFAULT_OLLAMA_TIMEOUT = int(
    os.getenv(
        "OLLAMA_TIMEOUT",
        os.getenv("OLLAMA_REQUEST_TIMEOUT", os.getenv("TIMEOUT", "60"))
    )
)
ollama_service = OllamaService(
    base_url=DEFAULT_OLLAMA_BASE_URL,
    max_workers=DEFAULT_OLLAMA_MAX_WORKERS,
    timeout_seconds=DEFAULT_OLLAMA_TIMEOUT,
)
logger.info(
    "Initialized Ollama service with base_url=%s, max_workers=%s, timeout=%ss",
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MAX_WORKERS,
    DEFAULT_OLLAMA_TIMEOUT,
)