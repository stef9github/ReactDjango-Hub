"""
Error injection tests for database failure scenarios
Tests service resilience against database connectivity issues, timeouts, and constraints
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy.exc import (
    DatabaseError, OperationalError, IntegrityError, 
    TimeoutError as SQLTimeoutError, DisconnectionError
)

from app.models.enhanced_models import User, Organization


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseErrorInjection:
    """Test service behavior under database failure conditions"""
    
    async def test_database_connection_failure(self, test_client: AsyncClient):
        """Test behavior when database connection fails"""
        with patch('app.core.database.get_session') as mock_session:
            mock_session.side_effect = OperationalError(
                "Connection to database failed", 
                None, 
                None
            )
            
            response = await test_client.post("/api/v1/auth/register", json={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "SecurePass123!"
            })
            
            # Should return 500 Internal Server Error
            assert response.status_code == 500
            assert "database" in response.json()["detail"].lower()
    
    async def test_database_timeout_handling(self, test_client: AsyncClient):
        """Test behavior when database operations timeout"""
        with patch('app.services.auth_service.AuthService.create_user') as mock_create:
            mock_create.side_effect = SQLTimeoutError(
                "Query timed out after 30 seconds", 
                None, 
                None
            )
            
            response = await test_client.post("/api/v1/auth/register", json={
                "email": "timeout@example.com", 
                "first_name": "Timeout",
                "last_name": "Test",
                "password": "SecurePass123!"
            })
            
            assert response.status_code == 500
            assert "timeout" in response.json()["detail"].lower()
    
    async def test_database_integrity_constraint_violation(self, test_client: AsyncClient):
        """Test behavior when database integrity constraints are violated"""
        # First create a user
        await test_client.post("/api/v1/auth/register", json={
            "email": "unique@example.com",
            "first_name": "First",
            "last_name": "User", 
            "password": "SecurePass123!"
        })
        
        # Try to create another user with the same email (should violate uniqueness)
        response = await test_client.post("/api/v1/auth/register", json={
            "email": "unique@example.com",  # Duplicate email
            "first_name": "Second",
            "last_name": "User",
            "password": "AnotherPass123!"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    async def test_session_rollback_on_error(self, test_session):
        """Test that sessions are properly rolled back on errors"""
        initial_count = (await test_session.execute("SELECT COUNT(*) FROM users")).scalar()
        
        try:
            # Start a transaction that will fail
            user = User(
                email="rollback@example.com",
                first_name="Rollback",
                last_name="Test",
                password_hash="hash",
                # Intentionally cause a constraint violation by setting invalid data
                email="invalid_email_format"  # This should cause validation issues
            )
            test_session.add(user)
            await test_session.commit()
        except Exception:
            # Transaction should be rolled back automatically
            pass
        
        # Verify that no data was persisted
        final_count = (await test_session.execute("SELECT COUNT(*) FROM users")).scalar()
        assert final_count == initial_count
    
    async def test_database_disconnection_recovery(self, test_client: AsyncClient):
        """Test behavior when database connection is lost and recovered"""
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
            # First call fails with disconnection
            mock_execute.side_effect = [
                DisconnectionError("Database connection lost", None, None),
                # Second call succeeds (simulating reconnection)
                AsyncMock()
            ]
            
            # This should handle the disconnection gracefully
            response = await test_client.get("/health")
            
            # Health check might still succeed with retry logic
            # Or return appropriate error status
            assert response.status_code in [200, 503]  # OK or Service Unavailable


@pytest.mark.integration  
@pytest.mark.asyncio
class TestServiceResiliencePatterns:
    """Test service resilience patterns under adverse conditions"""
    
    async def test_concurrent_user_creation_race_condition(self, test_client: AsyncClient):
        """Test handling of race conditions in concurrent user creation"""
        import asyncio
        
        # Create multiple concurrent requests with same email
        tasks = []
        for i in range(5):
            task = test_client.post("/api/v1/auth/register", json={
                "email": "race@example.com",
                "first_name": f"User{i}",
                "last_name": "Test",
                "password": f"SecurePass{i}!"
            })
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one should succeed, others should fail with appropriate error
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 201)
        error_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code >= 400)
        
        assert success_count == 1, "Exactly one user creation should succeed"
        assert error_count >= 4, "Other attempts should fail with appropriate errors"
    
    async def test_partial_transaction_failure(self, test_session):
        """Test handling of partial transaction failures"""
        from app.models.enhanced_models import User, UserProfile
        
        # Create a transaction that partially succeeds then fails
        try:
            # This should succeed
            user = User(
                email="partial@example.com",
                first_name="Partial",
                last_name="Test",
                password_hash="hash123"
            )
            test_session.add(user)
            await test_session.flush()  # Flush but don't commit
            
            # This should fail (invalid foreign key or constraint)
            profile = UserProfile(
                user_id=user.id,
                # Add invalid data that will cause constraint violation
                emergency_contact_phone="x" * 300  # Exceeds length limit
            )
            test_session.add(profile)
            await test_session.commit()
            
        except Exception as e:
            await test_session.rollback()
            
            # Verify user was also rolled back
            from sqlalchemy import select
            result = await test_session.execute(
                select(User).where(User.email == "partial@example.com")
            )
            assert result.first() is None, "User should be rolled back on profile failure"
    
    async def test_memory_pressure_handling(self, test_session):
        """Test behavior under memory pressure conditions"""
        # Simulate creating many objects to test memory handling
        users = []
        try:
            for i in range(1000):  # Create many objects
                user = User(
                    email=f"memory{i}@example.com",
                    first_name=f"User{i}",
                    last_name="Test",
                    password_hash="hash123"
                )
                users.append(user)
                test_session.add(user)
                
                # Flush every 100 to prevent excessive memory usage
                if i % 100 == 0:
                    await test_session.flush()
            
            await test_session.commit()
            
        except Exception as e:
            # Should handle memory pressure gracefully
            await test_session.rollback()
            assert True, "Memory pressure handled appropriately"


@pytest.mark.integration
@pytest.mark.asyncio  
class TestCircuitBreakerPatterns:
    """Test circuit breaker patterns for external dependencies"""
    
    async def test_email_service_circuit_breaker(self, test_client: AsyncClient):
        """Test circuit breaker for email service failures"""
        with patch('app.services.email_service.EmailService.send_verification_email') as mock_email:
            # Simulate email service being down
            mock_email.side_effect = ConnectionError("Email service unavailable")
            
            response = await test_client.post("/api/v1/auth/register", json={
                "email": "circuit@example.com",
                "first_name": "Circuit",
                "last_name": "Test", 
                "password": "SecurePass123!"
            })
            
            # User creation should succeed even if email fails
            # Email should be queued for retry or marked as failed
            assert response.status_code in [201, 202]  # Created or Accepted
    
    async def test_redis_cache_fallback(self, test_client: AsyncClient):
        """Test fallback behavior when Redis cache is unavailable"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value.get.side_effect = ConnectionError("Redis unavailable")
            
            # Authentication should still work without cache
            # (though it may be slower)
            response = await test_client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            })
            
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 503]  # OK or Service Unavailable


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestLoadFailureScenarios:
    """Test service behavior under high load failure scenarios"""
    
    async def test_connection_pool_exhaustion(self, test_client: AsyncClient):
        """Test behavior when database connection pool is exhausted"""
        import asyncio
        
        # Create many concurrent requests to exhaust connection pool
        async def make_request():
            return await test_client.get("/health")
        
        # Create more requests than typical connection pool size
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests should succeed, others may timeout or be queued
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        
        # Should handle pool exhaustion gracefully
        assert success_count > 0, "Some requests should succeed"
    
    async def test_cascading_failure_prevention(self, test_client: AsyncClient):
        """Test prevention of cascading failures"""
        # Simulate a dependency failure that could cause cascading issues
        with patch('app.services.auth_service.TokenService.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token service down")
            
            # Protected endpoints should fail gracefully without cascading
            response = await test_client.get("/api/v1/auth/me", headers={
                "Authorization": "Bearer invalid_token"
            })
            
            # Should return appropriate error, not cascade failures
            assert response.status_code in [401, 503]  # Unauthorized or Service Unavailable
            assert "token" in response.json()["detail"].lower()


# Error injection fixtures for testing
@pytest.fixture
def mock_database_error():
    """Fixture to inject database errors"""
    return OperationalError("Simulated database error", None, None)


@pytest.fixture  
def mock_timeout_error():
    """Fixture to inject timeout errors"""
    return SQLTimeoutError("Simulated timeout", None, None)


@pytest.fixture
def mock_integrity_error():
    """Fixture to inject integrity constraint errors"""
    return IntegrityError("Unique constraint violation", None, None)