"""
Load Balancer Module for TTAi Super Model Hybrid
Implements 60/30/10 routing strategy
"""

import random
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """AI Provider Types"""
    OLLAMA_LOCAL = "ollama_local"
    OLLAMA_REMOTE = "ollama_remote"
    CLI_PROXY = "cli_proxy"
    GPT_DIRECT = "gpt_direct"


class QueryComplexity(Enum):
    """Query Complexity Levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class ProviderConfig:
    """Configuration for AI Provider"""
    name: str
    provider_type: ProviderType
    endpoint: str
    model: str
    weight: float
    timeout: int
    enabled: bool = True


@dataclass
class QueryClassification:
    """Query Classification Result"""
    complexity: QueryComplexity
    confidence: float
    language: str
    needs_context: bool
    estimated_tokens: int


class LoadBalancer:
    """Intelligent Load Balancer for TTAi Hybrid System"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.health_status = {}
        self.request_count = {}
        self._initialize_metrics()
        
    def _initialize_providers(self) -> Dict[ProviderType, List[ProviderConfig]]:
        """Initialize all AI providers with 60/30/10 distribution"""
        
        providers = {
            ProviderType.OLLAMA_LOCAL: [
                ProviderConfig(
                    name="gemma3:4b-local",
                    provider_type=ProviderType.OLLAMA_LOCAL,
                    endpoint="http://localhost:11434/api/generate",
                    model="gemma3:4b",
                    weight=0.40,  # 40% of 60%
                    timeout=30
                ),
                ProviderConfig(
                    name="qwen3:4b-local",
                    provider_type=ProviderType.OLLAMA_LOCAL,
                    endpoint="http://localhost:11434/api/generate",
                    model="qwen3:4b",
                    weight=0.15,  # 15% of 60%
                    timeout=45
                ),
                ProviderConfig(
                    name="deepseek-r1:8b-local",
                    provider_type=ProviderType.OLLAMA_LOCAL,
                    endpoint="http://localhost:11434/api/generate",
                    model="deepseek-r1:8b",
                    weight=0.05,  # 5% of 60%
                    timeout=90
                )
            ],
            
            ProviderType.OLLAMA_REMOTE: [
                ProviderConfig(
                    name="deepseek-r1:8b-remote",
                    provider_type=ProviderType.OLLAMA_REMOTE,
                    endpoint="http://100.89.201.7:11434/api/generate",
                    model="deepseek-r1:8b",
                    weight=0.20,  # 20% of 60%
                    timeout=120
                )
            ],
            
            ProviderType.CLI_PROXY: [
                ProviderConfig(
                    name="cliproxy-deepseek",
                    provider_type=ProviderType.CLI_PROXY,
                    endpoint="cliproxy/gpt-mini",
                    model="cliproxy/gpt-mini",
                    weight=0.20,  # 20% of 30%
                    timeout=30
                ),
                ProviderConfig(
                    name="cliproxy-gpt",
                    provider_type=ProviderType.CLI_PROXY,
                    endpoint="cliproxy/gpt-mini",
                    model="cliproxy/gpt-mini",
                    weight=0.07,  # 7% of 30%
                    timeout=30
                ),
                ProviderConfig(
                    name="cliproxy-gemini",
                    provider_type=ProviderType.CLI_PROXY,
                    endpoint="cliproxy/gemini-pro",
                    model="cliproxy/gemini-pro",
                    weight=0.03,  # 3% of 30%
                    timeout=30
                )
            ],
            
            ProviderType.GPT_DIRECT: [
                ProviderConfig(
                    name="gpt-5.2-direct",
                    provider_type=ProviderType.GPT_DIRECT,
                    endpoint="openai/gpt-5.2",
                    model="gpt-5.2",
                    weight=0.10,  # 10% fallback
                    timeout=60
                )
            ]
        }
        
        logger.info(f"Initialized {sum(len(p) for p in providers.values())} providers")
        return providers
    
    def _initialize_metrics(self):
        """Initialize metrics tracking"""
        for provider_type, provider_list in self.providers.items():
            for provider in provider_list:
                self.request_count[provider.name] = 0
                self.health_status[provider.name] = True
    
    async def select_provider(self, classification: QueryClassification) -> ProviderConfig:
        """
        Select provider based on query classification and load balancing strategy
        
        Strategy:
        - SIMPLE: 70% local gemma, 30% remote gemma (within 60% Ollama pool)
        - MEDIUM: 50% CLI Proxy, 50% remote deepseek
        - COMPLEX: 60% remote deepseek, 40% GPT 5.2 fallback
        
        FALLBACK CHAIN (if selected provider not healthy):
        1. Other Ollama local models
        2. CLI Proxy models
        3. GPT direct (last resort)
        """
        
        if classification.complexity == QueryComplexity.SIMPLE:
            # Simple queries: prefer fast local models
            candidates = [
                p for p in self.providers[ProviderType.OLLAMA_LOCAL] 
                if p.model == "gemma3:4b" and p.enabled
            ]
            if not candidates:
                candidates = [p for p in self.providers[ProviderType.OLLAMA_LOCAL] if p.enabled]
            
            # Weighted random selection
            weights = [p.weight for p in candidates]
            selected = random.choices(candidates, weights=weights, k=1)[0]
            
        elif classification.complexity == QueryComplexity.MEDIUM:
            # Medium queries: mix of CLI Proxy and remote Ollama
            candidates = []
            weights = []
            
            # Add CLI Proxy providers (50%)
            cli_providers = [p for p in self.providers[ProviderType.CLI_PROXY] if p.enabled]
            candidates.extend(cli_providers)
            weights.extend([p.weight * 0.5 for p in cli_providers])  # Scale to 50%
            
            # Add remote Ollama providers (50%)
            remote_providers = [
                p for p in self.providers[ProviderType.OLLAMA_REMOTE] 
                if p.enabled and "deepseek" in p.model
            ]
            candidates.extend(remote_providers)
            weights.extend([p.weight * 0.5 for p in remote_providers])  # Scale to 50%
            
            if not candidates:
                # Fallback to any available provider
                all_providers = []
                for provider_list in self.providers.values():
                    all_providers.extend([p for p in provider_list if p.enabled])
                candidates = all_providers
                weights = [p.weight for p in candidates]
            
            selected = random.choices(candidates, weights=weights, k=1)[0]
            
        else:  # COMPLEX
            # Complex queries: remote deepseek or GPT fallback
            candidates = []
            weights = []
            
            # Remote deepseek (60%)
            remote_deepseek = [
                p for p in self.providers[ProviderType.OLLAMA_REMOTE]
                if p.enabled and "deepseek" in p.model
            ]
            candidates.extend(remote_deepseek)
            weights.extend([p.weight * 0.6 for p in remote_deepseek])
            
            # GPT direct fallback (40%)
            gpt_providers = [p for p in self.providers[ProviderType.GPT_DIRECT] if p.enabled]
            candidates.extend(gpt_providers)
            weights.extend([p.weight * 0.4 for p in gpt_providers])
            
            if not candidates:
                # Ultimate fallback
                all_providers = []
                for provider_list in self.providers.values():
                    all_providers.extend([p for p in provider_list if p.enabled])
                candidates = all_providers
                weights = [p.weight for p in candidates]
            
            selected = random.choices(candidates, weights=weights, k=1)[0]
        
        # Update metrics
        self.request_count[selected.name] += 1
        logger.info(f"Selected provider: {selected.name} for {classification.complexity.value} query")
        
        # Check health and implement fallback if needed
        if not await self.check_health(selected):
            logger.warning(f"Selected provider {selected.name} is not healthy, attempting fallback...")
            
            # Fallback chain: try other providers
            fallback_providers = []
            
            # 1. Try other providers of same type
            same_type_providers = [
                p for p in self.providers[selected.provider_type]
                if p.name != selected.name and p.enabled
            ]
            fallback_providers.extend(same_type_providers)
            
            # 2. Try CLI Proxy (for medium/complex queries)
            if classification.complexity in [QueryComplexity.MEDIUM, QueryComplexity.COMPLEX]:
                fallback_providers.extend([
                    p for p in self.providers[ProviderType.CLI_PROXY]
                    if p.enabled
                ])
            
            # 3. Try GPT direct (last resort)
            fallback_providers.extend([
                p for p in self.providers[ProviderType.GPT_DIRECT]
                if p.enabled
            ])
            
            # Find first healthy fallback
            for fallback in fallback_providers:
                if await self.check_health(fallback):
                    logger.info(f"Falling back to {fallback.name}")
                    self.request_count[fallback.name] = self.request_count.get(fallback.name, 0) + 1
                    return fallback
            
            # If no fallback available, return original (will likely fail)
            logger.error(f"No healthy fallback available for {selected.name}")
        
        return selected
    
    async def check_health(self, provider: ProviderConfig) -> bool:
        """Check if provider is healthy"""
        try:
            # Simple health check based on provider type
            if provider.provider_type in [ProviderType.OLLAMA_LOCAL, ProviderType.OLLAMA_REMOTE]:
                # Check Ollama API
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        provider.endpoint.replace("/api/generate", "/api/tags"),
                        timeout=5
                    ) as response:
                        return response.status == 200
            else:
                # For CLI Proxy and GPT, assume healthy
                return True
        except Exception as e:
            logger.warning(f"Health check failed for {provider.name}: {e}")
            return False
    
    def get_metrics(self) -> Dict:
        """Get load balancing metrics"""
        total_requests = sum(self.request_count.values())
        
        metrics = {
            "total_requests": total_requests,
            "provider_distribution": {},
            "health_status": self.health_status.copy()
        }
        
        # Calculate distribution by provider type
        for provider_type, provider_list in self.providers.items():
            type_requests = sum(
                self.request_count[p.name] 
                for p in provider_list 
                if p.name in self.request_count
            )
            metrics["provider_distribution"][provider_type.value] = {
                "requests": type_requests,
                "percentage": (type_requests / total_requests * 100) if total_requests > 0 else 0
            }
        
        return metrics
    
    def disable_provider(self, provider_name: str):
        """Disable a provider (e.g., due to repeated failures)"""
        for provider_list in self.providers.values():
            for provider in provider_list:
                if provider.name == provider_name:
                    provider.enabled = False
                    logger.warning(f"Disabled provider: {provider_name}")
                    return True
        return False
    
    def enable_provider(self, provider_name: str):
        """Enable a previously disabled provider"""
        for provider_list in self.providers.values():
            for provider in provider_list:
                if provider.name == provider_name:
                    provider.enabled = True
                    logger.info(f"Enabled provider: {provider_name}")
                    return True
        return False


# Singleton instance
load_balancer = LoadBalancer()