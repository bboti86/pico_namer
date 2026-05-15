import logging
import json
import os
import sys

def setup_logger(name):
    """
    Sets up a configured logger.
    The log level is determined by the 'log_level' key in config.json.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        log_level_str = "INFO"
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    log_level_str = config.get("log_level", "INFO").upper()
        except Exception:
            pass
            
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_map.get(log_level_str, logging.INFO)
        
        logger.setLevel(level)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)

        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        ch.setFormatter(formatter)

        logger.addHandler(ch)

    return logger
