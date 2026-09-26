"""Main application runner for AI inference service."""
import json
from pathlib import Path
from inference.detector import ObjectDetector
from inference.blur_detection import CameraBlurDetector
from inference.tracker import CentroidTracker


def load_config():
    config_path = Path(__file__).parent / "config" / "settings.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def main():
    config = load_config()
    blur_cfg = config.get("blur_detection", {})
    detector = ObjectDetector()
    blur_detector = CameraBlurDetector(
        confidence_threshold=blur_cfg.get("confidence_threshold", 0.45),
        consecutive_frame_threshold=blur_cfg.get("consecutive_frame_threshold", 3)
    )
    tracker = CentroidTracker()
    print("AI Inference Service initialized successfully.")


if __name__ == "__main__":
    main()
