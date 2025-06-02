"""
File Manager Module for WhatsApp Chat Notes Processor

Handles file discovery, validation, and mapping of media files to chat references.

Created: January 2025
Author: AI Assistant
Changes: Initial implementation with folder scanning and file mapping functionality
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class MediaFile:
    """Represents a media file found in the WhatsApp export."""
    filename: str
    filepath: Path
    file_type: str  # 'image', 'video', 'audio', 'document'
    size_bytes: int
    extension: str


class FileManager:
    """Manages file discovery and mapping for WhatsApp exports."""
    
    def __init__(self, export_folder: Path):
        """
        Initialize file manager for a WhatsApp export folder.
        
        Args:
            export_folder: Path to the WhatsApp export folder
        """
        self.export_folder = export_folder
        self.logger = logging.getLogger(__name__)
        
        # Supported file extensions by type
        self.file_type_extensions = {
            'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
            'video': {'.mp4', '.mov', '.avi', '.mkv', '.3gp', '.webm'},
            'audio': {'.opus', '.mp3', '.wav', '.aac', '.m4a', '.ogg'},
            'document': {'.pdf', '.doc', '.docx', '.txt', '.zip', '.rar'}
        }
    
    def discover_files(self) -> Tuple[Path, Dict[str, MediaFile]]:
        """
        Discover the chat file and all media files in the export folder.
        
        Returns:
            Tuple of (chat_file_path, media_files_dict)
        """
        self.logger.info(f"Discovering files in: {self.export_folder}")
        
        chat_file = self._find_chat_file()
        media_files = self._find_media_files()
        
        self.logger.info(f"Found chat file: {chat_file.name}")
        self.logger.info(f"Found {len(media_files)} media files")
        
        return chat_file, media_files
    
    def _find_chat_file(self) -> Path:
        """
        Find the WhatsApp chat .txt file in the export folder.
        
        Returns:
            Path to the chat file
            
        Raises:
            FileNotFoundError: If no suitable chat file is found
        """
        # Look for .txt files
        txt_files = list(self.export_folder.glob("*.txt"))
        
        if not txt_files:
            raise FileNotFoundError(f"No .txt files found in {self.export_folder}")
        
        # Prefer files with "WhatsApp Chat" in the name
        for txt_file in txt_files:
            if "WhatsApp Chat" in txt_file.name or "chat" in txt_file.name.lower():
                self.logger.debug(f"Found WhatsApp chat file: {txt_file.name}")
                return txt_file
        
        # If no obvious chat file, check content of first .txt file
        for txt_file in txt_files:
            try:
                sample_content = txt_file.read_text(encoding='utf-8', errors='ignore')[:1000]
                # Check for WhatsApp patterns
                if any(pattern in sample_content for pattern in [
                    " - ", "(file attached)", "/2025,", "/2024,"
                ]):
                    self.logger.debug(f"Identified chat file by content: {txt_file.name}")
                    return txt_file
            except Exception as e:
                self.logger.warning(f"Could not read {txt_file}: {e}")
        
        # Last resort: return the first .txt file
        self.logger.warning(f"Using first .txt file as chat file: {txt_files[0].name}")
        return txt_files[0]
    
    def _find_media_files(self) -> Dict[str, MediaFile]:
        """
        Find all media files in the export folder.
        
        Returns:
            Dictionary mapping filename to MediaFile object
        """
        media_files = {}
        
        # Get all files in the folder (excluding the chat .txt file)
        for file_path in self.export_folder.iterdir():
            if file_path.is_file() and not file_path.name.endswith('.txt'):
                media_file = self._analyze_media_file(file_path)
                if media_file:
                    media_files[media_file.filename] = media_file
        
        self._log_media_statistics(media_files)
        return media_files
    
    def _analyze_media_file(self, file_path: Path) -> Optional[MediaFile]:
        """
        Analyze a file to determine if it's a supported media file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            MediaFile object if it's a supported media file, None otherwise
        """
        try:
            extension = file_path.suffix.lower()
            file_type = self._get_file_type(extension)
            
            if not file_type:
                return None
            
            # Get file size
            size_bytes = file_path.stat().st_size
            
            return MediaFile(
                filename=file_path.name,
                filepath=file_path,
                file_type=file_type,
                size_bytes=size_bytes,
                extension=extension
            )
        
        except Exception as e:
            self.logger.warning(f"Could not analyze file {file_path}: {e}")
            return None
    
    def _get_file_type(self, extension: str) -> Optional[str]:
        """
        Determine file type based on extension.
        
        Args:
            extension: File extension (including dot)
            
        Returns:
            File type string or None if not supported
        """
        for file_type, extensions in self.file_type_extensions.items():
            if extension in extensions:
                return file_type
        return None
    
    def _log_media_statistics(self, media_files: Dict[str, MediaFile]) -> None:
        """Log statistics about discovered media files."""
        if not media_files:
            self.logger.info("No media files found")
            return
        
        type_counts = {}
        total_size = 0
        
        for media_file in media_files.values():
            file_type = media_file.file_type
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
            total_size += media_file.size_bytes
        
        self.logger.info("Media file statistics:")
        for file_type, count in type_counts.items():
            self.logger.info(f"  {file_type.title()}s: {count}")
        
        total_size_mb = total_size / (1024 * 1024)
        self.logger.info(f"  Total size: {total_size_mb:.1f} MB")
    
    def map_references_to_files(self, media_references: List[str], 
                               media_files: Dict[str, MediaFile]) -> Dict[str, Optional[MediaFile]]:
        """
        Map media file references from chat to actual files.
        
        Args:
            media_references: List of media filenames referenced in chat
            media_files: Dictionary of discovered media files
            
        Returns:
            Dictionary mapping reference to MediaFile (or None if not found)
        """
        mapping = {}
        found_count = 0
        
        for reference in media_references:
            if reference in media_files:
                mapping[reference] = media_files[reference]
                found_count += 1
            else:
                mapping[reference] = None
                self.logger.warning(f"Media file not found: {reference}")
        
        self.logger.info(f"Mapped {found_count}/{len(media_references)} media references to files")
        
        if found_count < len(media_references):
            missing_count = len(media_references) - found_count
            self.logger.warning(f"{missing_count} media files are missing from the export folder")
        
        return mapping
    
    def validate_file_sizes(self, media_files: Dict[str, MediaFile], 
                           max_image_size_mb: int = 20, 
                           max_audio_size_mb: int = 25) -> Dict[str, bool]:
        """
        Validate that media files are within API size limits.
        
        Args:
            media_files: Dictionary of media files to validate
            max_image_size_mb: Maximum size for images/videos in MB
            max_audio_size_mb: Maximum size for audio files in MB
            
        Returns:
            Dictionary mapping filename to validation result (True/False)
        """
        validation_results = {}
        
        for filename, media_file in media_files.items():
            size_mb = media_file.size_bytes / (1024 * 1024)
            
            if media_file.file_type in ['image', 'video']:
                is_valid = size_mb <= max_image_size_mb
                if not is_valid:
                    self.logger.warning(f"{filename}: {size_mb:.1f}MB exceeds image/video limit ({max_image_size_mb}MB)")
            elif media_file.file_type == 'audio':
                is_valid = size_mb <= max_audio_size_mb
                if not is_valid:
                    self.logger.warning(f"{filename}: {size_mb:.1f}MB exceeds audio limit ({max_audio_size_mb}MB)")
            else:
                is_valid = True  # Documents are not processed by AI services
            
            validation_results[filename] = is_valid
        
        valid_count = sum(validation_results.values())
        self.logger.info(f"File size validation: {valid_count}/{len(validation_results)} files within limits")
        
        return validation_results 