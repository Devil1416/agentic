import os
from typing import Optional
from pipeline.pose_extractor import PoseExtractor
from pipeline.image_editor import ImageEditor
from pipeline.path_utils import safe_join    # Importing local module

def main(input_img_path: str, output_img_path: str, pose_model_path: Optional[str] = None, edit_model_path: Optional[str] = None):
    if not os.path.exists(input_img_path):
        raise ValueError('Input image path does not exist')
    
    # Initialize PoseExtractor and ImageEditor with safe paths
    pose_extractor = PoseExtractor(safe_join(pose_model_path)) if pose_model_path else None
    image_editor = ImageEditor(safe_join(edit_model_path)) if edit_model_path else None
    
    # Load input image
    img = cv2.imread(input_img_path)
    
    try:
        # Extract pose from image
        if pose_extractor:
            poses = pose_extractor.extract_pose(img)
        
        # Edit image based on extracted pose
        if image_editor:
            img = image_editor.edit_image(img, poses)
    except Exception as e:
        print('Error during pipeline execution:', str(e))
        return
    
    # Save resultant image
    cv2.imwrite(safe_join(output_img_path), img)