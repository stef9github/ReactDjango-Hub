# AI Architecture Documentation
## Workflow Intelligence Service Multi-Provider AI System

### 🎯 **Overview**

The Workflow Intelligence Service now features a comprehensive multi-provider AI architecture that provides enterprise-grade artificial intelligence capabilities with intelligent routing, automatic failover, and cost optimization. This system supports multiple AI providers including OpenAI (GPT-5, GPT-4.1, o1) and Anthropic (Claude Opus 4.1, Claude Sonnet 4) with seamless switching between providers based on task requirements, cost constraints, and performance needs.

### 🏗️ **Architecture Components**

#### **1. Base Interface Layer (`ai_providers/base.py`)**
- **Abstract Base Class**: Defines unified interface for all AI providers
- **Standard Data Models**: AIRequest, AIResponse, AIModelConfig for consistent API
- **Task Types**: Supports 7 task types (summarize, analyze, suggest, classify, extract, translate, generate)
- **Error Handling**: Comprehensive exception hierarchy for different failure modes
- **Cost Tracking**: Built-in cost estimation and usage tracking

#### **2. Provider Implementations**
- **OpenAI Provider** (`ai_providers/openai_provider.py`): 8 models including GPT-5, GPT-4.1, o1
- **Anthropic Provider** (`ai_providers/anthropic_provider.py`): 8 models including Claude Opus 4.1, Claude Sonnet 4
- **Model Configuration**: Complete model definitions with capabilities, costs, and limits
- **Health Monitoring**: Real-time provider health checks and status monitoring

#### **3. AI Provider Manager (`ai_providers/manager.py`)**
- **Intelligent Routing**: 5 selection strategies (performance, cost, speed, balanced, fallback)
- **Automatic Failover**: Seamless provider switching when primary fails
- **Cost Optimization**: Budget controls and cost-aware model selection
- **Load Balancing**: Distributes requests across healthy providers
- **Quality Ranking**: Model quality scoring system for intelligent selection

#### **4. Service Integration Layer (`ai_service.py`)**
- **Backward Compatibility**: Maintains existing workflow service API
- **Enhanced Features**: Advanced selection strategies and cost controls
- **Health Management**: Comprehensive health checks across all providers
- **Usage Analytics**: Detailed usage statistics and performance metrics

### 📊 **Supported AI Models**

#### **OpenAI Models**
| Model | Quality Rank | Input Cost | Output Cost | Context Window | Capabilities |
|-------|--------------|------------|-------------|----------------|--------------|
| GPT-5 | 1 (Best) | $0.03/1k | $0.06/1k | 1M tokens | reasoning, analysis, coding, creative |
| GPT-4.1 | 2 | $0.025/1k | $0.05/1k | 128k tokens | reasoning, analysis, coding |
| o1 | 2 | $0.015/1k | $0.06/1k | 128k tokens | reasoning, problem-solving |
| ChatGPT-4o-latest | 2 | $0.005/1k | $0.015/1k | 128k tokens | chat, analysis |
| GPT-4o | 3 | $0.0025/1k | $0.01/1k | 128k tokens | general purpose |
| GPT-5-mini | 3 | $0.015/1k | $0.03/1k | 1M tokens | analysis, summarization |
| o1-mini | 3 | $0.003/1k | $0.012/1k | 128k tokens | reasoning |
| GPT-4o-mini | 4 | $0.00015/1k | $0.0006/1k | 128k tokens | fast, cost-effective |

#### **Anthropic Models**
| Model | Quality Rank | Input Cost | Output Cost | Context Window | Capabilities |
|-------|--------------|------------|-------------|----------------|--------------|
| Claude Opus 4.1 | 1 (Best) | $0.075/1k | $0.375/1k | 200k tokens | reasoning, analysis, creative, coding, multimodal |
| Claude Opus 4 | 2 | $0.06/1k | $0.30/1k | 200k tokens | reasoning, analysis, creative, coding |
| Claude Sonnet 4 | 2 | $0.03/1k | $0.15/1k | 200k tokens | analysis, reasoning, coding |
| Claude 3.7 Sonnet | 3 | $0.03/1k | $0.15/1k | 200k tokens | analysis, reasoning |
| Claude 3.5 Sonnet | 3 | $0.03/1k | $0.15/1k | 200k tokens | analysis, reasoning |
| Claude 3.5 Haiku | 4 | $0.0025/1k | $0.0125/1k | 200k tokens | fast, cost-effective |
| Claude 3 Opus | 3 | $0.015/1k | $0.075/1k | 200k tokens | reasoning, creative |
| Claude 3 Haiku | 5 | $0.00025/1k | $0.00125/1k | 200k tokens | basic, fast |

### 🎯 **Model Selection Strategies**

#### **1. Performance Strategy**
- **Goal**: Best quality results regardless of cost
- **Selection**: Prioritizes GPT-5, Claude Opus 4.1, and other top-tier models
- **Use Cases**: Critical analysis, complex reasoning, high-stakes decisions
- **Scoring**: 70% quality + 30% capabilities

