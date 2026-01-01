"""
Unit tests for Pydantic models.
Industry standard: Comprehensive test coverage.
"""
import pytest
from datetime import datetime
from backend.models import (
    SteeringMessage,
    GameUpdateMessage,
    ConnectionStats,
    HealthResponse,
    ErrorResponse,
)


class TestSteeringMessage:
    """Tests for SteeringMessage model."""
    
    def test_valid_steering(self):
        """Test valid steering values."""
        msg = SteeringMessage(steering=0.5)
        assert msg.steering == 0.5
        assert -1.0 <= msg.steering <= 1.0
    
    def test_steering_clamping(self):
        """Test that steering values are clamped."""
        msg = SteeringMessage(steering=2.0)
        assert msg.steering == 1.0
        
        msg = SteeringMessage(steering=-2.0)
        assert msg.steering == -1.0
    
    def test_steering_validation(self):
        """Test steering validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            SteeringMessage(steering="invalid")


class TestConnectionStats:
    """Tests for ConnectionStats model."""
    
    def test_valid_stats(self):
        """Test valid connection stats."""
        stats = ConnectionStats(
            game_clients=5,
            cv_clients=1,
            max_game_clients=10,
            max_cv_clients=1
        )
        assert stats.game_clients == 5
        assert stats.cv_clients == 1


class TestHealthResponse:
    """Tests for HealthResponse model."""
    
    def test_health_response(self):
        """Test health response creation."""
        stats = ConnectionStats(
            game_clients=0,
            cv_clients=0,
            max_game_clients=10,
            max_cv_clients=1
        )
        health = HealthResponse(status="healthy", stats=stats)
        assert health.status == "healthy"
        assert isinstance(health.timestamp, datetime)
