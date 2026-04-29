import os
from typing import Optional

def safe_join(base: str, *paths: str) -> Optional[str]:
    """
    Safely join paths while preventing 'NoneType' errors during path joining.
    
    Args:
        base (str): Base directory to start from.
        *paths (str): Additional directories or files to add.
        
    Returns:
        str: The joined path if all inputs are valid, None otherwise.
    """
    for p in paths:
        # If any of the paths is None, return None immediately
        if p is None:
            return None
            
        base = os.path.join(base, p)
        
    # Check if the final path exists
    if not os<｜begin▁of▁sentence｜>.path.exists(base):
        print(f"Error: Path {base} does not exist.")
        return None
    
    return base