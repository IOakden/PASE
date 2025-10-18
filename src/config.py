"""
Configuration management for PASE project.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(config['output']['logs_dir'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = getattr(logging, config['logging']['level'])
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / 'pase.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('PASE')
    logger.info("Logging initialized")
    
    return logger


def create_directories(config: Dict[str, Any]) -> None:
    """
    Create necessary directories based on configuration.
    
    Args:
        config: Configuration dictionary
    """
    directories = [
        config['data']['pdb_dir'],
        config['data']['asbench_dir'],
        config['data']['processed_dir'],
        config['output']['models_dir'],
        config['output']['figures_dir'],
        config['output']['logs_dir'],
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def get_device(config: Dict[str, Any]) -> str:
    """
    Get the appropriate device based on configuration and availability.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Device string ('cuda', 'mps', or 'cpu')
    """
    import torch
    
    requested_device = config['hardware']['device']
    
    if requested_device == 'cuda' and torch.cuda.is_available():
        return 'cuda'
    elif requested_device == 'mps' and torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'


def set_seed(seed: int) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed value
    """
    import random
    import numpy as np
    import torch
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # For deterministic behavior (may impact performance)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

