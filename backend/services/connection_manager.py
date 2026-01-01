"""
Connection Manager - Manages WebSocket connections with proper state handling.
Implements separation of concerns and thread-safe operations.
"""
import asyncio
from typing import Set
from fastapi import WebSocket
from datetime import datetime

from backend.models import ConnectionStats
from backend.utils.logger import logger


class ConnectionManager:
    """
    Manages WebSocket connections for the racing game.
    Provides thread-safe operations and proper separation of concerns.
    """
    
    def __init__(self, max_game_clients: int = 10, max_cv_clients: int = 1):
        """
        Initialize connection manager with limits.
        
        Args:
            max_game_clients: Maximum number of concurrent game clients
            max_cv_clients: Maximum number of concurrent CV input clients
        """
        self._game_clients: Set[WebSocket] = set()  # Use set for O(1) operations
        self._cv_clients: Set[WebSocket] = set()
        self._latest_steering: float = 0.0
        self._lock = asyncio.Lock()  # For thread-safe operations
        self._max_game_clients = max_game_clients
        self._max_cv_clients = max_cv_clients
    
    async def connect_cv_client(self, websocket: WebSocket) -> bool:
        """
        Connect a CV input client.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            True if connected, False if limit reached
        """
        async with self._lock:
            if len(self._cv_clients) >= self._max_cv_clients:
                return False
            self._cv_clients.add(websocket)
            return True
    
    async def disconnect_cv_client(self, websocket: WebSocket):
        """Disconnect a CV input client."""
        async with self._lock:
            self._cv_clients.discard(websocket)  # Safe even if not in set
    
    async def connect_game_client(self, websocket: WebSocket) -> bool:
        """
        Connect a game client.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            True if connected, False if limit reached
        """
        async with self._lock:
            if len(self._game_clients) >= self._max_game_clients:
                return False
            self._game_clients.add(websocket)
            return True
    
    async def disconnect_game_client(self, websocket: WebSocket):
        """Disconnect a game client."""
        async with self._lock:
            self._game_clients.discard(websocket)
    
    async def update_steering(self, steering: float) -> None:
        """
        Update steering value (headless - just store, no broadcast).
        
        Args:
            steering: Steering value in range [-1.0, 1.0]
        """
        # Validate and clamp
        steering = max(-1.0, min(1.0, float(steering)))
        
        async with self._lock:
            self._latest_steering = steering
    
    async def get_latest_steering(self) -> float:
        """Get the latest steering value."""
        async with self._lock:
            return self._latest_steering
    
    def get_stats(self) -> ConnectionStats:
        """Get connection statistics."""
        return ConnectionStats(
            game_clients=len(self._game_clients),
            cv_clients=len(self._cv_clients),
            max_game_clients=self._max_game_clients,
            max_cv_clients=self._max_cv_clients,
        )
