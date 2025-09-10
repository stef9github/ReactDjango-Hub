"""
OpenAI Provider Implementation
==============================

Supports multiple OpenAI models including GPT-5, GPT-4.1, GPT-4o, and earlier versions.
Handles model-specific parameters and capabilities.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import openai
from openai import AsyncOpenAI

from .base import (
    AIProvider, AIRequest, AIResponse, AIModelConfig, AITaskType, 
    AIProviderType, AIProviderError, AIProviderUnavailableError,
    AIProviderQuotaExceededError, AIProviderInvalidRequestError
)


class OpenAIProvider(AIProvider):
    """OpenAI provider with support for latest models"""
    
    # Model configurations for OpenAI models
    OPENAI_MODELS = {
        "gpt-5": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="gpt-5",
            display_name="GPT-5 (Latest)",
            max_tokens=4000,
            supports_temperature=False,  # GPT-5 only supports default temperature
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.03,
            cost_per_1k_tokens_output=0.06,
            context_window=1000000,  # 1M tokens
            capabilities=["chat", "reasoning", "analysis", "coding", "creative"]
        ),
        "gpt-5-mini": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="gpt-5-mini",
            display_name="GPT-5 Mini",
            max_tokens=4000,
            supports_temperature=False,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.015,
            cost_per_1k_tokens_output=0.03,
            context_window=1000000,
            capabilities=["chat", "analysis", "summarization"]
        ),
        "gpt-4.1": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="gpt-4.1",
            display_name="GPT-4.1",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.03,
            cost_per_1k_tokens_output=0.06,
            context_window=1000000,
            capabilities=["chat", "reasoning", "analysis", "coding"]
        ),
        "gpt-4o": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="gpt-4o",
            display_name="GPT-4o (Omni)",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.0025,
            cost_per_1k_tokens_output=0.01,
            context_window=128000,
            capabilities=["chat", "vision", "audio", "multimodal"]
        ),
        "gpt-4o-mini": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.00015,
            cost_per_1k_tokens_output=0.0006,
            context_window=128000,
            capabilities=["chat", "vision", "fast-response"]
        ),
        "chatgpt-4o-latest": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="chatgpt-4o-latest",
            display_name="ChatGPT-4o (Latest)",
            max_tokens=4000,
            supports_temperature=True,
            supports_system_messages=True,
            cost_per_1k_tokens_input=0.005,
            cost_per_1k_tokens_output=0.015,
            context_window=128000,
            capabilities=["chat", "reasoning", "web-browsing"]
        ),
        "o1": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="o1",
            display_name="OpenAI o1",
            max_tokens=4000,
            supports_temperature=False,  # o1 models don't support temperature
            supports_system_messages=False,  # o1 models don't support system messages
            cost_per_1k_tokens_input=0.015,
            cost_per_1k_tokens_output=0.06,
            context_window=200000,
            capabilities=["reasoning", "complex-problem-solving", "mathematics"]
        ),
        "o1-mini": AIModelConfig(
            provider=AIProviderType.OPENAI,
            model_id="o1-mini",
            display_name="OpenAI o1-mini",
            max_tokens=4000,
            supports_temperature=False,
            supports_system_messages=False,
            cost_per_1k_tokens_input=0.003,
            cost_per_1k_tokens_output=0.012,
            context_window=128000,
            capabilities=["reasoning", "problem-solving", "coding"]
        )
    }
    
    def __init__(self, api_key: str, default_model: str = "gpt-5"):
        model_config = self.OPENAI_MODELS.get(default_model, self.OPENAI_MODELS["gpt-5"])
        super().__init__(model_config, api_key)
        self.default_model = default_model
        self._client = None
    
    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        try:
            self._client = AsyncOpenAI(api_key=self.api_key)
            # Test connection
            await self.health_check()
        except Exception as e:
            raise AIProviderUnavailableError(f"Failed to initialize OpenAI provider: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            if not self._client:
                self._client = AsyncOpenAI(api_key=self.api_key)
            
            # Test with a simple request
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for health check
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            return {
                "status": "healthy",
                "provider": "openai",
                "models_available": len(self.OPENAI_MODELS),
                "default_model": self.default_model,
                "api_accessible": True
            }
        except openai.AuthenticationError:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": "Invalid API key",
                "api_accessible": False
            }
        except openai.RateLimitError:
            return {
                "status": "degraded",
                "provider": "openai",
                "error": "Rate limit exceeded",
                "api_accessible": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": str(e),
                "api_accessible": False
            }
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process AI request using OpenAI models"""
        start_time = time.time()
        
        # Determine which model to use
        model = request.model_override or self.default_model
        model_config = self.OPENAI_MODELS.get(model, self.config)
        
        if not self._client:
            await self.initialize()
        
        try:
            # Build messages
            messages = []
            
            # Add system message if supported by the model
            if model_config.supports_system_messages and request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            elif model_config.supports_system_messages:
                messages.append({
                    "role": "system",
                    "content": self._build_system_prompt(request.task_type)
                })
            
            # Add user message
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
                "messages": messages,
            }
            
            # Add max tokens (use model-specific parameter name)
            if model.startswith("gpt-5") or model.startswith("o1"):
                params["max_completion_tokens"] = request.max_tokens or model_config.max_tokens
            else:
                params["max_tokens"] = request.max_tokens or model_config.max_tokens
            
            # Add temperature if supported
            if model_config.supports_temperature and request.temperature is not None:
                params["temperature"] = request.temperature
            
            # Make API call
            response = await self._client.chat.completions.create(**params)
            
            response_time = time.time() - start_time
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Calculate usage and cost
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            cost_estimate = self._calculate_cost(usage, model_config)
            
            return AIResponse(
                content=content,
                provider=AIProviderType.OPENAI,
                model=response.model,
                task_type=request.task_type,
                usage=usage,
                response_time=response_time,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model_config": model_config.__dict__
                }
            )
            
        except openai.AuthenticationError as e:
            raise AIProviderInvalidRequestError(f"Authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            raise AIProviderQuotaExceededError(f"Rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            raise AIProviderError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise AIProviderError(f"Unexpected error: {str(e)}")
    
    async def get_available_models(self) -> List[AIModelConfig]:
        """Get list of available OpenAI models"""
        return list(self.OPENAI_MODELS.values())
    
    def estimate_cost(self, request: AIRequest, response: AIResponse = None) -> float:
        """Estimate cost for OpenAI request/response"""
        model = request.model_override or self.default_model
        model_config = self.OPENAI_MODELS.get(model, self.config)
        
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
            AITaskType.SUMMARIZE: ["gpt-4o-mini", "gpt-5-mini", "gpt-4o"],
            AITaskType.ANALYZE: ["gpt-5", "gpt-4.1", "o1"],
            AITaskType.SUGGEST: ["gpt-5", "chatgpt-4o-latest", "gpt-4.1"],
            AITaskType.CLASSIFY: ["gpt-4o-mini", "gpt-5-mini"],
            AITaskType.EXTRACT: ["gpt-4o", "gpt-4.1"],
            AITaskType.TRANSLATE: ["gpt-4o", "gpt-4.1"],
            AITaskType.GENERATE: ["gpt-5", "chatgpt-4o-latest"]
        }
        
        return recommendations.get(task_type, ["gpt-5", "gpt-4o"])