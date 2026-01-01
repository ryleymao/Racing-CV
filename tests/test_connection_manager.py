"""
Integration tests for ConnectionManager.
Industry standard: Test async components properly.
"""
import pytest
from fastapi.testclient import TestClient
from backend.services.connection_manager import ConnectionManager
from backend.models import ConnectionStats


@pytest.mark.asyncio
class TestConnectionManager:
    """Tests for ConnectionManager."""
    
    async def test_connection_limits(self):
        """Test that connection limits are enforced."""
        manager = ConnectionManager(max_game_clients=2, max_cv_clients=1)
        
        # Mock WebSocket objects (simplified for testing)
        class MockWebSocket:
            pass
        
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()
        
        # Should allow first two
        assert await manager.connect_game_client(ws1) is True
        assert await manager.connect_game_client(ws2) is True
        
        # Third should be rejected
        assert await manager.connect_game_client(ws3) is False
        
        # Cleanup
        await manager.disconnect_game_client(ws1)
        await manager.disconnect_game_client(ws2)
    
    async def test_steering_update(self):
        """Test steering value updates."""
        manager = ConnectionManager()
        
        await manager.update_steering(0.5)
        steering = await manager.get_latest_steering()
        assert steering == 0.5
        
        # Test clamping
        await manager.update_steering(2.0)
        steering = await manager.get_latest_steering()
        assert steering == 1.0
    
    async def test_stats(self):
        """Test statistics retrieval."""
        manager = ConnectionManager(max_game_clients=10, max_cv_clients=1)
        
        stats = manager.get_stats()
        assert isinstance(stats, ConnectionStats)
        assert stats.max_game_clients == 10
        assert stats.max_cv_clients == 1
