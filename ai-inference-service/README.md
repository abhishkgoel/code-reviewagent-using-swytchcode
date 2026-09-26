# AI Inference Service

High-performance real-time computer vision inference and camera quality monitoring pipeline.

## Modules
- `inference/detector.py`: Object detection with confidence scoring
- `inference/blur_detection.py`: Camera blur detection with frame confidence evaluation & Laplacian fallback
- `inference/tracker.py`: Multi-object tracking across sequential video frames

## Running Tests
```bash
python3 -m unittest discover -s tests
```
