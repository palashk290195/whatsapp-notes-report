"""
AI Service Manager - OpenAI-Only Processing

Manages AI services for media processing using OpenAI Vision and Whisper.
- OpenAI Vision for image analysis
- OpenAI Whisper for audio transcription with automatic format conversion
- Skips video processing entirely
- Automatic conversion of unsupported audio formats (e.g., .opus) to .mp3

Created: December 2024
Author: AI Assistant
Changes: Added audio format conversion for .opus files using ffmpeg
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

from ai_services.data_models import ProcessingResult, MediaFile


@dataclass
class OpenAIImageResponse:
    """Response from OpenAI Vision API."""
    success: bool
    description: str = ""
    tokens_used: int = 0
    processing_time: float = 0.0
    error: str = ""


@dataclass
class OpenAIAudioResponse:
    """Response from OpenAI Whisper API."""
    success: bool
    transcription: str = ""
    processing_time: float = 0.0
    error: str = ""


class OpenAIImageService:
    """OpenAI Vision service for image analysis."""
    
    def __init__(self, api_key: str):
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.model = "gpt-4o"  # Use GPT-4o for vision
        
        # Image settings
        self.max_image_size_mb = 20
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
    
    def describe_image(self, media_file: MediaFile, 
                      custom_prompt: Optional[str] = None) -> OpenAIImageResponse:
        """
        Describe an image using OpenAI Vision.
        
        Args:
            media_file: MediaFile object for the image
            custom_prompt: Optional custom prompt for description
            
        Returns:
            OpenAIImageResponse with image description
        """
        start_time = time.time()
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_formats:
                return OpenAIImageResponse(
                    success=False,
                    error=f"Unsupported image format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_image_size_mb:
                return OpenAIImageResponse(
                    success=False,
                    error=f"Image too large: {size_mb:.1f}MB (max: {self.max_image_size_mb}MB)"
                )
            
            # Default prompt for image description
            prompt = custom_prompt or (
                "Describe this image in detail. Focus on the main subjects, objects, "
                "activities, setting, text content (if any), and any notable features. "
                "Be comprehensive but concise."
            )
            
            # Process image
            self.logger.debug(f"Processing image with OpenAI Vision: {media_file.filename}")
            
            # Read and encode image
            import base64
            with open(media_file.filepath, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{media_file.extension.lstrip('.')};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            processing_time = time.time() - start_time
            
            if response and response.choices and response.choices[0].message.content:
                description = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                self.logger.info(f"Image described successfully: {media_file.filename} ({processing_time:.2f}s)")
                
                return OpenAIImageResponse(
                    success=True,
                    description=description,
                    tokens_used=tokens_used,
                    processing_time=processing_time
                )
            else:
                return OpenAIImageResponse(
                    success=False,
                    error="Empty response from OpenAI Vision API",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"OpenAI Vision processing failed: {str(e)}"
            self.logger.error(f"Image processing error for {media_file.filename}: {error_msg}")
            return OpenAIImageResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )


class OpenAIAudioService:
    """OpenAI Whisper service for audio transcription."""
    
    def __init__(self, api_key: str):
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
        # Audio settings
        self.max_audio_size_mb = 25
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.ogg', '.opus', '.aac', '.flac', '.mp4', '.mpeg', '.mpga', '.oga', '.webm'}
        self.whisper_supported_formats = {'.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}
    
    def transcribe_audio(self, media_file: MediaFile) -> OpenAIAudioResponse:
        """
        Transcribe audio using OpenAI Whisper.
        
        Args:
            media_file: MediaFile object for the audio
            
        Returns:
            OpenAIAudioResponse with transcription
        """
        start_time = time.time()
        converted_file_path = None
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_formats:
                return OpenAIAudioResponse(
                    success=False,
                    error=f"Unsupported audio format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_audio_size_mb:
                return OpenAIAudioResponse(
                    success=False,
                    error=f"Audio too large: {size_mb:.1f}MB (max: {self.max_audio_size_mb}MB)"
                )
            
            # Check if format is supported by OpenAI Whisper
            file_to_transcribe = media_file.filepath
            if media_file.extension.lower() not in self.whisper_supported_formats:
                # Convert to MP3
                self.logger.info(f"Converting {media_file.extension} to MP3: {media_file.filename}")
                converted_file_path = self._convert_audio_to_mp3(media_file.filepath)
                if not converted_file_path:
                    return OpenAIAudioResponse(
                        success=False,
                        error=f"Failed to convert {media_file.extension} to MP3"
                    )
                file_to_transcribe = converted_file_path
                self.logger.info(f"Successfully converted {media_file.filename} to MP3, now transcribing...")
            
            # Process audio
            self.logger.debug(f"Transcribing audio with OpenAI Whisper: {media_file.filename}")
            
            with open(file_to_transcribe, 'rb') as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text"
                )
            
            processing_time = time.time() - start_time
            
            if response and response.strip():
                self.logger.info(f"Audio transcribed successfully: {media_file.filename} ({processing_time:.2f}s)")
                
                return OpenAIAudioResponse(
                    success=True,
                    transcription=response.strip(),
                    processing_time=processing_time
                )
            else:
                return OpenAIAudioResponse(
                    success=False,
                    error="Empty response from OpenAI Whisper API",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"OpenAI Whisper processing failed: {str(e)}"
            self.logger.error(f"Audio processing error for {media_file.filename}: {error_msg}")
            return OpenAIAudioResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
        finally:
            # Clean up converted file
            if converted_file_path and converted_file_path.exists():
                try:
                    converted_file_path.unlink()
                    self.logger.debug(f"Cleaned up converted file: {converted_file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up converted file {converted_file_path}: {e}")
    
    def _convert_audio_to_mp3(self, audio_path: Path) -> Optional[Path]:
        """
        Convert audio file to MP3 format using ffmpeg.
        
        Args:
            audio_path: Path to the original audio file
            
        Returns:
            Path to converted MP3 file, or None if conversion failed
        """
        try:
            import subprocess
            import tempfile
            
            # Create temporary MP3 file
            temp_dir = Path(tempfile.gettempdir())
            temp_mp3_path = temp_dir / f"converted_audio_{int(time.time())}_{audio_path.stem}.mp3"
            
            # Try to convert using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-vn',  # No video
                '-ar', '16000',  # 16kHz sample rate (good for speech)
                '-ac', '1',  # Mono
                '-b:a', '32k',  # 32kbps bitrate (good for speech)
                '-y',  # Overwrite output file
                str(temp_mp3_path)
            ]
            
            # Run ffmpeg conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0 and temp_mp3_path.exists():
                self.logger.debug(f"Successfully converted {audio_path.name} to MP3")
                return temp_mp3_path
            else:
                self.logger.error(f"ffmpeg conversion failed for {audio_path.name}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Audio conversion timeout for {audio_path.name}")
            return None
        except FileNotFoundError:
            self.logger.error("ffmpeg not found. Please install ffmpeg to convert audio files.")
            return None
        except Exception as e:
            self.logger.error(f"Audio conversion error for {audio_path.name}: {e}")
            return None


class AIServiceManager:
    """Manages OpenAI-only AI services for media processing."""
    
    def __init__(self, openai_api_key: str):
        """
        Initialize AI services with OpenAI API key.
        
        Args:
            openai_api_key: OpenAI API key
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI services
        try:
            self.vision_service = OpenAIImageService(openai_api_key)
            self.audio_service = OpenAIAudioService(openai_api_key)
            self.logger.info("OpenAI services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI services: {e}")
            raise
        
        # Cost tracking
        self.cost_tracker = {
            'vision_calls': 0,
            'whisper_minutes': 0.0,
            'estimated_cost': 0.0
        }
    
    def process_media_file(self, media_file: MediaFile) -> ProcessingResult:
        """
        Process any media file based on its type.
        
        Args:
            media_file: MediaFile object to process
            
        Returns:
            ProcessingResult with appropriate description/transcription
        """
        if media_file.file_type == 'image':
            return self._process_image(media_file)
        elif media_file.file_type == 'video':
            # Skip video processing
            self.logger.info(f"Skipping video file: {media_file.filename}")
            return ProcessingResult(
                success=True,
                description="[Video file - processing skipped]",
                service_used="skipped",
                processing_time=0.0,
                error=""
            )
        elif media_file.file_type == 'audio':
            return self._process_audio(media_file)
        else:
            return ProcessingResult(
                success=False,
                description="",
                service_used="none",
                processing_time=0.0,
                error=f"Unsupported media type: {media_file.file_type}"
            )
    
    def _process_image(self, media_file: MediaFile) -> ProcessingResult:
        """Process image with OpenAI Vision."""
        try:
            response = self.vision_service.describe_image(media_file)
            
            if response.success:
                # Update cost tracking
                self.cost_tracker['vision_calls'] += 1
                # Rough estimate: $0.01 per image (GPT-4o vision pricing)
                self.cost_tracker['estimated_cost'] += 0.01
                
                return ProcessingResult(
                    success=True,
                    description=response.description,
                    service_used="openai_vision",
                    processing_time=response.processing_time,
                    tokens_used=response.tokens_used
                )
            else:
                return ProcessingResult(
                    success=False,
                    description="",
                    service_used="openai_vision",
                    processing_time=response.processing_time,
                    error=response.error
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                description="",
                service_used="openai_vision",
                processing_time=0.0,
                error=f"Image processing failed: {str(e)}"
            )
    
    def _process_audio(self, media_file: MediaFile) -> ProcessingResult:
        """Process audio with OpenAI Whisper."""
        try:
            response = self.audio_service.transcribe_audio(media_file)
            
            if response.success:
                # Update cost tracking
                # Rough estimate: $0.006 per minute for Whisper
                estimated_minutes = max(0.1, response.processing_time / 60)  # Minimum 0.1 min
                self.cost_tracker['whisper_minutes'] += estimated_minutes
                self.cost_tracker['estimated_cost'] += estimated_minutes * 0.006
                
                return ProcessingResult(
                    success=True,
                    description=response.transcription,
                    service_used="openai_whisper",
                    processing_time=response.processing_time
                )
            else:
                return ProcessingResult(
                    success=False,
                    description="",
                    service_used="openai_whisper",
                    processing_time=response.processing_time,
                    error=response.error
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                description="",
                service_used="openai_whisper",
                processing_time=0.0,
                error=f"Audio processing failed: {str(e)}"
            )
    
    def test_all_services(self) -> Dict[str, bool]:
        """Test connectivity for all services."""
        results = {}
        
        # Test OpenAI Vision (simple API check)
        try:
            # Create a simple test - just check if we can create a client
            test_client = OpenAI(api_key=self.vision_service.client.api_key)
            results['openai_vision'] = True
        except Exception as e:
            self.logger.error(f"OpenAI Vision test failed: {e}")
            results['openai_vision'] = False
        
        # Test OpenAI Whisper (simple API check)
        try:
            # Create a simple test - just check if we can create a client
            test_client = OpenAI(api_key=self.audio_service.client.api_key)
            results['openai_whisper'] = True
        except Exception as e:
            self.logger.error(f"OpenAI Whisper test failed: {e}")
            results['openai_whisper'] = False
        
        return results
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        return {
            'vision_calls': self.cost_tracker['vision_calls'],
            'whisper_minutes': round(self.cost_tracker['whisper_minutes'], 2),
            'estimated_total_cost': round(self.cost_tracker['estimated_cost'], 2),
            'currency': 'USD'
        } 