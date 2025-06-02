"""
Google Gemini AI Service Integration

Handles image and video description using Google Gemini Vision API with
rate limiting, error handling, and retry mechanisms.

Created: January 2025
Author: AI Assistant
Changes: Fixed Google Generative AI import for proper initialization
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import base64
from dataclasses import dataclass

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from file_manager import MediaFile


@dataclass
class GeminiResponse:
    """Response from Gemini API."""
    success: bool
    description: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time: float = 0.0


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 15):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum API calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            wait_time = self.min_interval - time_since_last_call
            logging.getLogger(__name__).debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        self.last_call_time = time.time()


class GeminiService:
    """Google Gemini AI service for image and video description."""
    
    def __init__(self, api_key: str, max_image_size_mb: int = 20):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Google API key
            max_image_size_mb: Maximum image size in MB
        """
        if not genai:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key
        self.max_image_size_mb = max_image_size_mb
        self.logger = logging.getLogger(__name__)
        
        # Initialize client with API key
        try:
            genai.configure(api_key=api_key)
            self.logger.info("Gemini client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise
        
        # Rate limiter (Gemini API: 15 requests per minute for free tier)
        self.rate_limiter = RateLimiter(calls_per_minute=15)
        
        # Supported formats
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
        self.supported_video_formats = {'.mp4', '.mov', '.avi', '.mkv', '.3gp', '.webm'}
        
        # Model to use
        self.model_name = "gemini-2.0-flash"
    
    def describe_image(self, media_file: MediaFile, 
                      custom_prompt: Optional[str] = None) -> GeminiResponse:
        """
        Generate description for an image file.
        
        Args:
            media_file: MediaFile object containing image information
            custom_prompt: Optional custom prompt for description
            
        Returns:
            GeminiResponse with description or error
        """
        start_time = time.time()
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_image_formats:
                return GeminiResponse(
                    success=False,
                    error=f"Unsupported image format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_image_size_mb:
                return GeminiResponse(
                    success=False,
                    error=f"Image too large: {size_mb:.1f}MB (max: {self.max_image_size_mb}MB)"
                )
            
            # Default prompt for image description
            prompt = custom_prompt or (
                "Describe this image in detail. Focus on the main subjects, objects, "
                "activities, setting, and any text visible in the image. "
                "Be concise but comprehensive."
            )
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Process image
            self.logger.debug(f"Processing image: {media_file.filename}")
            
            if size_mb > 20:  # Use Files API for large files
                response = self._process_large_image(media_file, prompt)
            else:  # Use inline processing for smaller files
                response = self._process_small_image(media_file, prompt)
            
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            if response.success:
                self.logger.info(f"Image described successfully: {media_file.filename} ({processing_time:.2f}s)")
            else:
                self.logger.warning(f"Image description failed: {media_file.filename} - {response.error}")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing image {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return GeminiResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def describe_video(self, media_file: MediaFile, 
                      custom_prompt: Optional[str] = None) -> GeminiResponse:
        """
        Generate description for a video file.
        
        Args:
            media_file: MediaFile object containing video information
            custom_prompt: Optional custom prompt for description
            
        Returns:
            GeminiResponse with description or error
        """
        start_time = time.time()
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_video_formats:
                return GeminiResponse(
                    success=False,
                    error=f"Unsupported video format: {media_file.extension}"
                )
            
            # Check file size (videos are typically larger, be more lenient)
            size_mb = media_file.size_bytes / (1024 * 1024)
            max_video_size = self.max_image_size_mb * 2  # Allow 2x for videos
            if size_mb > max_video_size:
                return GeminiResponse(
                    success=False,
                    error=f"Video too large: {size_mb:.1f}MB (max: {max_video_size}MB)"
                )
            
            # Default prompt for video description
            prompt = custom_prompt or (
                "Describe this video in detail. Focus on the main subjects, activities, "
                "setting, and any notable events or changes throughout the video. "
                "Be concise but comprehensive."
            )
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Process video (always use Files API for videos)
            self.logger.debug(f"Processing video: {media_file.filename}")
            response = self._process_video_with_files_api(media_file)
            
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            if response.success:
                self.logger.info(f"Video described successfully: {media_file.filename} ({processing_time:.2f}s)")
            else:
                self.logger.warning(f"Video description failed: {media_file.filename} - {response.error}")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing video {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return GeminiResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def _process_small_image(self, media_file: MediaFile, prompt: str) -> GeminiResponse:
        """Process small images using inline data."""
        try:
            # Read and encode image
            with open(media_file.filepath, 'rb') as f:
                image_data = f.read()
            
            # Create model instance
            model = genai.GenerativeModel(self.model_name)
            
            # Create content with image data
            response = model.generate_content([
                prompt,
                {
                    'mime_type': self._get_mime_type(media_file.extension),
                    'data': image_data
                }
            ])
            
            if response and response.text:
                return GeminiResponse(
                    success=True,
                    description=response.text.strip(),
                    tokens_used=getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
                )
            else:
                return GeminiResponse(
                    success=False,
                    error="Empty response from Gemini API"
                )
                
        except Exception as e:
            return GeminiResponse(
                success=False,
                error=f"API call failed: {str(e)}"
            )
    
    def _process_large_image(self, media_file: MediaFile, prompt: str) -> GeminiResponse:
        """Process large images using inline processing (fallback for older genai versions)."""
        try:
            # For older versions without upload_file, use inline processing
            # but warn about potential size limits
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > 15:  # More restrictive for large files without upload API
                return GeminiResponse(
                    success=False,
                    error=f"Image too large for inline processing: {size_mb:.1f}MB (max: 15MB)"
                )
            
            # Read and encode image
            with open(media_file.filepath, 'rb') as f:
                image_data = f.read()
            
            # Create model instance
            model = genai.GenerativeModel(self.model_name)
            
            # Create content with image data
            response = model.generate_content([
                prompt,
                {
                    'mime_type': self._get_mime_type(media_file.extension),
                    'data': image_data
                }
            ])
            
            if response and response.text:
                return GeminiResponse(
                    success=True,
                    description=response.text.strip(),
                    tokens_used=getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
                )
            else:
                return GeminiResponse(
                    success=False,
                    error="Empty response from Gemini API"
                )
                
        except Exception as e:
            return GeminiResponse(
                success=False,
                error=f"Inline processing failed: {str(e)}"
            )
    
    def _process_video_with_files_api(self, media_file: MediaFile) -> GeminiResponse:
        """
        Process video using inline processing (for compatibility with older genai versions).
        
        Args:
            media_file: MediaFile object for the video
            
        Returns:
            GeminiResponse with video description
        """
        try:
            self.logger.debug(f"Processing video with inline method: {media_file.filename}")
            
            # Check file size for inline processing (be more restrictive)
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > 10:  # Limit to 10MB for inline video processing
                return GeminiResponse(
                    success=False,
                    error=f"Video too large for inline processing: {size_mb:.1f}MB (max: 10MB)"
                )
            
            # Read video file
            with open(media_file.filepath, 'rb') as f:
                video_data = f.read()
            
            # Create model instance
            model = genai.GenerativeModel(self.model_name)
            
            # Create content with video data
            prompt = "Describe this video in detail, focusing on the main subjects, actions, setting, and any notable features or events."
            response = model.generate_content([
                prompt,
                {
                    'mime_type': self._get_mime_type(media_file.extension),
                    'data': video_data
                }
            ])
            
            if response and response.text:
                return GeminiResponse(
                    success=True,
                    description=response.text.strip(),
                    tokens_used=getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
                )
            else:
                return GeminiResponse(
                    success=False,
                    error="Empty response from Gemini API"
                )
                
        except Exception as e:
            error_msg = f"Inline video processing failed: {str(e)}"
            self.logger.error(f"Video processing error for {media_file.filename}: {error_msg}")
            return GeminiResponse(
                success=False,
                error=error_msg
            )
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.3gp': 'video/3gpp',
            '.webm': 'video/webm'
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')
    
    def test_connection(self) -> bool:
        """Test if the Gemini API connection is working."""
        try:
            # Simple test with text-only request
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content("Say 'Hello' if you can receive this message.")
            return bool(response and response.text and 'hello' in response.text.lower())
        except Exception as e:
            self.logger.error(f"Gemini connection test failed: {e}")
            return False 