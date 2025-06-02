"""
WhatsApp Chat Parser Module

Parses WhatsApp chat export files and extracts structured message data including
media file references for further processing.

Created: January 2025
Author: AI Assistant
Changes: Initial implementation with regex patterns for WhatsApp chat format parsing
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Types of messages in WhatsApp chat."""
    TEXT = "text"
    MEDIA = "media"
    SYSTEM = "system"
    DELETED = "deleted"
    URL = "url"


@dataclass
class ParsedMessage:
    """Structured representation of a parsed WhatsApp message."""
    timestamp: datetime
    sender: Optional[str]
    content: str
    message_type: MessageType
    media_filename: Optional[str] = None
    raw_line: str = ""
    line_number: int = 0


class WhatsAppChatParser:
    """Parser for WhatsApp chat export files."""
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        self.logger = logging.getLogger(__name__)
        
        # WhatsApp message patterns
        # Format: DD/MM/YYYY, HH:MM - Sender Name: Message content
        self.message_pattern = re.compile(
            r'^(\d{1,2}/\d{1,2}/\d{4}),?\s+(\d{1,2}:\d{2})\s*-\s*([^:]+?):\s*(.*)$'
        )
        
        # Media file patterns
        self.media_patterns = {
            'file_attached': re.compile(r'(.+?)\s*\(file attached\)'),
            'omitted': re.compile(r'<Media omitted>'),
            'image': re.compile(r'\[?(?:Photo|Image)\]?'),
            'video': re.compile(r'\[?Video\]?'),
            'audio': re.compile(r'\[?Audio\]?'),
            'document': re.compile(r'\[?Document\]?'),
        }
        
        # System message patterns
        self.system_patterns = [
            re.compile(r'.+\s+(?:added|removed|left|joined|created|changed)'),
            re.compile(r'Messages and calls are end-to-end encrypted'),
            re.compile(r'Only messages that mention'),
            re.compile(r'You added|You removed|You left|You created'),
            re.compile(r'Security code changed'),
            re.compile(r'This message was deleted'),
        ]
        
        # URL pattern
        self.url_pattern = re.compile(r'https?://[^\s]+')
        
        # Deleted message pattern
        self.deleted_pattern = re.compile(r'This message was deleted|You deleted this message')
    
    def parse_chat_file(self, file_path: Path) -> List[ParsedMessage]:
        """
        Parse a WhatsApp chat export file.
        
        Args:
            file_path: Path to the chat .txt file
            
        Returns:
            List of ParsedMessage objects
        """
        self.logger.info(f"Parsing chat file: {file_path}")
        
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Basic parsing for now
                    match = self.message_pattern.match(line)
                    if match:
                        date_str, time_str, sender, content = match.groups()
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                        except ValueError:
                            timestamp = datetime.now()
                        
                        # Check for media files
                        media_filename = None
                        message_type = MessageType.TEXT
                        
                        if '(file attached)' in content:
                            media_match = re.search(r'(.+?)\s*\(file attached\)', content)
                            if media_match:
                                media_filename = media_match.group(1).strip()
                                message_type = MessageType.MEDIA
                        
                        messages.append(ParsedMessage(
                            timestamp=timestamp,
                            sender=sender.strip(),
                            content=content.strip(),
                            message_type=message_type,
                            media_filename=media_filename,
                            raw_line=line,
                            line_number=line_number
                        ))
        
        except Exception as e:
            self.logger.error(f"Error parsing chat file {file_path}: {e}")
            raise
        
        self.logger.info(f"Parsed {len(messages)} messages from chat file")
        return messages
    
    def get_media_references(self, messages: List[ParsedMessage]) -> List[str]:
        """Extract all media file references from parsed messages."""
        media_files = []
        for msg in messages:
            if msg.media_filename:
                media_files.append(msg.media_filename)
        
        unique_files = list(set(media_files))
        self.logger.info(f"Found {len(unique_files)} unique media file references")
        return unique_files 