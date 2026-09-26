"""Helper script to reset the demo repository to its initial buggy state for live demonstration."""
from pathlib import Path

BUGGY_CODE = '''"""Camera blur detection module for AI inference service.

AICV-1432 Context:
Camera blur detection monitors video frames to detect degraded or blurred camera feeds.
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
        
        # NOTE: State tracking across frames
        self.consecutive_low_confidence_frames = 0
        self.is_blurred = False

    def check_laplacian_fallback(self, laplacian_variance: Optional[float]) -> bool:
        """Fallback check based on Laplacian variance measure."""
        if not self.enable_laplacian_fallback or laplacian_variance is None:
            return False
        return laplacian_variance < self.laplacian_var_threshold

    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single frame to evaluate blur condition.
        
        BUG (AICV-1432):
        Currently evaluates object confidence independently per frame and triggers
        immediately if low_confidence_objects >= 2, ignoring consecutive_frame_threshold.
        Transient drops cause false positives and state resets prematurely.
        """
        detections: List[Dict[str, Any]] = frame_data.get("detections", [])
        laplacian_variance: Optional[float] = frame_data.get("laplacian_variance")

        low_confidence_objects = sum(
            1 for d in detections if d.get("confidence", 1.0) < self.confidence_threshold
        )

        # BUGGY IMPLEMENTATION:
        # Does not track consecutive frames properly! Triggers on a single transient frame.
        if low_confidence_objects >= 2:
            self.is_blurred = True
        else:
            self.is_blurred = False

        # Fallback check
        if not self.is_blurred and self.check_laplacian_fallback(laplacian_variance):
            self.is_blurred = True

        return {
            "is_blurred": self.is_blurred,
            "low_confidence_objects": low_confidence_objects,
            "consecutive_low_confidence_frames": self.consecutive_low_confidence_frames,
            "laplacian_fallback_triggered": self.check_laplacian_fallback(laplacian_variance)
        }

    def reset_state(self):
        """Reset state tracking."""
        self.consecutive_low_confidence_frames = 0
        self.is_blurred = False
'''

target = Path(__file__).resolve().parent.parent / "ai-inference-service" / "inference" / "blur_detection.py"
target.write_text(BUGGY_CODE, encoding="utf-8")
print(f"Successfully reset {target} to initial buggy state for AICV-1432 demo.")
