import os
from typing import Union

def safe_join(base: str, *paths: Union[str, None]) -> str:
    """
    Safely join paths while handling None inputs.
    
    If any of the path components are None, an empty string is returned for that component. 
    This prevents a TypeError from os.path.join().
    """
    if not base and not paths:
        raise ValueError("At least one argument must be provided")
        
    safe_paths = [""] + list(paths)
    
    for i, path in enumerate(safe_paths):
        if path is None:
            safe_paths[i] = ""
            
    return os.path.join(base, *safe_paths)