import os
from typing import Optional
from .path_utils import safe_join   # Importing local module

class ImageEditor:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def edit(self, image_path: Optional[str], output_path: Optional[str]) -> None:
        if not safe_join('', image_path):  # Checking for valid image path
            raise ValueError("Invalid image path")
        
        if not output_path:  # If no output path is provided, use the same as input
            output_path = image_path
            
        # Rest of your code to edit and save the image goes here.