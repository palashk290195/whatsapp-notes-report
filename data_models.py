"""
WhatsApp Chat Notes - Data Models

Shared data structures and classes for the WhatsApp chat processing system.
Contains processing statistics, results, and configuration models.

Created: December 2024
Author: AI Assistant
Changes: Added ProcessingStats and updated models for OpenAI-only processing
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class ProcessingStats:
    """Statistics for chat processing session."""
    total_messages: int = 0
    media_messages: int = 0
    processed_media: int = 0
    failed_media: int = 0
    processing_time: float = 0.0
    success_rate: float = 0.0
    estimated_cost: float = 0.0
    
    # Media type breakdown
    images_processed: int = 0
    audio_processed: int = 0
    
    # OpenAI service usage
    openai_vision_calls: int = 0
    openai_whisper_minutes: float = 0.0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)


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


@dataclass
class ConferenceMetrics:
    """Metrics for conference analysis."""
    total_attendees: int = 0
    total_sessions: int = 0
    key_topics: List[str] = field(default_factory=list)
    action_items: int = 0
    networking_connections: int = 0
    business_opportunities: int = 0


@dataclass
class AIServiceConfig:
    """Configuration for AI services."""
    openai_api_key: str
    max_image_size_mb: int = 20
    max_audio_size_mb: int = 25
    enable_caching: bool = True
    timeout_seconds: int = 30


@dataclass
class ExportSummary:
    """Summary of a processed chat export."""
    export_name: str
    processing_date: str
    stats: ProcessingStats
    output_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.stats.success_rate > 50 and len(self.errors) == 0 