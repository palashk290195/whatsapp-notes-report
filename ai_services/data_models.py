"""
AI Services Data Models

Data structures and classes specifically for AI service operations.

Created: December 2024
Author: AI Assistant
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ProcessingResult:
    """Result from processing a media file."""
    success: bool
    description: str
    service_used: str
    processing_time: float
    error: str = ""
    tokens_used: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MediaFile:
    """Represents a media file in the chat export."""
    filename: str
    filepath: Path
    file_type: str  # 'image', 'video', 'audio', 'document'
    size_bytes: int
    extension: str
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size_bytes / (1024 * 1024) 