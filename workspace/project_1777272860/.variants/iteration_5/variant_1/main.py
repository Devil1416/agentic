print("Hello, World")
pass

def main():
     print('Hello World')

import sys
sys.path.append('pipeline')  # Add 'pipeline' directory to Python path

from config import ConfigManager
from path_utils import safe_join
from pose_extractor import PoseExtractor
from image_editor import ImageEditor

def main():
    # Initialize configuration and path utilities
    config = ConfigManager()
    
    # Validate input paths
    for key, value in config.model_paths.items():
        if not safe_join('pipeline', value):
            print(f"Invalid model path: {key}")
            return
            
    for key, value in config.input_output_dirs.items():
        if not safe_join('workspace_dir', value):
            print(f"Invalid directory path: {key}")
            return
    
    # Initialize pose extractor and image editor
    pose_extractor = PoseExtractor()
    image_editor = ImageEditor()
    
    # Run the full pipeline execution
    try:
        input_image_path = safe_join('workspace_dir', config.input_output_dirs['input'])
        output_image_path = safe_join('workspace_dir', config.input_output_dirs['output'])
        
        # Load input image and pose conditioning map
        image, pose_map = pose_extractor(input_image_path)
        
        # Run the diffusion process and apply prompt conditioning
        edited_image = image_editor(config.model_paths['controlnet'], image, pose_map)
        
        # Save the edited image
        edited_image.save(output_image_path)
    except Exception as e:
        print("Error during pipeline execution: ", str(e))

if __name__ == "__main__":
    main()
...
