import logging
from ..utils.config import Config

def setup_logger(name: str) -> logging.Logger:
    """Configure a logger with console handler and formatter.
    
    Args:
        name: Name for the logger instance
    
    Returns:
        logging.Logger: Configured logger with console handler
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    logger.setLevel(Config.get_log_level())
    
    return logger
