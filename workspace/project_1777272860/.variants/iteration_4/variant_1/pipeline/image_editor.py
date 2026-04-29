Here is the raw source code for `pipeline/image_editor.py`:

```python
import torch
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
from transformers import ControlNetModel, ControlNetConditionalGenerationPipeline
from accelerate import Accelerator
from PIL import Image
import numpy as np
import cv2
from .path_utils import safe_join
from pipeline.config import ConfigManager

class ImageEditor:
    def __init__(self, config: ConfigManager):
        self._config = config
        self._accelerator = Accelerator()
        
    def load_controlnet(self) -> ControlNetModel:
        controlnet_path = safe_join(self._config.get('model_paths', 'controlnet'))
        if not controlnet_path:
            raise ValueError("ControlNet model path is None")
        
        controlnet = ControlNetModel.from_pretrained(controlnet_path)
        return controlnet
    
    def load_diffusion_pipeline(self, controlnet: ControlNetModel) -> StableDiffusionPipeline:
        pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        controlnet_pipeline = ControlNetConditionalGenerationPipeline(unet=pipe.unet, scheduler=pipe.scheduler, 
                                                                       controlnet=controlnet)
        return controlnet_pipeline
    
    def apply_prompt_conditioning(self, pipeline: StableDiffusionPipeline, prompt: str):
        if not prompt:
            raise ValueError("Prompt is None")
        
        image = pipeline(prompt).images[0]
        return image
```
Please note that this code assumes the existence of `pipeline/config.py` and `pipeline/path_utils.py` modules, which are not provided in your request. You should have these files available to run this script successfully. Also, ensure you replace placeholders with actual values in the config file before running the script.