#### **2. Cost Strategy**  
- **Goal**: Minimize operational costs while meeting quality thresholds
- **Selection**: Prefers GPT-4o-mini, Claude 3 Haiku for basic tasks
- **Use Cases**: High-volume operations, budget-conscious deployments
- **Scoring**: 80% cost efficiency + 20% quality

#### **3. Speed Strategy**
- **Goal**: Fastest response times
- **Selection**: Optimizes for models known for speed (mini, haiku variants)
- **Use Cases**: Real-time applications, user-facing features
- **Scoring**: Speed bonus + 30% quality + 20% cost

#### **4. Balanced Strategy (Default)**
- **Goal**: Optimal balance of quality, cost, and performance
- **Selection**: Intelligently balances all factors
- **Use Cases**: General-purpose applications, most workflow tasks
- **Scoring**: 40% quality + 40% cost + 20% capabilities

#### **5. Fallback Strategy**
- **Goal**: Maximum reliability with provider redundancy
- **Selection**: Uses primary provider with automatic fallback
- **Use Cases**: Mission-critical systems, high availability requirements
- **Behavior**: Automatic provider switching on failures

### 🔧 **Configuration**

#### **Environment Variables**
```bash
# AI Service Configuration
AI_ENABLED=true
AI_STRATEGY=balanced  # performance, cost, speed, balanced, fallback

# OpenAI Configuration
AI_OPENAI_ENABLED=true
AI_OPENAI_PRIORITY=1
AI_OPENAI_DEFAULT_MODEL=gpt-5
AI_OPENAI_RATE_LIMIT_RPM=1000
AI_OPENAI_RATE_LIMIT_TPM=100000
AI_OPENAI_DAILY_BUDGET=100.0
OPENAI_API_KEY=your-openai-key

# Anthropic Configuration
AI_ANTHROPIC_ENABLED=true
AI_ANTHROPIC_PRIORITY=2
AI_ANTHROPIC_DEFAULT_MODEL=claude-opus-4-1-20250805
AI_ANTHROPIC_RATE_LIMIT_RPM=500
AI_ANTHROPIC_RATE_LIMIT_TPM=50000
AI_ANTHROPIC_DAILY_BUDGET=100.0
ANTHROPIC_API_KEY=your-anthropic-key
```

#### **Provider Priority System**
- **Priority 1** (Highest): OpenAI - First choice for most tasks
- **Priority 2**: Anthropic - Fallback and specialized reasoning tasks
- **Automatic Failover**: If Priority 1 fails, automatically use Priority 2
- **Health Monitoring**: Continuous provider health checks

### 🚀 **API Endpoints**

#### **Core AI Operations**
```python
# Document Summarization
POST /api/v1/ai/summarize
{
    "text": "Document content to summarize",
    "strategy": "balanced",  # Optional: performance, cost, speed, balanced
    "max_cost": 0.10        # Optional: Maximum cost per request
}

# Content Analysis
POST /api/v1/ai/analyze
{
    "content": "Content to analyze",
    "strategy": "performance",  # Use best models for analysis
    "context": {"domain": "business"}  # Optional context
}

# Smart Suggestions
POST /api/v1/ai/suggest
{
    "context_data": "Current workflow state",
    "strategy": "balanced"
}
```

#### **Management Endpoints**
```python
# Health Status
GET /api/v1/ai/health
# Returns: {"openai": "healthy", "anthropic": "healthy", "status": "healthy"}

# Model Recommendations
GET /api/v1/ai/models/recommend?task_type=summarize&strategy=cost
# Returns recommended model for specific task and strategy

# Available Models
GET /api/v1/ai/models
# Returns all available models from all providers with capabilities

# Usage Statistics
GET /api/v1/ai/usage
# Returns detailed usage stats, costs, and performance metrics
```

### 📈 **Usage Examples**

#### **Basic Usage**
```python
from ai_service import get_ai_service

# Initialize AI service
ai_service = await get_ai_service()

# Summarize document with balanced approach
result = await ai_service.summarize(
    text="Long document content...",
    strategy="balanced"
)

# Analyze content with best available model
analysis = await ai_service.analyze(
    content="Business proposal content...",
    strategy="performance"
)

# Get cost-optimized suggestions
suggestions = await ai_service.suggest(
    context_data="Current workflow state...",
    strategy="cost",
    max_cost=0.05  # Limit to 5 cents per request
)
```

#### **Advanced Configuration**
```python
from ai_providers.manager import AIProviderManager, ModelSelectionCriteria
from ai_providers.base import AIRequest, AITaskType

# Create custom selection criteria
criteria = ModelSelectionCriteria(
    task_type=AITaskType.ANALYZE,
    strategy=ModelSelectionStrategy.PERFORMANCE,
    max_cost=0.20,
    min_quality="excellent",
    prefer_provider=AIProviderType.ANTHROPIC
)

# Process with specific requirements
request = AIRequest(
    task_type=AITaskType.ANALYZE,
    content="Complex business analysis content...",
    system_prompt="Focus on risk assessment and strategic implications"
)

manager = AIProviderManager()
await manager.initialize()
response = await manager.process_request(request, criteria)
```

