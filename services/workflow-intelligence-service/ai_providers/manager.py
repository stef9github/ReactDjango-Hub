"""
AI Provider Manager
===================

Manages multiple AI providers and handles intelligent model selection, 
failover, cost optimization, and load balancing across providers.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, asdict

from .base import (
    AIProvider, AIRequest, AIResponse, AIModelConfig, AITaskType, 
    AIProviderType, AIProviderError, AIProviderUnavailableError
)
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class ModelSelectionStrategy(Enum):
    """Strategies for selecting AI models"""
    PERFORMANCE = "performance"  # Best model for the task
    COST = "cost"               # Cheapest model that can handle the task
    SPEED = "speed"             # Fastest model
    BALANCED = "balanced"       # Balance of cost, speed, and performance
    FALLBACK = "fallback"       # Use fallback providers if primary fails


@dataclass
class ProviderConfig:
    """Configuration for AI providers"""
    provider_type: AIProviderType
    api_key: str
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    default_model: Optional[str] = None
    rate_limit_rpm: int = 1000
    rate_limit_tpm: int = 100000
    cost_budget_daily: float = 100.0  # Daily budget in USD


@dataclass
class ModelSelectionCriteria:
    """Criteria for intelligent model selection"""
    task_type: AITaskType
    max_cost: Optional[float] = None
    max_latency: Optional[float] = None
    min_quality: Optional[str] = None  # "basic", "good", "excellent"
    prefer_provider: Optional[AIProviderType] = None
    strategy: ModelSelectionStrategy = ModelSelectionStrategy.BALANCED


class AIProviderManager:
    """Manages multiple AI providers with intelligent routing"""
    
    def __init__(self):
        self.providers: Dict[AIProviderType, AIProvider] = {}
        self.provider_configs: Dict[AIProviderType, ProviderConfig] = {}
        self.provider_health: Dict[AIProviderType, Dict[str, Any]] = {}
        self.usage_tracking: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        # Model quality rankings (1 = best, 5 = basic)
        self.model_quality_rankings = {
            # OpenAI models
            "gpt-5": 1,
            "gpt-4.1": 2,
            "o1": 2,
            "chatgpt-4o-latest": 2,
            "gpt-4o": 3,
            "gpt-5-mini": 3,
            "o1-mini": 3,
            "gpt-4o-mini": 4,
            
            # Anthropic models
            "claude-opus-4-1-20250805": 1,
            "claude-opus-4-20250514": 2,
            "claude-sonnet-4-20250514": 2,
            "claude-3-7-sonnet-20250219": 3,
            "claude-3-5-sonnet-20241022": 3,
            "claude-3-5-haiku-20241022": 4,
            "claude-3-haiku-20240307": 5,
            "claude-3-opus-20240229": 3,
        }
    
    async def initialize(self) -> None:
        """Initialize all configured AI providers"""
        # Load configuration from environment
        await self._load_configuration()
        
        # Initialize providers
        for provider_type, config in self.provider_configs.items():
            if config.enabled:
                try:
                    provider = await self._create_provider(provider_type, config)
                    await provider.initialize()
                    self.providers[provider_type] = provider
                    self.logger.info(f"Initialized {provider_type.value} provider")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {provider_type.value}: {str(e)}")
        
        # Perform initial health checks
        await self.check_all_provider_health()
    
    async def _load_configuration(self) -> None:
        """Load provider configuration from environment variables"""
        # OpenAI configuration
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.provider_configs[AIProviderType.OPENAI] = ProviderConfig(
                provider_type=AIProviderType.OPENAI,
                api_key=openai_key,
                enabled=os.getenv("AI_OPENAI_ENABLED", "true").lower() == "true",
                priority=int(os.getenv("AI_OPENAI_PRIORITY", "1")),
                default_model=os.getenv("AI_OPENAI_DEFAULT_MODEL", "gpt-5"),
                rate_limit_rpm=int(os.getenv("AI_OPENAI_RATE_LIMIT_RPM", "1000")),
                rate_limit_tpm=int(os.getenv("AI_OPENAI_RATE_LIMIT_TPM", "100000")),
                cost_budget_daily=float(os.getenv("AI_OPENAI_DAILY_BUDGET", "100.0"))
            )
        
        # Anthropic configuration
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.provider_configs[AIProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=AIProviderType.ANTHROPIC,
                api_key=anthropic_key,
                enabled=os.getenv("AI_ANTHROPIC_ENABLED", "true").lower() == "true",
                priority=int(os.getenv("AI_ANTHROPIC_PRIORITY", "2")),
                default_model=os.getenv("AI_ANTHROPIC_DEFAULT_MODEL", "claude-opus-4-1-20250805"),
                rate_limit_rpm=int(os.getenv("AI_ANTHROPIC_RATE_LIMIT_RPM", "500")),
                rate_limit_tpm=int(os.getenv("AI_ANTHROPIC_RATE_LIMIT_TPM", "50000")),
                cost_budget_daily=float(os.getenv("AI_ANTHROPIC_DAILY_BUDGET", "100.0"))
            )
    
    async def _create_provider(self, provider_type: AIProviderType, config: ProviderConfig) -> AIProvider:
        """Create provider instance based on type"""
        if provider_type == AIProviderType.OPENAI:
            return OpenAIProvider(config.api_key, config.default_model)
        elif provider_type == AIProviderType.ANTHROPIC:
            return AnthropicProvider(config.api_key, config.default_model)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    async def process_request(self, request: AIRequest, criteria: Optional[ModelSelectionCriteria] = None) -> AIResponse:
        """Process AI request with intelligent provider/model selection"""
        # Use default criteria if not provided
        if not criteria:
            criteria = ModelSelectionCriteria(task_type=request.task_type)
        
        # Select optimal provider and model
        selected_provider, selected_model = await self._select_provider_and_model(criteria, request)
        
        if not selected_provider:
            raise AIProviderUnavailableError("No healthy AI providers available")
        
        # Override model in request
        request.model_override = selected_model
        
        # Try primary provider
        try:
            response = await selected_provider.process_request(request)
            await self._track_usage(selected_provider.config.provider, response)
            return response
        except AIProviderError as e:
            self.logger.warning(f"Primary provider {selected_provider.config.provider.value} failed: {str(e)}")
            
            # Try fallback if available and strategy allows
            if criteria.strategy in [ModelSelectionStrategy.FALLBACK, ModelSelectionStrategy.BALANCED]:
                fallback_response = await self._try_fallback(request, selected_provider.config.provider)
                if fallback_response:
                    return fallback_response
            
            # Re-raise the original error if no fallback succeeded
            raise e
    
    async def _select_provider_and_model(self, criteria: ModelSelectionCriteria, request: AIRequest) -> Tuple[Optional[AIProvider], Optional[str]]:
        """Select optimal provider and model based on criteria"""
        candidates = []
        
        # Get all healthy providers
        for provider_type, provider in self.providers.items():
            if not self._is_provider_healthy(provider_type):
                continue
            
            # Skip if specific provider preferred and this isn't it
            if criteria.prefer_provider and criteria.prefer_provider != provider_type:
                continue
            
            # Get models for this task type
            if provider_type == AIProviderType.OPENAI:
                recommended_models = provider.get_model_recommendations(criteria.task_type)
            elif provider_type == AIProviderType.ANTHROPIC:
                recommended_models = provider.get_model_recommendations(criteria.task_type)
            else:
                recommended_models = [provider.config.model_id]
            
            # Evaluate each model
            for model in recommended_models:
                # Get model config
                if provider_type == AIProviderType.OPENAI:
                    model_config = provider.OPENAI_MODELS.get(model)
                elif provider_type == AIProviderType.ANTHROPIC:
                    model_config = provider.ANTHROPIC_MODELS.get(model)
                else:
                    model_config = provider.config
                
                if not model_config:
                    continue
                
                # Check quality requirements
                quality_rank = self.model_quality_rankings.get(model, 3)
                if criteria.min_quality:
                    quality_threshold = {"excellent": 2, "good": 3, "basic": 5}[criteria.min_quality]
                    if quality_rank > quality_threshold:
                        continue
                
                # Estimate cost
                estimated_cost = provider.estimate_cost(request)
                if criteria.max_cost and estimated_cost > criteria.max_cost:
                    continue
                
                # Calculate score based on strategy
                score = self._calculate_model_score(model_config, quality_rank, estimated_cost, criteria)
                
                candidates.append({
                    "provider": provider,
                    "model": model,
                    "config": model_config,
                    "score": score,
                    "cost": estimated_cost,
                    "quality_rank": quality_rank
                })
        
        # Sort by score (higher is better)
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        if candidates:
            best = candidates[0]
            return best["provider"], best["model"]
        
        return None, None
    
    def _calculate_model_score(self, model_config: AIModelConfig, quality_rank: int, cost: float, criteria: ModelSelectionCriteria) -> float:
        """Calculate score for model selection based on strategy"""
        # Base score components
        quality_score = max(0, 6 - quality_rank)  # Higher quality = higher score
        cost_score = max(0, 10 - (cost * 100))    # Lower cost = higher score
        capability_score = len(model_config.capabilities)
        
        # Weight based on strategy
        if criteria.strategy == ModelSelectionStrategy.PERFORMANCE:
            return quality_score * 0.7 + capability_score * 0.3
        elif criteria.strategy == ModelSelectionStrategy.COST:
            return cost_score * 0.8 + quality_score * 0.2
        elif criteria.strategy == ModelSelectionStrategy.SPEED:
            # Prefer models known for speed (haiku, mini, etc.)
            speed_bonus = 3 if any(x in model_config.model_id.lower() for x in ["haiku", "mini", "fast"]) else 0
            return speed_bonus + quality_score * 0.3 + cost_score * 0.2
        else:  # BALANCED or FALLBACK
            return (quality_score * 0.4 + cost_score * 0.4 + capability_score * 0.2)
    
    async def _try_fallback(self, request: AIRequest, failed_provider: AIProviderType) -> Optional[AIResponse]:
        """Try fallback providers when primary fails"""
        # Sort providers by priority, excluding the failed one
        available_providers = [
            (config.priority, provider_type, provider) 
            for provider_type, provider in self.providers.items() 
            if provider_type != failed_provider and self._is_provider_healthy(provider_type)
        ]
        available_providers.sort()  # Sort by priority (lower = higher priority)
        
        for _, provider_type, provider in available_providers:
            try:
                self.logger.info(f"Trying fallback provider: {provider_type.value}")
                
                # Use provider's default model for fallback
                request.model_override = self.provider_configs[provider_type].default_model
                
                response = await provider.process_request(request)
                await self._track_usage(provider_type, response)
                
                self.logger.info(f"Fallback to {provider_type.value} successful")
                return response
                
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type.value} also failed: {str(e)}")
                continue
        
        return None
    
    async def check_all_provider_health(self) -> Dict[AIProviderType, Dict[str, Any]]:
        """Check health of all providers"""
        health_results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                health = await provider.health_check()
                health_results[provider_type] = health
                self.provider_health[provider_type] = health
            except Exception as e:
                health = {
                    "status": "unhealthy",
                    "provider": provider_type.value,
                    "error": str(e),
                    "api_accessible": False
                }
                health_results[provider_type] = health
                self.provider_health[provider_type] = health
        
        return health_results
    
    def _is_provider_healthy(self, provider_type: AIProviderType) -> bool:
        """Check if a provider is healthy"""
        health = self.provider_health.get(provider_type, {})
        return health.get("status") in ["healthy", "degraded"]
    
    async def _track_usage(self, provider_type: AIProviderType, response: AIResponse) -> None:
        """Track usage for monitoring and billing"""
        if provider_type.value not in self.usage_tracking:
            self.usage_tracking[provider_type.value] = {
                "requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_response_time": 0.0
            }
        
        usage = self.usage_tracking[provider_type.value]
        usage["requests"] += 1
        usage["total_tokens"] += response.usage["total_tokens"]
        usage["total_cost"] += response.cost_estimate
        
        # Update average response time
        current_avg = usage["avg_response_time"]
        new_avg = (current_avg * (usage["requests"] - 1) + response.response_time) / usage["requests"]
        usage["avg_response_time"] = new_avg
    
    async def get_all_available_models(self) -> Dict[AIProviderType, List[AIModelConfig]]:
        """Get all available models from all providers"""
        models = {}
        for provider_type, provider in self.providers.items():
            try:
                models[provider_type] = await provider.get_available_models()
            except Exception as e:
                self.logger.error(f"Failed to get models from {provider_type.value}: {str(e)}")
                models[provider_type] = []
        
        return models
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics across all providers"""
        return {
            "providers": dict(self.usage_tracking),
            "total_requests": sum(stats["requests"] for stats in self.usage_tracking.values()),
            "total_cost": sum(stats["total_cost"] for stats in self.usage_tracking.values()),
            "provider_health": dict(self.provider_health)
        }
    
    async def recommend_model(self, task_type: AITaskType, criteria: Optional[ModelSelectionCriteria] = None) -> Dict[str, Any]:
        """Get model recommendation without making a request"""
        if not criteria:
            criteria = ModelSelectionCriteria(task_type=task_type)
        
        # Create dummy request for model selection
        dummy_request = AIRequest(
            task_type=task_type,
            content="dummy content for model selection"
        )
        
        provider, model = await self._select_provider_and_model(criteria, dummy_request)
        
        if provider and model:
            model_config = None
            if provider.config.provider == AIProviderType.OPENAI:
                model_config = provider.OPENAI_MODELS.get(model)
            elif provider.config.provider == AIProviderType.ANTHROPIC:
                model_config = provider.ANTHROPIC_MODELS.get(model)
            
            return {
                "recommended_provider": provider.config.provider.value,
                "recommended_model": model,
                "model_config": asdict(model_config) if model_config else None,
                "estimated_cost": provider.estimate_cost(dummy_request),
                "quality_rank": self.model_quality_rankings.get(model, 3)
            }
        
        return {
            "recommended_provider": None,
            "recommended_model": None,
            "error": "No suitable models found"
        }