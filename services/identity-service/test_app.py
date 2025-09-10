"""
Minimal FastAPI app for testing without consul dependency
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test.db'

app = FastAPI(title="Auth Service Test", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}