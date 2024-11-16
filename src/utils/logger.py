import logging
from typing import Optional

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name (str, optional): Name for the logger. If None, returns the root logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers haven't been set up
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return logger
