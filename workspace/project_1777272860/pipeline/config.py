import torch

class Config:
    # Model IDs
    BASE_MODEL_ID = "runwayml/stable-diffusion-inpainting"
    CONTROLNET_MODEL_ID = "lllyasviel/sd-controlnet-openpose"
    
    # Device
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Quality Presets
    PRESETS = {
        "speed": {
            "num_inference_steps": 20,
            "guidance_scale": 7.0,
            "resolution": 512
        },
        "quality": {
            "num_inference_steps": 50,
            "guidance_scale": 8.5,
            "resolution": 768
        }
    }