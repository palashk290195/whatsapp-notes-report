"""
AI Services Package - OpenAI Only

Simplified AI services package that provides OpenAI Vision and Whisper services
for WhatsApp chat media processing.

Features:
- OpenAI Vision for image analysis
- OpenAI Whisper for audio transcription  
- Skips video processing entirely
- Simplified service management

Created: January 2025
Author: AI Assistant
Changes: Simplified to OpenAI-only processing
"""

from .service_manager import AIServiceManager
from .data_models import ProcessingResult, MediaFile

__all__ = [
    'AIServiceManager',
    'ProcessingResult', 
    'MediaFile'
]

__version__ = '1.0.0' 