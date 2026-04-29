Here is the raw source code for `pipeline/pose_extractor.py`:

```python
import torch
from typing import Tuple, Union
from .path_utils import safe_join
from PIL import Image
import numpy as np
import cv2

class PoseExtractor:
    def __init__(self, model_path: str):
        self.model = torch.hub.load('CMU-Perceptual-Computing-Lab/openpose', 'pose_coco')
        self.model.setModelComplexity(1)  # Set the model complexity to 1 (medium)
        self.model.setNumThreads(4)      # Set the number of threads to 4
        self.model.setInputParams(size=368)   # Set input size to 368x368 pixels

    def extract_pose(self, image: Union[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        if isinstance(image, str):
            img = cv2.imread(safe_join(image))  # Load the image from file
            image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # Convert to PIL Image and RGB color space
        elif isinstance(image, np.ndarray):
            pass  # Assume it's already an OpenCV image
        else:
            raise ValueError("Input must be a string (path to image) or a numpy array")
        
        dataloader_output = self.model.forward(np.array([image]), True)   # Forward pass through the model
        keypoints, heatmaps = dataloader_output['keypoints'], dataloader_output['heatmaps']  # Extract keypoints and heatmaps
        
        return keypoints, heatmaps
```

This code defines a class `PoseExtractor` that uses the OpenPose model from PyTorch Hub to extract pose information from images. The `extract_pose` method takes an image (either as a file path or a numpy array) and returns the keypoints and heatmaps produced by the model.