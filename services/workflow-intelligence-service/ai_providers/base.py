"""
AI Provider Base Interface
==========================

Defines the common interface for all AI providers in the workflow intelligence service.
Supports multiple providers (OpenAI, Anthropic, etc.) with unified API.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import time


class AITaskType(Enum):
    """Standard AI task types for workflow intelligence"""
    SUMMARIZE = "summarize"
    ANALYZE = "analyze" 
    SUGGEST = "suggest"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    TRANSLATE = "translate"
    GENERATE = "generate"


class AIProviderType(Enum):
    """Available AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class AIModelConfig:
    """Configuration for AI models"""
    provider: AIProviderType
    model_id: str
    display_name: str
    max_tokens: int
    supports_temperature: bool = True
    supports_system_messages: bool = True
    cost_per_1k_tokens_input: float = 0.0
    cost_per_1k_tokens_output: float = 0.0
    context_window: int = 4096
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class AIRequest:
    """Standardized AI request format"""
    task_type: AITaskType
    content: str
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_override: Optional[str] = None


@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    provider: AIProviderType
    model: str
    task_type: AITaskType
    usage: Dict[str, int]
    response_time: float
    cost_estimate: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: AIModelConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the AI client"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity"""
        pass
    
    @abstractmethod
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process an AI request and return standardized response"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[AIModelConfig]:
        """Get list of available models for this provider"""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: AIRequest, response: AIResponse = None) -> float:
        """Estimate cost for request/response"""
        pass
    
    def _build_system_prompt(self, task_type: AITaskType, custom_prompt: str = None) -> str:
        """Build system prompt based on task type"""
        base_prompts = {
            AITaskType.SUMMARIZE: "You are a professional document summarizer. Provide clear, concise summaries that capture key points and actionable items.",
            AITaskType.ANALYZE: "You are a business analyst. Analyze the provided content for insights, patterns, risks, and opportunities. Be thorough and objective.",
            AITaskType.SUGGEST: "You are a workflow optimization assistant. Provide intelligent suggestions to improve processes, forms, and business operations.",
            AITaskType.CLASSIFY: "You are a content classifier. Categorize and tag content accurately based on business rules and patterns.",
            AITaskType.EXTRACT: "You are a data extraction specialist. Extract specific information, entities, and structured data from unstructured content.",
            AITaskType.TRANSLATE: "You are a professional translator. Provide accurate translations while maintaining business context and terminology.",
            AITaskType.GENERATE: "You are a content generator. Create professional, relevant content that meets business requirements."
        }
        
        system_prompt = base_prompts.get(task_type, "You are an AI assistant for workflow intelligence.")
        
        if custom_prompt:
            system_prompt = f"{system_prompt}\n\nAdditional instructions: {custom_prompt}"
        
        return system_prompt
    
    async def _track_usage(self, request: AIRequest, response: AIResponse) -> None:
        """Track usage metrics for monitoring and billing"""
        # This would integrate with monitoring/analytics service
        # For now, just log the usage
        pass


class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass


class AIProviderUnavailableError(AIProviderError):
    """Raised when AI provider is unavailable"""
    pass


class AIProviderQuotaExceededError(AIProviderError):
    """Raised when API quota is exceeded"""
    pass


class AIProviderInvalidRequestError(AIProviderError):
    """Raised when request format is invalid"""
    pass