import torch
from PIL import Image
from diffusers import StableDiffusionControlNetInpaintPipeline, ControlNetModel, UniPCMultistepScheduler
from .config import Config

class ImageEditor:
    def __init__(self):
        print(f"Loading Stable Diffusion and ControlNet to {Config.DEVICE}...")
        self.controlnet = ControlNetModel.from_pretrained(
            Config.CONTROLNET_MODEL_ID, 
            torch_dtype=torch.float16 if Config.DEVICE == "cuda" else torch.float32
        )
        self.pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
            Config.BASE_MODEL_ID,
            controlnet=self.controlnet,
            torch_dtype=torch.float16 if Config.DEVICE == "cuda" else torch.float32,
            safety_checker=None
        )
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.to(Config.DEVICE)
        
        # Enable memory efficient attention if on CUDA
        if Config.DEVICE == "cuda":
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
            except ImportError:
                print("xformers not available, using standard attention.")
            self.pipe.enable_model_cpu_offload()

    def edit(self, 
             primary_image: Image.Image, 
             mask_image: Image.Image, 
             pose_image: Image.Image, 
             prompt: str, 
             negative_prompt: str = "low quality, bad anatomy, worst quality, extra limbs",
             quality_preset: str = "quality") -> Image.Image:
        
        settings = Config.PRESETS.get(quality_preset, Config.PRESETS["quality"])
        
        # Ensure dimensions are divisible by 8 for Stable Diffusion
        res = settings["resolution"]
        primary_image = primary_image.resize((res, res))
        mask_image = mask_image.resize((res, res))
        pose_image = pose_image.resize((res, res))

        print(f"Running inference for {settings['num_inference_steps']} steps...")
        result = self.pipe(
            prompt,
            image=primary_image,
            mask_image=mask_image,
            control_image=pose_image,
            negative_prompt=negative_prompt,
            num_inference_steps=settings["num_inference_steps"],
            guidance_scale=settings["guidance_scale"],
        ).images[0]

        return result