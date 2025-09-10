"""
Anthropic Provider Implementation
=================================

Supports latest Anthropic Claude models including Claude Opus 4.1, Claude Sonnet 4, and Claude 3.x series.
Handles Anthropic-specific parameters and message formatting.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import anthropic
from anthropic import AsyncAnthropic

from .base import (
    AIProvider, AIRequest, AIResponse, AIModelConfig, AITaskType, 
    AIProviderType, AIProviderError, AIProviderUnavailableError,
    AIProviderQuotaExceededError, AIProviderInvalidRequestError
)


class AnthropicProvider(AIProvider):
    """Anthropic provider with support for latest Claude models"""
    
    # Model configurations for Anthropic Claude models
    ANTHROPIC_MODELS = {
        "claude-opus-4-1-20250805": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-opus-4-1-20250805",
            display_name="Claude Opus 4.1 (Latest)",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.075,
            cost_per_1k_tokens_output=0.375,
            context_window=200000,
            capabilities=["reasoning", "analysis", "creative-writing", "coding", "multimodal"]
        ),
        "claude-opus-4-20250514": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-opus-4-20250514",
            display_name="Claude Opus 4",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.06,
            cost_per_1k_tokens_output=0.30,
            context_window=200000,
            capabilities=["reasoning", "analysis", "creative-writing", "coding"]
        ),
        "claude-sonnet-4-20250514": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-sonnet-4-20250514",
            display_name="Claude Sonnet 4",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.03,
            cost_per_1k_tokens_output=0.15,
            context_window=200000,
            capabilities=["analysis", "reasoning", "coding", "fast-response"]
        ),
        "claude-3-7-sonnet-20250219": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-3-7-sonnet-20250219",
            display_name="Claude Sonnet 3.7",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.025,
            cost_per_1k_tokens_output=0.125,
            context_window=200000,
            capabilities=["analysis", "coding", "writing"]
        ),
        "claude-3-5-sonnet-20241022": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-3-5-sonnet-20241022",
            display_name="Claude Sonnet 3.5 (New)",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.003,
            cost_per_1k_tokens_output=0.015,
            context_window=200000,
            capabilities=["analysis", "coding", "vision", "tool-use"]
        ),
        "claude-3-5-haiku-20241022": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-3-5-haiku-20241022",
            display_name="Claude Haiku 3.5",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.001,
            cost_per_1k_tokens_output=0.005,
            context_window=200000,
            capabilities=["fast-response", "summarization", "classification"]
        ),
        "claude-3-haiku-20240307": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-3-haiku-20240307",
            display_name="Claude Haiku 3",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.00025,
            cost_per_1k_tokens_output=0.00125,
            context_window=200000,
            capabilities=["fast-response", "summarization", "basic-analysis"]
        ),
        "claude-3-opus-20240229": AIModelConfig(
            provider=AIProviderType.ANTHROPIC,
            model_id="claude-3-opus-20240229",
            display_name="Claude Opus 3",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.015,
            cost_per_1k_tokens_output=0.075,
            context_window=200000,
            capabilities=["reasoning", "creative-writing", "complex-analysis"]
        )
    }
    
    def __init__(self, api_key: str, default_model: str = "claude-opus-4-1-20250805"):
        model_config = self.ANTHROPIC_MODELS.get(default_model, self.ANTHROPIC_MODELS["claude-opus-4-1-20250805"])
        super().__init__(model_config, api_key)
        self.default_model = default_model
        self._client = None
    
    async def initialize(self) -> None:
        """Initialize Anthropic client"""
        try:
            self._client = AsyncAnthropic(api_key=self.api_key)
            # Test connection
            await self.health_check()
        except Exception as e:
            raise AIProviderUnavailableError(f"Failed to initialize Anthropic provider: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health"""
        try:
            if not self._client:
                self._client = AsyncAnthropic(api_key=self.api_key)
            
            # Test with a simple request using fast/cheap model
            response = await self._client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return {
                "status": "healthy",
                "provider": "anthropic",
                "models_available": len(self.ANTHROPIC_MODELS),
                "default_model": self.default_model,
                "api_accessible": True
            }
        except anthropic.AuthenticationError:
            return {
                "status": "unhealthy",
                "provider": "anthropic",
                "error": "Invalid API key",
                "api_accessible": False
            }
        except anthropic.RateLimitError:
            return {
                "status": "degraded",
                "provider": "anthropic",
                "error": "Rate limit exceeded",
                "api_accessible": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "anthropic",
                "error": str(e),
                "api_accessible": False
            }
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process AI request using Anthropic Claude models"""
        start_time = time.time()
        
        # Determine which model to use
        model = request.model_override or self.default_model
        model_config = self.ANTHROPIC_MODELS.get(model, self.config)
        
        if not self._client:
            await self.initialize()
        
        try:
            # Build messages
            messages = []
            
            # Anthropic uses system parameter separately, not in messages
            system_prompt = None
            if model_config.supports_system_messages:
                system_prompt = request.system_prompt or self._build_system_prompt(request.task_type)
            
            # Add user message with context if provided
            user_content = request.content
            if request.context:
                context_str = "\n".join([f"{k}: {v}" for k, v in request.context.items()])
                user_content = f"Context:\n{context_str}\n\nTask: {user_content}"
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Build request parameters
            params = {
                "model": model,
                "max_tokens": request.max_tokens or model_config.max_tokens,
                "messages": messages,
            }
            
            # Add system prompt if supported
            if system_prompt:
                params["system"] = system_prompt
            
            # Add temperature if specified and supported
            if model_config.supports_temperature and request.temperature is not None:
                params["temperature"] = request.temperature
            
            # Make API call
            response = await self._client.messages.create(**params)
            
            response_time = time.time() - start_time
            
            # Extract response content
            content = ""
            if response.content:
                # Handle different content types
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif isinstance(block, dict) and 'text' in block:
                        content += block['text']
            
            # Calculate usage and cost
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            cost_estimate = self._calculate_cost(usage, model_config)
            
            return AIResponse(
                content=content,
                provider=AIProviderType.ANTHROPIC,
                model=response.model,
                task_type=request.task_type,
                usage=usage,
                response_time=response_time,
                cost_estimate=cost_estimate,
                metadata={
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence,
                    "model_config": model_config.__dict__
                }
            )
            
        except anthropic.AuthenticationError as e:
            raise AIProviderInvalidRequestError(f"Authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise AIProviderQuotaExceededError(f"Rate limit exceeded: {str(e)}")
        except anthropic.APIError as e:
            raise AIProviderError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            raise AIProviderError(f"Unexpected error: {str(e)}")
    
    async def get_available_models(self) -> List[AIModelConfig]:
        """Get list of available Anthropic models"""
        return list(self.ANTHROPIC_MODELS.values())
    
    def estimate_cost(self, request: AIRequest, response: AIResponse = None) -> float:
        """Estimate cost for Anthropic request/response"""
        model = request.model_override or self.default_model
        model_config = self.ANTHROPIC_MODELS.get(model, self.config)
        
        if response:
            return self._calculate_cost(response.usage, model_config)
        else:
            # Rough estimate based on input length
            estimated_input_tokens = len(request.content.split()) * 1.3  # Rough approximation
            estimated_output_tokens = 150  # Default estimate
            
            usage = {
                "prompt_tokens": int(estimated_input_tokens),
                "completion_tokens": estimated_output_tokens,
                "total_tokens": int(estimated_input_tokens) + estimated_output_tokens
            }
            
            return self._calculate_cost(usage, model_config)
    
    def _calculate_cost(self, usage: Dict[str, int], model_config: AIModelConfig) -> float:
        """Calculate actual cost based on usage"""
        input_cost = (usage["prompt_tokens"] / 1000) * model_config.cost_per_1k_tokens_input
        output_cost = (usage["completion_tokens"] / 1000) * model_config.cost_per_1k_tokens_output
        return input_cost + output_cost
    
    def get_model_recommendations(self, task_type: AITaskType) -> List[str]:
        """Get recommended models for specific task types"""
        recommendations = {
            AITaskType.SUMMARIZE: ["claude-3-5-haiku-20241022", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"],
            AITaskType.ANALYZE: ["claude-opus-4-1-20250805", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
            AITaskType.SUGGEST: ["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"],
            AITaskType.CLASSIFY: ["claude-3-5-haiku-20241022", "claude-3-haiku-20240307"],
            AITaskType.EXTRACT: ["claude-3-5-sonnet-20241022", "claude-sonnet-4-20250514"],
            AITaskType.TRANSLATE: ["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219"],
            AITaskType.GENERATE: ["claude-opus-4-1-20250805", "claude-opus-4-20250514"]
        }
        
        return recommendations.get(task_type, ["claude-opus-4-1-20250805", "claude-sonnet-4-20250514"])
    
    def get_latest_model(self) -> str:
        """Get the latest/best Anthropic model"""
        return "claude-opus-4-1-20250805"
    
    def get_fastest_model(self) -> str:
        """Get the fastest Anthropic model"""
        return "claude-3-5-haiku-20241022"
    
    def get_cheapest_model(self) -> str:
        """Get the most cost-effective Anthropic model"""
        return "claude-3-haiku-20240307"