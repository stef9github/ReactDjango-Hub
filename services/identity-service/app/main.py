"""
Auth Service - Organized FastAPI Application
Clean architecture with separated concerns
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import redis.asyncio as redis
import consul.aio as consul
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.core.config import settings
from app.core.database import init_db
from app.utils.messaging import EventPublisher
from app.api.v1 import auth, users, organizations, mfa

# Metrics
auth_requests = Counter('auth_requests_total', 'Total authentication requests')
auth_failures = Counter('auth_failures_total', 'Total authentication failures')
token_generation_time = Histogram('token_generation_seconds', 'Token generation time')


# Service Discovery
async def register_service():
    """Register service with Consul"""
    try:
        consul_client = consul.Consul(
            host=settings.CONSUL_HOST,
            port=settings.CONSUL_PORT
        )
        
        await consul_client.agent.service.register(
            name="auth-service",
            service_id="auth-service-1",
            address=settings.SERVICE_HOST,
            port=settings.SERVICE_PORT,
            tags=["authentication", "microservice"],
            check=consul.Check.http(
                f"http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/health",
                interval="30s"
            )
        )
        print("✅ Service registered with Consul")
    except Exception as e:
        print(f"❌ Failed to register with Consul: {e}")


async def deregister_service():
    """Deregister service from Consul"""
    try:
        consul_client = consul.Consul(
            host=settings.CONSUL_HOST,
            port=settings.CONSUL_PORT
        )
        await consul_client.agent.service.deregister("auth-service-1")
        print("✅ Service deregistered from Consul")
    except Exception as e:
        print(f"❌ Failed to deregister from Consul: {e}")


# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle service startup and shutdown"""
    # Startup
    print("🚀 Starting Auth Service...")
    await init_db()
    await register_service()
    
    # Initialize Redis
    app.state.redis = await redis.from_url(settings.REDIS_URL)
    print("✅ Redis connection established")
    
    # Initialize Event Publisher
    app.state.event_publisher = EventPublisher()
    print("✅ Event Publisher initialized")
    
    print("✅ Auth Service started successfully")
    yield
    
    # Shutdown
    print("🛑 Shutting down Auth Service...")
    await deregister_service()
    await app.state.redis.close()
    print("✅ Auth Service shutdown complete")


# FastAPI Application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Auth Service",
        description="Enhanced Authentication Microservice with Multi-Factor Authentication",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # OpenTelemetry Instrumentation
    FastAPIInstrumentor.instrument_app(app)

    # API Routes
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1") 
    app.include_router(mfa.router, prefix="/api/v1")

    # Health Check
    @app.get("/health")
    async def health_check():
        """Service health check with dependencies"""
        health_status = {
            "service": "auth-service",
            "status": "healthy",
            "version": "2.0.0",
            "database": "connected",
            "cache": "connected"
        }
        
        try:
            # Check Redis
            await app.state.redis.ping()
        except Exception:
            health_status["cache"] = "disconnected"
            health_status["status"] = "degraded"
        
        return health_status

    # Metrics Endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest()

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors"""
        print(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    return app


# Create app instance
app = create_app()


# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )