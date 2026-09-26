"""Regression and unit tests for CameraBlurDetector.

AICV-1432:
Tests verify consecutive-frame blur state tracking and prevention of false-positives
on transient single-frame drops.
"""
import unittest
from inference.blur_detection import CameraBlurDetector


class TestCameraBlurDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CameraBlurDetector(
            confidence_threshold=0.45,
            consecutive_frame_threshold=3,
            laplacian_var_threshold=100.0,
            enable_laplacian_fallback=True
        )

    def test_single_low_confidence_frame_should_not_trigger_blur(self):
        """Single transient frame with low confidence must NOT trigger blur event."""
        transient_frame = {
            "detections": [
                {"label": "vehicle", "confidence": 0.20},
                {"label": "pedestrian", "confidence": 0.15}
            ],
            "laplacian_variance": 150.0  # High variance (clear image)
        }
        res = self.detector.process_frame(transient_frame)
        self.assertFalse(
            res["is_blurred"],
            "Single low-confidence frame should not trigger blur. Requires 3 consecutive frames!"
        )

    def test_consecutive_low_confidence_frames_triggers_blur(self):
        """Blur should trigger only after consecutive_frame_threshold frames."""
        low_conf_frame = {
            "detections": [
                {"label": "vehicle", "confidence": 0.20},
                {"label": "pedestrian", "confidence": 0.15}
            ],
            "laplacian_variance": 150.0
        }
        # Frame 1: count=1, not blurred
        r1 = self.detector.process_frame(low_conf_frame)
        # Frame 2: count=2, not blurred
        r2 = self.detector.process_frame(low_conf_frame)
        # Frame 3: count=3, blurred!
        r3 = self.detector.process_frame(low_conf_frame)

        self.assertTrue(r3["is_blurred"])
        self.assertEqual(r3["consecutive_low_confidence_frames"], 3)

    def test_recovery_to_normal_confidence_resets_state(self):
        """Normal frames should reset the consecutive counter and clear blur."""
        low_conf_frame = {
            "detections": [{"label": "car", "confidence": 0.1}],
            "laplacian_variance": 150.0
        }
        normal_frame = {
            "detections": [{"label": "car", "confidence": 0.9}],
            "laplacian_variance": 150.0
        }
        self.detector.process_frame(low_conf_frame)
        self.detector.process_frame(normal_frame)
        self.assertEqual(self.detector.consecutive_low_confidence_frames, 0)
        self.assertFalse(self.detector.is_blurred)

    def test_laplacian_fallback_when_variance_low(self):
        """Laplacian fallback triggers blur when visual variance is below threshold."""
        blurry_frame = {
            "detections": [{"label": "car", "confidence": 0.9}],
            "laplacian_variance": 45.0  # Below 100.0 threshold
        }
        res = self.detector.process_frame(blurry_frame)
        self.assertTrue(res["is_blurred"])
        self.assertTrue(res["laplacian_fallback_triggered"])


if __name__ == "__main__":
    unittest.main()
