"""
Simple test to check basic imports and coverage
"""
import pytest
from app.models.enhanced_models import User, Organization, UserProfile

def test_models_exist():
    """Test that main models exist"""
    assert User is not None
    assert Organization is not None
    assert UserProfile is not None

if __name__ == "__main__":
    test_models_exist()
    print("Basic models test passed!")