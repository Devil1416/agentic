from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import io
import numpy as np

try:
    from rembg import remove
except ImportError:
    remove = None

from pipeline.pose_extractor import PoseExtractor
from pipeline.image_editor import ImageEditor

app = FastAPI(
    title="Pose-Guided Image Editor API",
    description="Modular pipeline for pose extraction, background removal, and conditional generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy loading of ML models to avoid slow startup until first request
editor = None
pose_extractor = None

def get_editor():
    global editor
    if editor is None:
        editor = ImageEditor()
    return editor

def get_pose_extractor():
    global pose_extractor
    if pose_extractor is None:
        pose_extractor = PoseExtractor()
    return pose_extractor

@app.post("/edit_image")
async def edit_image_api(
    primary_image: UploadFile = File(..., description="The main scene image"),
    secondary_image: UploadFile = File(None, description="The subject to composite into the scene (optional)"),
    prompt: str = Form(..., description="The editing instruction or generation prompt"),
    mode: str = Form("quality", description="'speed' or 'quality'")
):
    try:
        # Load primary image
        primary_data = await primary_image.read()
        primary_pil = Image.open(io.BytesIO(primary_data)).convert("RGB")
        
        if secondary_image:
            sec_data = await secondary_image.read()
            
            # Remove background from secondary subject if rembg is installed
            if remove:
                subject_no_bg = remove(sec_data)
                subject_pil = Image.open(io.BytesIO(subject_no_bg)).convert("RGBA")
            else:
                subject_pil = Image.open(io.BytesIO(sec_data)).convert("RGBA")
            
            # Extract mask from alpha channel (if present, else make full mask)
            if subject_pil.mode == "RGBA":
                mask_np = np.array(subject_pil)[:, :, 3]
                mask_pil = Image.fromarray(mask_np).convert("L")
            else:
                mask_pil = Image.new("L", subject_pil.size, 255)
            
            # Extract pose from the segmented subject
            pose_map = get_pose_extractor().extract_pose(subject_pil.convert("RGB"))
        else:
            # If no secondary image, we extract pose from primary and mask everything to regenerate
            mask_pil = Image.new("L", primary_pil.size, 255) # White mask = replace all based on pose
            pose_map = get_pose_extractor().extract_pose(primary_pil)
        
        # Run diffusion pipeline
        result_img = get_editor().edit(
            primary_image=primary_pil,
            mask_image=mask_pil,
            pose_image=pose_map,
            prompt=prompt,
            quality_preset=mode
        )
        
        # Return as bytes
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='JPEG')
        
        return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "models_loaded": editor is not None}

if __name__ == "__main__":
    print("Starting Pose-Guided Image Editor API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)