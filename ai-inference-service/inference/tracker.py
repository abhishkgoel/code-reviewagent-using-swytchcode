"""Centroid tracker for multi-object tracking."""
from typing import List, Dict, Tuple


class CentroidTracker:
    def __init__(self, max_disappeared: int = 5):
        self.next_object_id = 0
        self.objects: Dict[int, Tuple[int, int]] = {}
        self.disappeared: Dict[int, int] = {}
        self.max_disappeared = max_disappeared

    def register(self, centroid: Tuple[int, int]) -> int:
        object_id = self.next_object_id
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.next_object_id += 1
        return object_id

    def deregister(self, object_id: int):
        del self.objects[object_id]
        del self.disappeared[object_id]
