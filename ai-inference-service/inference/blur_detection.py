"""Camera blur detection module for AI inference service.

AICV-1432 Context:
Camera blur detection monitors video frames to detect degraded or blurred camera feeds.
Fixed by DevPilot: Maintains consecutive-frame low-confidence state tracking.
"""
from typing import Dict, Any, List, Optional


class CameraBlurDetector:
    def __init__(
        self,
        confidence_threshold: float = 0.45,
        consecutive_frame_threshold: int = 3,
        laplacian_var_threshold: float = 100.0,
        enable_laplacian_fallback: bool = True
    ):
        self.confidence_threshold = confidence_threshold
        self.consecutive_frame_threshold = consecutive_frame_threshold
        self.laplacian_var_threshold = laplacian_var_threshold
        self.enable_laplacian_fallback = enable_laplacian_fallback
        
        # State tracking across sequential frames
        self.consecutive_low_confidence_frames = 0
        self.is_blurred = False

    def check_laplacian_fallback(self, laplacian_variance: Optional[float]) -> bool:
        """Fallback check based on Laplacian variance measure."""
        if not self.enable_laplacian_fallback or laplacian_variance is None:
            return False
        return laplacian_variance < self.laplacian_var_threshold

    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single frame to evaluate blur condition.
        
        AICV-1432 Fix:
        Accurately increments consecutive_low_confidence_frames and only triggers blur
        when the threshold is reached. Resets counter upon frame recovery.
        """
        detections: List[Dict[str, Any]] = frame_data.get("detections", [])
        laplacian_variance: Optional[float] = frame_data.get("laplacian_variance")

        # Count low confidence detections
        low_confidence_objects = sum(
            1 for d in detections if d.get("confidence", 1.0) < self.confidence_threshold
        )

        has_low_confidence = (low_confidence_objects >= 2) or (
            len(detections) > 0 and (low_confidence_objects / len(detections)) > 0.5
        )

        if has_low_confidence:
            self.consecutive_low_confidence_frames += 1
        else:
            # Normal frame detected: reset consecutive counter
            self.consecutive_low_confidence_frames = 0
            self.is_blurred = False

        # Only trigger blur if threshold of consecutive frames is reached
        if self.consecutive_low_confidence_frames >= self.consecutive_frame_threshold:
            self.is_blurred = True

        # Fallback check: Laplacian variance measure
        laplacian_triggered = self.check_laplacian_fallback(laplacian_variance)
        if not self.is_blurred and laplacian_triggered:
            self.is_blurred = True

        return {
            "is_blurred": self.is_blurred,
            "low_confidence_objects": low_confidence_objects,
            "consecutive_low_confidence_frames": self.consecutive_low_confidence_frames,
            "laplacian_fallback_triggered": laplacian_triggered
        }

    def reset_state(self):
        """Reset state tracking."""
        self.consecutive_low_confidence_frames = 0
        self.is_blurred = False
