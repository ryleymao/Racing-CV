"""
Application settings using Pydantic Settings.
Industry standard: Type-safe configuration with validation.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # WebSocket Configuration
    ws_cv_endpoint: str = "/ws"
    ws_game_endpoint: str = "/ws/game"
    
    # CORS Configuration
    allowed_origins: str = "*"  # Comma-separated or "*" for all
    
    # Connection Limits
    max_game_clients: int = 10
    max_cv_clients: int = 1
    
    # CV Input Configuration
    cv_websocket_uri: str = ""  # Auto-generated if empty
    
    # Webcam Configuration
    webcam_index: int = 0
    
    # MediaPipe Configuration
    hand_detection_confidence: float = 0.7
    hand_tracking_confidence: float = 0.5
    max_num_hands: int = 1
    
    # Game Update Rate
    game_update_rate_hz: int = 60
    
    # File Paths
    project_root: Path = Path(__file__).parent.parent
    frontend_path: Path = project_root / "frontend" / "js" / "index.html"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="RACING_CV_",  # RACING_CV_SERVER_PORT, etc.
    )
    
    @property
    def game_update_interval(self) -> float:
        """Calculate update interval from rate."""
        return 1.0 / self.game_update_rate_hz
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins string to list."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def cv_websocket_uri_resolved(self) -> str:
        """Get CV WebSocket URI, auto-generate if not set."""
        if self.cv_websocket_uri:
            return self.cv_websocket_uri
        return f"ws://localhost:{self.server_port}{self.ws_cv_endpoint}"


# Global settings instance
settings = Settings()