### 🔍 **Monitoring and Analytics**

#### **Health Monitoring**
- **Real-time Status**: Continuous health checks every 5 minutes
- **Provider Availability**: Track which providers are available
- **Response Times**: Monitor average response times per provider
- **Error Rates**: Track failure rates and error types
- **Cost Tracking**: Real-time cost monitoring with budget alerts

#### **Usage Analytics**
- **Request Volume**: Requests per provider and model
- **Token Usage**: Input/output token consumption
- **Cost Analysis**: Detailed cost breakdown by provider/model
- **Performance Metrics**: Response times and success rates
- **Quality Metrics**: Model selection effectiveness

#### **Alerting System**
- **Budget Alerts**: Notify when approaching daily/monthly limits
- **Provider Failures**: Alert when providers become unavailable
- **Performance Degradation**: Alert on increased response times
- **Error Thresholds**: Alert on elevated error rates

### 🧪 **Testing Architecture**

#### **Comprehensive Test Suite (`test_ai_architecture.py`)**
- **Provider Initialization**: Verify all providers initialize correctly
- **Health Checks**: Test provider connectivity and status
- **Model Availability**: Confirm all models are accessible
- **Task Processing**: Validate all task types work correctly
- **Provider Switching**: Test automatic failover functionality
- **Cost Optimization**: Verify cost-aware model selection
- **Performance Comparison**: Compare providers for different tasks
- **Error Handling**: Test graceful error handling and recovery

#### **Test Results Status**
✅ **Provider Initialization**: OpenAI and Anthropic providers initialize successfully  
✅ **Health Checks**: All providers report healthy status  
✅ **Model Availability**: 16 total models available (8 OpenAI + 8 Anthropic)  
✅ **Task Processing**: All task types process successfully  
✅ **Intelligent Selection**: Strategy-based model selection works correctly  
✅ **Actual AI Requests**: Real API calls to both providers successful  
✅ **Cost Optimization**: Budget-aware model selection functioning  
✅ **Error Handling**: Graceful fallback and error recovery working  

### 🔒 **Security and Compliance**

#### **API Security**
- **JWT Authentication**: All AI endpoints protected with JWT tokens
- **Rate Limiting**: Per-provider rate limiting with configurable limits
- **API Key Management**: Secure storage and rotation of provider API keys
- **Input Validation**: Comprehensive validation of all AI requests
- **Output Sanitization**: Sanitize AI responses before returning to clients

#### **Data Privacy**
- **No Data Retention**: AI providers configured with no training data retention
- **Content Filtering**: Filter sensitive data before sending to providers
- **Audit Logging**: Complete audit trail of all AI requests and responses
- **Compliance Ready**: GDPR, CCPA, and other regulatory compliance features

### 🚀 **Production Deployment**

#### **Container Configuration**
```yaml
# Docker environment
environment:
  - AI_ENABLED=true
  - AI_STRATEGY=balanced
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - AI_OPENAI_DAILY_BUDGET=500.0
  - AI_ANTHROPIC_DAILY_BUDGET=500.0
```

#### **Scaling Considerations**
- **Horizontal Scaling**: Multiple service instances with load balancing
- **Provider Load Balancing**: Distribute requests across providers
- **Caching Strategy**: Cache frequently requested AI responses
- **Queue Management**: Use Celery for background AI processing
- **Resource Management**: Monitor and optimize resource usage

#### **Operational Monitoring**
- **Metrics Collection**: Prometheus metrics for all AI operations
- **Dashboard**: Grafana dashboards for AI service monitoring
- **Alerting**: PagerDuty/Slack integration for critical alerts
- **Log Aggregation**: Centralized logging with ELK stack
- **Performance Tracking**: Track SLA compliance and performance trends

### 🔮 **Future Enhancements**

#### **Planned Features**
- **Additional Providers**: Google Gemini, Microsoft Azure OpenAI
- **Model Fine-tuning**: Custom model training for specific workflows
- **Batch Processing**: Optimized batch AI processing capabilities  
- **Caching Layer**: Intelligent response caching for performance
- **A/B Testing**: Model performance comparison and optimization
- **Cost Analytics**: Advanced cost prediction and optimization
- **Custom Models**: Integration with locally hosted models

#### **Integration Roadmap**
- **Workflow Integration**: Deep integration with workflow engine
- **Real-time Processing**: WebSocket-based real-time AI processing
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **Image Processing**: Computer vision for document analysis
- **Multi-modal**: Integrated text, image, and voice processing

---

**This AI architecture provides enterprise-grade artificial intelligence capabilities with intelligent routing, cost optimization, and automatic failover, making the Workflow Intelligence Service one of the most advanced AI-powered process automation platforms available.**