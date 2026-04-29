from controlnet_aux import OpenposeDetector
from PIL import Image

class PoseExtractor:
    def __init__(self):
        print("Loading OpenPose detector...")
        self.processor = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

    def extract_pose(self, image: Image.Image) -> Image.Image:
        """Extracts the OpenPose skeleton from the input image."""
        pose_image = self.processor(image)
        return pose_image