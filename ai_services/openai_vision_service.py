"""
OpenAI Vision Service Integration

Provides image understanding capabilities using OpenAI's vision models
as a backup service when Gemini API fails or hits rate limits.

Created: January 2025
Author: AI Assistant
Changes: Initial implementation of OpenAI Vision API for image backup processing
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import base64

try:
    import openai
except ImportError:
    openai = None

from file_manager import MediaFile


@dataclass
class VisionResponse:
    """Response from OpenAI Vision API."""
    success: bool
    description: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    confidence: Optional[float] = None


class OpenAIVisionService:
    """OpenAI Vision service for image understanding."""
    
    def __init__(self, api_key: str, max_image_size_mb: int = 20):
        """
        Initialize OpenAI Vision service.
        
        Args:
            api_key: OpenAI API key
            max_image_size_mb: Maximum image file size in MB
        """
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.api_key = api_key
        self.max_image_size_mb = max_image_size_mb
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=api_key)
            self.logger.info("OpenAI Vision client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI Vision client: {e}")
            raise
        
        # Supported image formats
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp'
        }
        
        # Default model
        self.model = "gpt-4o-mini"  # Updated model name from user's example
    
    def describe_image(self, media_file: MediaFile, 
                      prompt: str = "Describe this image in detail, focusing on the main subjects, setting, and any notable features or activities.") -> VisionResponse:
        """
        Generate a description of an image using OpenAI Vision.
        
        Args:
            media_file: MediaFile object containing image information
            prompt: Custom prompt for image description
            
        Returns:
            VisionResponse with description or error
        """
        start_time = time.time()
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_formats:
                return VisionResponse(
                    success=False,
                    error=f"Unsupported image format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_image_size_mb:
                return VisionResponse(
                    success=False,
                    error=f"Image too large: {size_mb:.1f}MB (max: {self.max_image_size_mb}MB)"
                )
            
            self.logger.debug(f"Processing image with OpenAI Vision: {media_file.filename}")
            
            # Encode image as base64
            with open(media_file.filepath, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Generate response using base64 encoding
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                max_tokens=300
            )
            
            description = response.choices[0].message.content
            if not description or not description.strip():
                return VisionResponse(
                    success=False,
                    error="Empty response from OpenAI Vision"
                )
            
            processing_time = time.time() - start_time
            
            self.logger.info(
                f"Image described successfully with OpenAI Vision: {media_file.filename} "
                f"({processing_time:.2f}s, {len(description)} chars)"
            )
            
            return VisionResponse(
                success=True,
                description=description.strip(),
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"OpenAI Vision error for {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return VisionResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def _create_file(self, file_path: Path) -> Optional[str]:
        """
        Upload file to OpenAI Files API.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            File ID if successful, None otherwise
        """
        # This method is no longer used but kept for compatibility
        try:
            with open(file_path, "rb") as file_content:
                result = self.client.files.create(
                    file=file_content,
                    purpose="vision"
                )
                return result.id
        except Exception as e:
            self.logger.error(f"Failed to upload file to OpenAI: {e}")
            return None
    
    def describe_with_retry(self, media_file: MediaFile, 
                           max_retries: int = 2,
                           retry_delay: float = 2.0) -> VisionResponse:
        """
        Describe image with retry mechanism.
        
        Args:
            media_file: MediaFile object containing image information
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            VisionResponse with description or error
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(f"OpenAI Vision retry attempt {attempt}/{max_retries} for {media_file.filename}")
                time.sleep(retry_delay)
            
            response = self.describe_image(media_file)
            
            if response.success:
                if attempt > 0:
                    self.logger.info(f"OpenAI Vision succeeded on retry {attempt}")
                return response
            
            last_error = response.error
            
            # Don't retry on certain types of errors
            if any(error_type in response.error.lower() for error_type in [
                'unsupported', 'too large', 'invalid format'
            ]):
                self.logger.debug(f"Not retrying OpenAI Vision due to error type: {response.error}")
                break
        
        self.logger.error(f"OpenAI Vision failed after {max_retries} retries: {last_error}")
        return VisionResponse(
            success=False,
            error=f"Failed after {max_retries} retries: {last_error}"
        )
    
    def test_connection(self) -> bool:
        """Test if the OpenAI Vision API connection is working."""
        try:
            # Simple test by checking available models
            models = self.client.models.list()
            return any(self.model in model.id for model in models.data)
        except Exception as e:
            self.logger.error(f"OpenAI Vision connection test failed: {e}")
            return False
    
    def estimate_cost(self, num_images: int) -> float:
        """
        Estimate the cost for processing images.
        
        Args:
            num_images: Number of images to process
            
        Returns:
            Estimated cost in USD
        """
        # OpenAI Vision pricing for gpt-4o-mini: ~$0.003 per image
        cost_per_image = 0.003
        return num_images * cost_per_image 