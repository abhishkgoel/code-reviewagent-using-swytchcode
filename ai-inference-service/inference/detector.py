"""Object detection module."""
from typing import List, Dict, Any


class ObjectDetector:
    def __init__(self, model_name: str = "default_yolo", confidence_threshold: float = 0.5):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold

    def detect(self, frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate detection on frame."""
        raw_detections = frame_data.get("detections", [])
        return [
            d for d in raw_detections
            if d.get("confidence", 0.0) >= self.confidence_threshold
        ]
