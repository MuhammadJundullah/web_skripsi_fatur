import os
import cv2
import numpy as np
import torch
from ultralytics import YOLO

HEALTHY_CLASS_NAME = "Udang Vanamei Sehat"
NORMALIZED_HEALTHY_CLASS_NAME = HEALTHY_CLASS_NAME.strip().lower()

def is_healthy_class(class_name: str) -> bool:
    return class_name.strip().lower() == NORMALIZED_HEALTHY_CLASS_NAME

class MockBoxes:
    def __init__(self, cls_list, id_list=None):
        self.cls = torch.tensor(cls_list)
        if id_list is not None:
            self.id = torch.tensor(id_list)
        else:
            self.id = None
        self.cls_list = cls_list
        self.id_list = id_list
        
    def __iter__(self):
        # When iterating, return individual Box mocks
        for i in range(len(self.cls_list)):
            yield MockBox(self.cls_list[i], self.id_list[i] if self.id_list is not None else None)

    def __len__(self):
        return len(self.cls_list)

class MockBox:
    def __init__(self, cls_val, id_val=None):
        self.cls = torch.tensor([cls_val])
        self.id = torch.tensor([id_val]) if id_val is not None else None

def process_boxes(results, model_names):
    seen_healthy_ids = set()
    seen_diseased_ids = set()
    
    current_healthy = 0
    current_diseased = 0
    
    if results and results.boxes:
        boxes = results.boxes
        # Extract track_ids
        track_ids = boxes.id.int().cpu().tolist() if boxes.id is not None else None
        
        for i, box in enumerate(boxes):
            class_id = int(box.cls[0])
            class_name = model_names[class_id]
            is_healthy = is_healthy_class(class_name)
            
            if is_healthy:
                current_healthy += 1
            else:
                current_diseased += 1
                
            if track_ids is not None:
                track_id = track_ids[i]
                if is_healthy:
                    seen_healthy_ids.add(track_id)
                else:
                    seen_diseased_ids.add(track_id)
                    
    # If tracking IDs are active, use unique counts; otherwise fall back to current frame count
    if len(seen_healthy_ids) > 0 or len(seen_diseased_ids) > 0:
        healthy_count = len(seen_healthy_ids)
        diseased_count = len(seen_diseased_ids)
    else:
        healthy_count = current_healthy
        diseased_count = current_diseased
        
    return healthy_count, diseased_count

# Run tests
model_names = {0: "Udang Tidak Sehat", 3: "Udang Vanamei Sehat"}

print("Test 1: With track IDs")
boxes_1 = MockBoxes([3, 3, 0], [10, 11, 20])
class MockResultsWrapper:
    def __init__(self, boxes):
        self.boxes = boxes

results_1 = MockResultsWrapper(boxes_1)
h, d = process_boxes(results_1, model_names)
print(f"Results: Healthy={h}, Diseased={d}")

print("Test 2: Without track IDs")
boxes_2 = MockBoxes([3, 0], None)
results_2 = MockResultsWrapper(boxes_2)
h, d = process_boxes(results_2, model_names)
print(f"Results: Healthy={h}, Diseased={d}")

print("Test 3: Empty boxes")
boxes_3 = MockBoxes([], None)
results_3 = MockResultsWrapper(boxes_3)
h, d = process_boxes(results_3, model_names)
print(f"Results: Healthy={h}, Diseased={d}")
