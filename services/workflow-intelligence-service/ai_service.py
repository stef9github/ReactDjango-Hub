"""
AI Service Integration
======================

Integrates the new AI provider manager with the workflow service,
providing backward compatibility and enhanced AI capabilities.
"""

import os
from typing import Dict, Any, Optional
import logging
from enum import Enum

from ai_providers.manager import AIProviderManager, ModelSelectionStrategy, ModelSelectionCriteria
from ai_providers.base import AIRequest, AIResponse, AITaskType, AIProviderType


class AIService:
    """Main AI service that integrates with the workflow intelligence service"""
    
    def __init__(self):
        self.manager = AIProviderManager()
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI service and all providers"""
        if self._initialized:
            return
        
        try:
            await self.manager.initialize()
            self._initialized = True
            self.logger.info("AI service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI service: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Get health status of all AI providers"""
        if not self._initialized:
            return {
                "openai": "not-initialized",
                "anthropic": "not-initialized",
                "status": "not-initialized"
            }
        
        try:
            health_results = await self.manager.check_all_provider_health()
            
            # Format for backward compatibility with existing health endpoint
            formatted_health = {}
            for provider_type, health in health_results.items():
                formatted_health[provider_type.value] = health["status"]
            
            # Determine overall status
            statuses = [health["status"] for health in health_results.values()]
            if any(status == "healthy" for status in statuses):
                overall_status = "healthy"
            elif any(status == "degraded" for status in statuses):
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
            
            formatted_health["status"] = overall_status
            return formatted_health
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "openai": "error",
                "anthropic": "error",
                "status": "error",
                "error": str(e)
            }
    
    async def summarize(self, text: str, context: Optional[Dict[str, Any]] = None, 
                       strategy: str = "balanced", max_cost: Optional[float] = None) -> Dict[str, Any]:
        """AI-powered document summarization"""
        if not self._initialized:
            await self.initialize()
        
        # Convert strategy string to enum
        strategy_enum = self._get_strategy_enum(strategy)
        
        # Create request
        request = AIRequest(
            task_type=AITaskType.SUMMARIZE,
            content=text,
            context=context,
            system_prompt="Provide a clear, concise summary highlighting key points, decisions, and action items."
        )
        
        # Create selection criteria
        criteria = ModelSelectionCriteria(
            task_type=AITaskType.SUMMARIZE,
            strategy=strategy_enum,
            max_cost=max_cost,
            min_quality="good"
        )
        
        try:
            response = await self.manager.process_request(request, criteria)
            return self._format_response(response)
        except Exception as e:
            self.logger.error(f"Summarization failed: {str(e)}")
            raise
    
    async def analyze(self, content: str, context: Optional[Dict[str, Any]] = None,
                     strategy: str = "performance", max_cost: Optional[float] = None) -> Dict[str, Any]:
        """AI-powered content analysis"""
        if not self._initialized:
            await self.initialize()
        
        strategy_enum = self._get_strategy_enum(strategy)
        
        request = AIRequest(
            task_type=AITaskType.ANALYZE,
            content=content,
            context=context,
            system_prompt="Analyze the content for insights, patterns, risks, opportunities, and strategic implications."
        )
        
        criteria = ModelSelectionCriteria(
            task_type=AITaskType.ANALYZE,
            strategy=strategy_enum,
            max_cost=max_cost,
            min_quality="excellent"  # Use best models for analysis
        )
        
        try:
            response = await self.manager.process_request(request, criteria)
            return self._format_response(response)
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            raise
    
    async def suggest(self, context_data: str, context: Optional[Dict[str, Any]] = None,
                     strategy: str = "balanced", max_cost: Optional[float] = None) -> Dict[str, Any]:
        """AI-powered suggestions for workflow optimization"""
        if not self._initialized:
            await self.initialize()
        
        strategy_enum = self._get_strategy_enum(strategy)
        
        request = AIRequest(
            task_type=AITaskType.SUGGEST,
            content=context_data,
            context=context,
            system_prompt="Provide intelligent suggestions to optimize workflows, improve processes, and enhance efficiency."
        )
        
        criteria = ModelSelectionCriteria(
            task_type=AITaskType.SUGGEST,
            strategy=strategy_enum,
            max_cost=max_cost,
            min_quality="good"
        )
        
        try:
            response = await self.manager.process_request(request, criteria)
            return self._format_response(response)
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {str(e)}")
            raise
    
    async def get_model_recommendation(self, task_type: str, strategy: str = "balanced") -> Dict[str, Any]:
        """Get AI model recommendation for a specific task type"""
        if not self._initialized:
            await self.initialize()
        
        try:
            task_enum = AITaskType(task_type.lower())
            strategy_enum = self._get_strategy_enum(strategy)
            
            criteria = ModelSelectionCriteria(
                task_type=task_enum,
                strategy=strategy_enum
            )
            
            recommendation = await self.manager.recommend_model(task_enum, criteria)
            return recommendation
        except Exception as e:
            self.logger.error(f"Model recommendation failed: {str(e)}")
            return {"error": str(e)}
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get all available models from all providers"""
        if not self._initialized:
            await self.initialize()
        
        try:
            all_models = await self.manager.get_all_available_models()
            
            # Format for API response
            formatted_models = {}
            for provider_type, models in all_models.items():
                formatted_models[provider_type.value] = [
                    {
                        "id": model.model_id,
                        "name": model.display_name,
                        "max_tokens": model.max_tokens,
                        "context_window": model.context_window,
                        "capabilities": model.capabilities,
                        "cost_per_1k_input": model.cost_per_1k_tokens_input,
                        "cost_per_1k_output": model.cost_per_1k_tokens_output,
                        "supports_temperature": model.supports_temperature,
                        "supports_system_messages": model.supports_system_messages
                    }
                    for model in models
                ]
            
            return formatted_models
        except Exception as e:
            self.logger.error(f"Failed to get available models: {str(e)}")
            return {"error": str(e)}
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics across all providers"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.manager.get_usage_stats()
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {str(e)}")
            return {"error": str(e)}
    
    def _get_strategy_enum(self, strategy_str: str) -> ModelSelectionStrategy:
        """Convert strategy string to enum"""
        strategy_map = {
            "performance": ModelSelectionStrategy.PERFORMANCE,
            "cost": ModelSelectionStrategy.COST,
            "speed": ModelSelectionStrategy.SPEED,
            "balanced": ModelSelectionStrategy.BALANCED,
            "fallback": ModelSelectionStrategy.FALLBACK
        }
        return strategy_map.get(strategy_str.lower(), ModelSelectionStrategy.BALANCED)
    
    def _format_response(self, response: AIResponse) -> Dict[str, Any]:
        """Format AI response for API return"""
        return {
            "content": response.content,
            "provider": response.provider.value,
            "model": response.model,
            "task_type": response.task_type.value,
            "usage": response.usage,
            "response_time": response.response_time,
            "cost_estimate": response.cost_estimate,
            "metadata": response.metadata or {}
        }


# Global AI service instance
ai_service = AIService()


async def get_ai_service() -> AIService:
    """Dependency injection for AI service"""
    if not ai_service._initialized:
        await ai_service.initialize()
    return ai_service