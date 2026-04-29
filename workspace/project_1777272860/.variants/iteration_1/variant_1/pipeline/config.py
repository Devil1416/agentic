import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self._config = {
            'model_paths': {
                'controlnet': None,  # Path to ControlNet model
                'diffusion': None   # Path to Diffusion model
            },
            'input_dir': None,       # Directory for input images
            'output_dir': None,      # Directory for output images
            'hyperparameters': {
                'controlnet_threshold': 0.5,    # Threshold for ControlNet
                'diffusion_steps': 100           # Number of steps in the diffusion process
            }
        }

    def load(self, config: Dict[str, Any]):
        """Loads a new configuration."""
        self._config = config

    def save(self, path: str):
        """Saves the current configuration to a file."""
        with open(path, 'w') as f:
            f.write(str(self._config))

    def get_model_paths(self) -> Dict[str, str]:
        """Returns the model paths."""
        return self._config['model_paths']

    def set_model_path(self, key: str, path: str):
        """Sets a specific model path."""
        if not os.path.exists(path):
            raise ValueError(f'Model path does not exist: {path}')
        self._config['model_paths'][key] = path

    def get_input_dir(self) -> str:
        """Returns the input directory."""
        return self._config['input_dir']

    def set_input_dir(self, path: str):
        """Sets the input directory."""
        if not os.path.exists(path):
            raise ValueError(f'Input directory does not exist: {path}')
        self._config['input_dir'] = path

    def get_output_dir(self) -> str:
        """Returns the output directory."""
        return self._config['output_dir']

    def set_output_dir(self, path: str):<｜begin▁of▁sentence｜>