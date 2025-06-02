"""
Configuration Management for WhatsApp Chat Notes Processor

Handles environment variables, API key validation, and application settings.

Created: January 2025
Author: AI Assistant
Changes: Added dotenv loading and Anthropic API key support for Claude dashboard generation
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration settings for the WhatsApp Chat Notes Processor."""
    
    # API Keys
    assembly_ai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Processing Settings
    use_cache: bool = True
    parallel_processing: bool = False
    max_workers: int = 4
    
    # Audio Processing
    audio_quality: str = "medium"  # low, medium, high
    max_audio_size_mb: int = 25    # Assembly AI limit
    
    # Image/Video Processing
    max_image_size_mb: int = 20    # Gemini limit
    image_quality: str = "medium"  # low, medium, high
    
    # Output Settings
    output_format: str = "txt"     # txt, json (future)
    include_metadata: bool = True
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file first
        load_dotenv()
        
        self.assembly_ai_api_key = os.getenv("ASSEMBLY_AI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Optional settings with defaults
        self.use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
        self.parallel_processing = os.getenv("PARALLEL_PROCESSING", "false").lower() == "true"
        self.max_workers = int(os.getenv("MAX_WORKERS", "4"))
        
        self.audio_quality = os.getenv("AUDIO_QUALITY", "medium")
        self.max_audio_size_mb = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
        
        self.max_image_size_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "20"))
        self.image_quality = os.getenv("IMAGE_QUALITY", "medium")
        
        self.output_format = os.getenv("OUTPUT_FORMAT", "txt")
        self.include_metadata = os.getenv("INCLUDE_METADATA", "true").lower() == "true"
    
    def validate(self) -> None:
        """
        Validate the configuration and API keys.
        
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        logger = logging.getLogger(__name__)
        
        # Check required API keys
        missing_keys = []
        
        if not self.assembly_ai_api_key:
            missing_keys.append("ASSEMBLY_AI_API_KEY")
        
        if not self.gemini_api_key:
            missing_keys.append("GEMINI_API_KEY")
        
        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                f"Please copy env.template to .env and fill in your API keys."
            )
        
        # Validate optional settings
        if self.audio_quality not in ["low", "medium", "high"]:
            logger.warning(f"Invalid audio quality '{self.audio_quality}', using 'medium'")
            self.audio_quality = "medium"
        
        if self.image_quality not in ["low", "medium", "high"]:
            logger.warning(f"Invalid image quality '{self.image_quality}', using 'medium'")
            self.image_quality = "medium"
        
        if self.output_format not in ["txt", "json"]:
            logger.warning(f"Invalid output format '{self.output_format}', using 'txt'")
            self.output_format = "txt"
        
        if self.max_workers < 1 or self.max_workers > 10:
            logger.warning(f"Invalid max_workers '{self.max_workers}', using 4")
            self.max_workers = 4
        
        # Log configuration status
        logger.info("Configuration validated successfully")
        logger.info(f"Assembly AI: {'✓' if self.assembly_ai_api_key else '✗'}")
        logger.info(f"Gemini API: {'✓' if self.gemini_api_key else '✗'}")
        logger.info(f"OpenAI API: {'✓' if self.openai_api_key else '✗ (optional)'}")
        logger.info(f"Anthropic API: {'✓' if self.anthropic_api_key else '✗ (optional)'}")
        logger.debug(f"Parallel processing: {self.parallel_processing}")
        logger.debug(f"Cache enabled: {self.use_cache}")
    
    def get_api_settings(self) -> Dict[str, Any]:
        """Get API-related settings for service initialization."""
        return {
            "assembly_ai_key": self.assembly_ai_api_key,
            "gemini_key": self.gemini_api_key,
            "openai_key": self.openai_api_key,
            "anthropic_key": self.anthropic_api_key,
            "max_audio_size_mb": self.max_audio_size_mb,
            "max_image_size_mb": self.max_image_size_mb,
            "audio_quality": self.audio_quality,
            "image_quality": self.image_quality,
        }
    
    def get_processing_settings(self) -> Dict[str, Any]:
        """Get processing-related settings."""
        return {
            "use_cache": self.use_cache,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "output_format": self.output_format,
            "include_metadata": self.include_metadata,
        } 