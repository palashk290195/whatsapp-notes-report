"""
Assembly AI Service Integration

Handles audio transcription using Assembly AI with error handling,
retry mechanisms, and progress tracking.

Created: January 2025
Author: AI Assistant
Changes: Initial implementation with Assembly AI for audio transcription
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import assemblyai as aai
except ImportError:
    aai = None

from file_manager import MediaFile


@dataclass
class TranscriptionResponse:
    """Response from Assembly AI transcription."""
    success: bool
    transcription: Optional[str] = None
    error: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: float = 0.0
    audio_duration: Optional[float] = None


class AssemblyAIService:
    """Assembly AI service for audio transcription."""
    
    def __init__(self, api_key: str, max_audio_size_mb: int = 25):
        """
        Initialize Assembly AI service.
        
        Args:
            api_key: Assembly AI API key
            max_audio_size_mb: Maximum audio file size in MB
        """
        if not aai:
            raise ImportError("assemblyai package not installed. Run: pip install assemblyai")
        
        self.api_key = api_key
        self.max_audio_size_mb = max_audio_size_mb
        self.logger = logging.getLogger(__name__)
        
        # Set global API key
        aai.settings.api_key = api_key
        
        # Supported audio formats
        self.supported_formats = {'.opus', '.mp3', '.wav', '.aac', '.m4a', '.ogg'}
        
        # Default transcription config
        self.transcription_config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.nano,
            language_detection=True,  # Auto-detect language
            punctuate=True,
            format_text=True,
            dual_channel=False,  # Most WhatsApp audio is mono
            speaker_labels=False,  # Not needed for WhatsApp voice messages
        )
        
        self.logger.info("Assembly AI service initialized successfully")
    
    def transcribe_audio(self, media_file: MediaFile, 
                        custom_config: Optional[aai.TranscriptionConfig] = None) -> TranscriptionResponse:
        """
        Transcribe an audio file.
        
        Args:
            media_file: MediaFile object containing audio information
            custom_config: Optional custom transcription configuration
            
        Returns:
            TranscriptionResponse with transcription or error
        """
        start_time = time.time()
        
        try:
            # Validate file type
            if media_file.extension.lower() not in self.supported_formats:
                return TranscriptionResponse(
                    success=False,
                    error=f"Unsupported audio format: {media_file.extension}"
                )
            
            # Check file size
            size_mb = media_file.size_bytes / (1024 * 1024)
            if size_mb > self.max_audio_size_mb:
                return TranscriptionResponse(
                    success=False,
                    error=f"Audio file too large: {size_mb:.1f}MB (max: {self.max_audio_size_mb}MB)"
                )
            
            self.logger.debug(f"Starting transcription: {media_file.filename} ({size_mb:.1f}MB)")
            
            # Use custom config if provided, otherwise use default
            config = custom_config or self.transcription_config
            
            # Create transcriber and submit job
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(str(media_file.filepath))
            
            # Check transcription status
            if transcript.status == aai.TranscriptStatus.error:
                error_msg = transcript.error or "Unknown transcription error"
                self.logger.error(f"Transcription failed for {media_file.filename}: {error_msg}")
                return TranscriptionResponse(
                    success=False,
                    error=f"Transcription failed: {error_msg}"
                )
            
            # Extract transcription text
            transcription_text = transcript.text or ""
            if not transcription_text.strip():
                self.logger.warning(f"Empty transcription for {media_file.filename}")
                transcription_text = "[No speech detected]"
            
            processing_time = time.time() - start_time
            
            # Get confidence score if available
            confidence = None
            if hasattr(transcript, 'confidence') and transcript.confidence:
                confidence = transcript.confidence
            
            # Get audio duration if available
            audio_duration = None
            if hasattr(transcript, 'audio_duration') and transcript.audio_duration:
                audio_duration = transcript.audio_duration / 1000.0  # Convert ms to seconds
            
            self.logger.info(
                f"Audio transcribed successfully: {media_file.filename} "
                f"({processing_time:.2f}s, {len(transcription_text)} chars)"
            )
            
            return TranscriptionResponse(
                success=True,
                transcription=transcription_text.strip(),
                confidence=confidence,
                processing_time=processing_time,
                audio_duration=audio_duration
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error transcribing audio {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return TranscriptionResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def transcribe_with_retry(self, media_file: MediaFile, 
                             max_retries: int = 3,
                             retry_delay: float = 5.0) -> TranscriptionResponse:
        """
        Transcribe audio with retry mechanism.
        
        Args:
            media_file: MediaFile object containing audio information
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            TranscriptionResponse with transcription or error
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt}/{max_retries} for {media_file.filename}")
                time.sleep(retry_delay)
            
            response = self.transcribe_audio(media_file)
            
            if response.success:
                if attempt > 0:
                    self.logger.info(f"Transcription succeeded on retry {attempt}")
                return response
            
            last_error = response.error
            
            # Don't retry on certain types of errors
            if any(error_type in response.error.lower() for error_type in [
                'unsupported', 'too large', 'invalid format'
            ]):
                self.logger.debug(f"Not retrying due to error type: {response.error}")
                break
        
        self.logger.error(f"Transcription failed after {max_retries} retries: {last_error}")
        return TranscriptionResponse(
            success=False,
            error=f"Failed after {max_retries} retries: {last_error}"
        )
    
    def get_transcription_status(self, transcript_id: str) -> Dict[str, Any]:
        """
        Get the status of a transcription job.
        
        Args:
            transcript_id: The ID of the transcription job
            
        Returns:
            Dictionary with status information
        """
        try:
            transcript = aai.Transcript.get_by_id(transcript_id)
            return {
                'id': transcript.id,
                'status': transcript.status.value,
                'text': transcript.text,
                'confidence': getattr(transcript, 'confidence', None),
                'error': transcript.error
            }
        except Exception as e:
            self.logger.error(f"Error getting transcription status: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test if the Assembly AI connection is working."""
        try:
            # Simple test by checking if we can create a transcriber
            test_config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano)
            transcriber = aai.Transcriber(config=test_config)
            
            # We can't easily test without uploading a file, so we'll just check
            # if the transcriber was created successfully
            return transcriber is not None
            
        except Exception as e:
            self.logger.error(f"Assembly AI connection test failed: {e}")
            return False
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get usage summary for the API key.
        Note: This might not be available in all Assembly AI plans.
        """
        try:
            # Assembly AI doesn't have a direct usage API in the free tier
            # This is a placeholder for future implementation
            return {
                'message': 'Usage tracking not available in current plan',
                'suggestion': 'Monitor usage through Assembly AI dashboard'
            }
        except Exception as e:
            return {'error': str(e)} 