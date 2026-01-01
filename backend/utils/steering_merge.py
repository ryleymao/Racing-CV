"""
Steering Merge Utility - Industry Standard
Simple Python function, no extra libraries.
Input: list of floats ([-1, 1])
Output: single float (-1 left → 1 right)
Optional smoothing: simple average or exponential smoothing
"""
from typing import List, Optional, Dict
from collections import deque
import time


def merge_steering(
    steering_values: List[float],
    weights: Optional[List[float]] = None,
    use_smoothing: bool = True,
    smoothing_alpha: float = 0.3
) -> float:
    """
    Merge multiple steering inputs into single value.
    Industry standard: Simple Python function.
    
    Args:
        steering_values: List of steering values in range [-1, 1]
        weights: Optional weights for each input (default: equal weights)
        use_smoothing: Whether to apply exponential smoothing
        smoothing_alpha: Smoothing factor (0-1), higher = more responsive
        
    Returns:
        Merged steering value in range [-1, 1]
    """
    if not steering_values:
        return 0.0
    
    # Clamp all values to [-1, 1]
    clamped = [max(-1.0, min(1.0, float(v))) for v in steering_values]
    
    # Calculate weights (equal if not provided)
    if weights is None:
        weights = [1.0 / len(clamped)] * len(clamped)
    else:
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(clamped)] * len(clamped)
    
    # Weighted average
    merged = sum(v * w for v, w in zip(clamped, weights))
    
    # Apply exponential smoothing if enabled
    if use_smoothing:
        if not hasattr(merge_steering, '_last_value'):
            merge_steering._last_value = merged
        else:
            # Exponential moving average
            merged = smoothing_alpha * merged + (1 - smoothing_alpha) * merge_steering._last_value
        merge_steering._last_value = merged
    
    # Clamp final result
    return max(-1.0, min(1.0, merged))


class SteeringMerger:
    """
    Class-based steering merger for stateful smoothing.
    Industry standard: Simple Python, no extra libraries.
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        smoothing_window: int = 5,
        smoothing_enabled: bool = True
    ):
        """
        Initialize steering merger.
        
        Args:
            weights: Dictionary mapping source names to weights (default: equal weights)
            smoothing_window: Number of recent values to average for smoothing
            smoothing_enabled: Whether to apply smoothing
        """
        self.weights = weights or {}
        self.smoothing_window = smoothing_window
        self.smoothing_enabled = smoothing_enabled
        
        # Store recent steering values per source
        self.source_values: Dict[str, deque] = {}
        self.source_timestamps: Dict[str, deque] = {}
        
        # Store smoothed output history
        self.output_history = deque(maxlen=smoothing_window)
    
    def update_source(self, source: str, steering: float, timestamp: Optional[float] = None):
        """
        Update steering value from a source.
        
        Args:
            source: Source identifier (e.g., "webcam", "phone")
            steering: Steering value in range [-1, 1]
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Clamp steering value
        steering = max(-1.0, min(1.0, float(steering)))
        
        # Initialize deque for this source if needed
        if source not in self.source_values:
            self.source_values[source] = deque(maxlen=self.smoothing_window)
            self.source_timestamps[source] = deque(maxlen=self.smoothing_window)
        
        # Store value and timestamp
        self.source_values[source].append(steering)
        self.source_timestamps[source].append(timestamp)
    
    def get_merged_steering(self) -> float:
        """
        Get merged steering value from all sources.
        Uses simple weighted average with optional smoothing.
        
        Returns:
            Merged steering value in range [-1, 1]
        """
        if not self.source_values:
            return 0.0
        
        # Get current values from each source (most recent)
        current_values = {}
        for source, values in self.source_values.items():
            if values:
                # Use most recent value
                current_values[source] = values[-1]
        
        if not current_values:
            return 0.0
        
        # Use simple merge function
        steering_list = list(current_values.values())
        source_weights = [self.weights.get(s, 1.0) for s in current_values.keys()]
        
        merged = merge_steering(
            steering_list,
            weights=source_weights,
            use_smoothing=self.smoothing_enabled
        )
        
        # Store in history for additional smoothing
        if self.smoothing_enabled:
            self.output_history.append(merged)
            if len(self.output_history) > 1:
                # Simple average of recent values
                merged = sum(self.output_history) / len(self.output_history)
        
        # Clamp final value
        merged = max(-1.0, min(1.0, merged))
        
        return merged
    
    def get_source_count(self) -> int:
        """Get number of active sources."""
        return len([s for s in self.source_values.values() if s])
    
    def get_source_info(self) -> Dict[str, float]:
        """Get current steering value for each source."""
        info = {}
        for source, values in self.source_values.items():
            if values:
                info[source] = values[-1]
        return info
