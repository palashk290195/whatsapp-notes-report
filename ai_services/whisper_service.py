"""
OpenAI Whisper Service Integration

Handles audio transcription using OpenAI Whisper API as a fallback option
for Assembly AI with error handling and retry mechanisms.

Created: January 2025
Author: AI Assistant
Changes: Initial implementation with OpenAI Whisper API for audio transcription
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None

from file_manager import MediaFile


@dataclass
class WhisperResponse:
    """Response from OpenAI Whisper API."""
    success: bool
    transcription: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = None
    processing_time: float = 0.0
    audio_duration: Optional[float] = None


class OpenAIWhisperService:
    """OpenAI Whisper service for audio transcription."""
    
    def __init__(self, api_key: str, max_audio_size_mb: int = 25):
        """
        Initialize OpenAI Whisper service.
        
        Args:
            api_key: OpenAI API key
            max_audio_size_mb: Maximum audio file size in MB (OpenAI limit is 25MB)
        """
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.api_key = api_key
        self.max_audio_size_mb = min(max_audio_size_mb, 25)  # OpenAI hard limit
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=api_key)
            self.logger.info("OpenAI Whisper client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        # Supported audio formats (OpenAI Whisper supports)
        self.supported_formats = {
            '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'
        }
        
        # Note: .opus files will need to be converted first
        self.needs_conversion = {'.opus', '.ogg', '.aac'}
        
        # Default model
        self.model = "whisper-1"
    
    def transcribe_audio(self, media_file: MediaFile, 
                        language: Optional[str] = None,
                        prompt: Optional[str] = None) -> WhisperResponse:
        """
        Transcribe an audio file using OpenAI Whisper.
        
        Args:
            media_file: MediaFile object containing audio information
            language: Optional language code (e.g., 'en', 'es', 'fr')
            prompt: Optional prompt to guide transcription
            
        Returns:
            WhisperResponse with transcription or error
        """
        start_time = time.time()
        
        try:
            # Validate file type
            file_ext = media_file.extension.lower()
            if file_ext not in self.supported_formats and file_ext not in self.needs_conversion:
                return WhisperResponse(
                    success=False,
                    error=f"Unsupported audio format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_audio_size_mb:
                return WhisperResponse(
                    success=False,
                    error=f"Audio file too large: {size_mb:.1f}MB (max: {self.max_audio_size_mb}MB)"
                )
            
            self.logger.debug(f"Starting Whisper transcription: {media_file.filename} ({size_mb:.1f}MB)")
            
            # Handle file conversion if needed
            audio_file_path = media_file.filepath
            if file_ext in self.needs_conversion:
                converted_path = self._convert_audio_format(media_file)
                if not converted_path:
                    return WhisperResponse(
                        success=False,
                        error=f"Failed to convert audio format from {file_ext}"
                    )
                audio_file_path = converted_path
            
            # Prepare transcription parameters
            transcription_params = {
                "model": self.model,
            }
            
            if language:
                transcription_params["language"] = language
            
            if prompt:
                transcription_params["prompt"] = prompt
            
            # Open and transcribe audio file
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **transcription_params
                )
            
            # Clean up converted file if it was created
            if audio_file_path != media_file.filepath:
                try:
                    audio_file_path.unlink()
                except:
                    pass  # Non-critical error
            
            # Extract transcription text
            transcription_text = transcript.text or ""
            if not transcription_text.strip():
                self.logger.warning(f"Empty transcription for {media_file.filename}")
                transcription_text = "[No speech detected]"
            
            processing_time = time.time() - start_time
            
            # For basic response format, we don't get language/duration info
            self.logger.info(
                f"Audio transcribed successfully with Whisper: {media_file.filename} "
                f"({processing_time:.2f}s, {len(transcription_text)} chars)"
            )
            
            return WhisperResponse(
                success=True,
                transcription=transcription_text.strip(),
                language=language,  # Use provided language since we can't detect it in basic mode
                processing_time=processing_time,
                audio_duration=None  # Not available in basic response format
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error transcribing audio with Whisper {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return WhisperResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def transcribe_with_retry(self, media_file: MediaFile, 
                             max_retries: int = 2,
                             retry_delay: float = 3.0,
                             language: Optional[str] = None) -> WhisperResponse:
        """
        Transcribe audio with retry mechanism.
        
        Args:
            media_file: MediaFile object containing audio information
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            language: Optional language code
            
        Returns:
            WhisperResponse with transcription or error
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(f"Whisper retry attempt {attempt}/{max_retries} for {media_file.filename}")
                time.sleep(retry_delay)
            
            response = self.transcribe_audio(media_file, language=language)
            
            if response.success:
                if attempt > 0:
                    self.logger.info(f"Whisper transcription succeeded on retry {attempt}")
                return response
            
            last_error = response.error
            
            # Don't retry on certain types of errors
            if any(error_type in response.error.lower() for error_type in [
                'unsupported', 'too large', 'invalid format', 'file format'
            ]):
                self.logger.debug(f"Not retrying Whisper due to error type: {response.error}")
                break
        
        self.logger.error(f"Whisper transcription failed after {max_retries} retries: {last_error}")
        return WhisperResponse(
            success=False,
            error=f"Failed after {max_retries} retries: {last_error}"
        )
    
    def _convert_audio_format(self, media_file: MediaFile) -> Optional[Path]:
        """
        Convert audio file to a format supported by Whisper.
        
        Args:
            media_file: MediaFile object to convert
            
        Returns:
            Path to converted file or None if conversion failed
        """
        try:
            # Import pydub for audio conversion
            try:
                from pydub import AudioSegment
            except ImportError:
                self.logger.error("pydub not installed. Cannot convert audio formats.")
                return None
            
            # Load audio file
            if media_file.extension.lower() == '.opus':
                audio = AudioSegment.from_file(media_file.filepath, format="opus")
            elif media_file.extension.lower() == '.ogg':
                audio = AudioSegment.from_ogg(media_file.filepath)
            elif media_file.extension.lower() == '.aac':
                audio = AudioSegment.from_file(media_file.filepath, format="aac")
            else:
                self.logger.error(f"Unknown conversion format: {media_file.extension}")
                return None
            
            # Convert to MP3 (widely supported)
            output_path = media_file.filepath.parent / f"{media_file.filepath.stem}_converted.mp3"
            audio.export(output_path, format="mp3")
            
            self.logger.debug(f"Converted {media_file.filename} to MP3 for Whisper")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to convert audio file {media_file.filename}: {e}")
            return None
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages for Whisper.
        
        Returns:
            List of supported language codes
        """
        # Common languages supported by Whisper
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
            'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'he',
            'th', 'vi', 'id', 'ms', 'tl', 'uk', 'bg', 'hr', 'cs', 'et',
            'lv', 'lt', 'mt', 'ro', 'sk', 'sl', 'el', 'hu', 'is', 'ga',
            'cy', 'eu', 'ca', 'gl', 'ast', 'oc', 'br', 'fo', 'hy', 'az',
            'ka', 'be', 'kk', 'ky', 'uz', 'tg', 'mn', 'my', 'si', 'km',
            'lo', 'bn', 'as', 'gu', 'kn', 'ml', 'mr', 'ne', 'or', 'pa',
            'ta', 'te', 'ur', 'ps', 'fa', 'dv', 'so', 'sw', 'am', 'yo',
            'ig', 'zu', 'af', 'sq', 'mk', 'mg', 'mt', 'mi', 'haw', 'ln',
            'yo', 'sn', 'ny', 'ha', 'xh', 'zu', 'st', 'tn', 'ts', 've'
        ]
    
    def test_connection(self) -> bool:
        """Test if the OpenAI API connection is working."""
        try:
            # Simple test by trying to access models
            models = self.client.models.list()
            return any(model.id == "whisper-1" for model in models.data)
        except Exception as e:
            self.logger.error(f"OpenAI Whisper connection test failed: {e}")
            return False
    
    def estimate_cost(self, audio_duration_minutes: float) -> float:
        """
        Estimate the cost for transcribing audio.
        
        Args:
            audio_duration_minutes: Duration of audio in minutes
            
        Returns:
            Estimated cost in USD
        """
        # OpenAI Whisper pricing: $0.006 per minute
        cost_per_minute = 0.006
        return audio_duration_minutes * cost_per_minute 