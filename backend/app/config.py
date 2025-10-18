"""
Backend configuration management.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]
    
    # Paths
    model_path: str = "../outputs/models/gvp_v1.pt"
    data_path: str = "../data/processed"
    upload_dir: str = "./uploads"
    
    # Model status
    model_status: str = "training"
    current_phase: str = "2 of 12 complete"
    validated_proteins: int = 116
    allosteric_residues: int = 2137
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

