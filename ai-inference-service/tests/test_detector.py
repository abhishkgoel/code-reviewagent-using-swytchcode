"""Unit tests for ObjectDetector."""
import unittest
from inference.detector import ObjectDetector


class TestObjectDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ObjectDetector(confidence_threshold=0.5)

    def test_filter_low_confidence(self):
        frame = {
            "detections": [
                {"label": "person", "confidence": 0.85},
                {"label": "car", "confidence": 0.30},
                {"label": "dog", "confidence": 0.60}
            ]
        }
        results = self.detector.detect(frame)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "person")
        self.assertEqual(results[1]["label"], "dog")


if __name__ == "__main__":
    unittest.main()
