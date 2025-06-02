"""
WhatsApp Chat Notes - Chat Processor

Core module for processing WhatsApp chat exports with OpenAI-powered media analysis.
Handles chat parsing, media file processing, and enhanced chat generation.

Features:
- WhatsApp chat parsing and message extraction
- OpenAI Vision for image analysis
- OpenAI Whisper for audio transcription
- Enhanced message generation with AI descriptions
- Comprehensive statistics and error tracking

Created: December 2024
Author: AI Assistant
Changes: Simplified to use OpenAI-only processing, skip videos
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from collections import defaultdict
from dataclasses import dataclass

from config import Config
from file_manager import FileManager, MediaFile
from ai_services.service_manager import AIServiceManager, ProcessingResult
from chat_parser import WhatsAppChatParser, ParsedMessage
from data_models import ProcessingStats


class ChatProcessor:
    """Main chat processing engine using OpenAI services."""
    
    def __init__(self, config: Config):
        """
        Initialize chat processor with OpenAI configuration.
        
        Args:
            config: Configuration object with OpenAI API key
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Validate OpenAI API key
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required for processing")
        
        # Initialize AI service manager with OpenAI
        try:
            self.ai_manager = AIServiceManager(config.openai_api_key)
            self.logger.info("OpenAI AI services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI services: {e}")
            raise
        
        # Initialize statistics tracking
        self.stats = ProcessingStats()
        
        # File tracking
        self.chat_file: Optional[Path] = None
        self.media_files: Dict[str, MediaFile] = {}
    
    def process_chat_export(self, input_folder: Path, output_folder: Path) -> bool:
        """
        Process a complete WhatsApp chat export.
        
        Args:
            input_folder: Path to folder containing WhatsApp export
            output_folder: Path for output files
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            start_time = time.time()
            self.logger.info(f"Starting chat processing: {input_folder}")
            
            # Create output folder
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Discover files
            if not self._discover_files(input_folder):
                return False
            
            # Step 2: Parse chat messages
            messages = self._parse_chat_file()
            if not messages:
                return False
            
            # Step 3: Process media files with AI
            enhanced_messages = self._process_media_messages(messages)
            
            # Step 4: Generate enhanced chat file
            output_file = self._generate_enhanced_chat(enhanced_messages, output_folder)
            
            # Step 5: Update final statistics
            self.stats.processing_time = time.time() - start_time
            self.stats.success_rate = (self.stats.processed_media / max(1, self.stats.media_messages)) * 100
            self.stats.estimated_cost = self.ai_manager.get_cost_summary()['estimated_total_cost']
            
            self.logger.info(f"Processing completed successfully in {self.stats.processing_time:.2f}s")
            self.logger.info(f"Enhanced chat saved: {output_file}")
            self._log_final_stats()
            
            return True
            
        except Exception as e:
            error_msg = f"Chat processing failed: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return False
    
    def _discover_files(self, input_folder: Path) -> bool:
        """Discover and validate chat and media files."""
        try:
            self.logger.info("Discovering files...")
            
            # Initialize file manager with input folder
            file_manager = FileManager(input_folder)
            
            # Find chat file and media files
            chat_file, media_files = file_manager.discover_files()
            
            if not chat_file:
                error_msg = f"No WhatsApp chat file found in {input_folder}"
                self.logger.error(error_msg)
                self.stats.errors.append(error_msg)
                return False
            
            self.chat_file = chat_file
            self.media_files = media_files
            
            self.logger.info(f"Found chat file: {chat_file.name}")
            self.logger.info(f"Found {len(media_files)} media files")
            
            # Log media type breakdown and skip videos
            media_types = defaultdict(int)
            for media_file in media_files.values():
                if media_file.file_type == 'video':
                    self.logger.info(f"Skipping video file: {media_file.filename}")
                    continue
                media_types[media_file.file_type] += 1
            
            for media_type, count in media_types.items():
                self.logger.info(f"  - {media_type}: {count} files")
            
            return True
            
        except Exception as e:
            error_msg = f"File discovery failed: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return False
    
    def _parse_chat_file(self) -> List[ParsedMessage]:
        """Parse the WhatsApp chat file."""
        try:
            self.logger.info("Parsing chat file...")
            
            parser = WhatsAppChatParser()
            messages = parser.parse_chat_file(self.chat_file)
            
            if not messages:
                error_msg = "No messages found in chat file"
                self.logger.error(error_msg)
                self.stats.errors.append(error_msg)
                return []
            
            # Update statistics
            self.stats.total_messages = len(messages)
            self.stats.media_messages = sum(1 for msg in messages if msg.media_filename)
            
            self.logger.info(f"Parsed {len(messages)} messages ({self.stats.media_messages} with media)")
            
            return messages
            
        except Exception as e:
            error_msg = f"Chat parsing failed: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return []
    
    def _process_media_messages(self, messages: List[ParsedMessage]) -> List[ParsedMessage]:
        """Process media messages with AI services."""
        self.logger.info("Processing media files with OpenAI services...")
        
        processed_messages = []
        media_count = 0
        total_media = self.stats.media_messages
        
        for i, message in enumerate(messages):
            if message.media_filename:
                media_count += 1
                
                # Emit progress update for current media file
                progress = 50 + int((media_count / total_media) * 25)  # 50-75% range for media processing
                status_message = f"Processing media {media_count}/{total_media}: {message.media_filename}"
                
                # Emit progress via logger if it has emit_progress method
                if hasattr(self.logger, 'emit_progress'):
                    self.logger.emit_progress(status_message, progress, "processing")
                else:
                    self.logger.info(status_message)
                
                # Find corresponding media file
                media_file = self._find_media_file(message.media_filename)
                
                if media_file:
                    # Skip videos
                    if media_file.file_type == 'video':
                        self.logger.info(f"Skipping video: {media_file.filename}")
                        if hasattr(self.logger, 'emit_progress'):
                            self.logger.emit_progress(f"Skipped video: {media_file.filename}", progress, "success")
                        
                        # Create message indicating video was skipped
                        enhanced_message = ParsedMessage(
                            timestamp=message.timestamp,
                            sender=message.sender,
                            content="[Video file - processing skipped]",
                            message_type=message.message_type,
                            media_filename=None
                        )
                        processed_messages.append(enhanced_message)
                        continue
                    
                    self.logger.debug(f"Processing media {media_count}/{total_media}: {media_file.filename}")
                    
                    # Process with AI
                    ai_result = self._process_media_file(media_file)
                    
                    # Emit result update
                    if ai_result.success:
                        result_message = f"✅ {media_file.filename}: {ai_result.service_used} ({ai_result.processing_time:.1f}s)"
                        if hasattr(self.logger, 'emit_progress'):
                            self.logger.emit_progress(result_message, progress, "success")
                        else:
                            self.logger.info(result_message)
                    else:
                        error_message = f"❌ {media_file.filename}: {ai_result.error}"
                        if hasattr(self.logger, 'emit_progress'):
                            self.logger.emit_progress(error_message, progress, "error")
                        else:
                            self.logger.warning(error_message)
                    
                    # Create enhanced message
                    enhanced_message = self._create_enhanced_message(message, ai_result)
                    processed_messages.append(enhanced_message)
                    
                    # Update statistics
                    if ai_result.success:
                        self.stats.processed_media += 1
                        self._update_media_stats(media_file, ai_result)
                    else:
                        self.stats.failed_media += 1
                        self.stats.errors.append(f"Failed to process {media_file.filename}: {ai_result.error}")
                else:
                    # Media file not found
                    error_message = f"Media file not found: {message.media_filename}"
                    self.logger.warning(error_message)
                    if hasattr(self.logger, 'emit_progress'):
                        self.logger.emit_progress(error_message, progress, "error")
                    
                    self.stats.failed_media += 1
                    self.stats.errors.append(f"Media file not found: {message.media_filename}")
                    processed_messages.append(message)  # Keep original message
            else:
                # Text message - keep as is
                processed_messages.append(message)
        
        # Final media processing update
        final_message = f"Media processing complete: {self.stats.processed_media} successful, {self.stats.failed_media} failed"
        if hasattr(self.logger, 'emit_progress'):
            self.logger.emit_progress(final_message, 75, "success")
        
        self.logger.info(final_message)
        return processed_messages
    
    def _find_media_file(self, filename: str) -> Optional[MediaFile]:
        """Find media file by filename."""
        return self.media_files.get(filename)
    
    def _process_media_file(self, media_file: MediaFile) -> ProcessingResult:
        """Process a single media file with AI services."""
        try:
            result = self.ai_manager.process_media_file(media_file)
            
            # Log result
            if result.success:
                self.logger.debug(f"✅ {media_file.filename}: {result.service_used} ({result.processing_time:.2f}s)")
            else:
                self.logger.warning(f"❌ {media_file.filename}: {result.error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing {media_file.filename}: {str(e)}"
            self.logger.error(error_msg)
            return ProcessingResult(
                success=False,
                description="",
                service_used="none",
                processing_time=0.0,
                error=error_msg
            )
    
    def _create_enhanced_message(self, original_message: ParsedMessage, ai_result: ProcessingResult) -> ParsedMessage:
        """Create enhanced message with AI description."""
        if ai_result.success and ai_result.description:
            # Determine description prefix based on media type
            media_file = self._find_media_file(original_message.media_filename)
            
            if media_file:
                if media_file.file_type == 'image':
                    enhanced_content = f"This is an image: {ai_result.description}"
                elif media_file.file_type == 'video':
                    enhanced_content = f"[Video file - processing skipped]"
                elif media_file.file_type == 'audio':
                    enhanced_content = f"Voice note: {ai_result.description}"
                else:
                    enhanced_content = f"Media file: {ai_result.description}"
            else:
                enhanced_content = f"Media: {ai_result.description}"
            
            # Create new message with enhanced content
            return ParsedMessage(
                timestamp=original_message.timestamp,
                sender=original_message.sender,
                content=enhanced_content,
                message_type=original_message.message_type,
                media_filename=None  # Remove media reference since we've described it
            )
        else:
            # Keep original message if AI processing failed
            return original_message
    
    def _update_media_stats(self, media_file: MediaFile, ai_result: ProcessingResult):
        """Update processing statistics for media."""
        # Count by media type
        if media_file.file_type == 'image':
            self.stats.images_processed += 1
        elif media_file.file_type == 'audio':
            self.stats.audio_processed += 1
        
        # Track AI service usage (OpenAI only)
        if 'openai_vision' in ai_result.service_used:
            self.stats.openai_vision_calls += 1
        elif 'openai_whisper' in ai_result.service_used:
            # Estimate duration (would need actual duration from AI result)
            self.stats.openai_whisper_minutes += 0.5  # Placeholder
    
    def _generate_enhanced_chat(self, messages: List[ParsedMessage], output_folder: Path) -> Path:
        """Generate enhanced chat file with AI descriptions."""
        try:
            self.logger.info("Generating enhanced chat file...")
            
            # Generate output filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = output_folder / f"enhanced_chat_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# Enhanced WhatsApp Chat Export\n")
                f.write(f"# Generated by WhatsApp Chat Notes Processor\n")
                f.write(f"# Processing completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total messages: {len(messages)}\n")
                f.write(f"# Media processed: {self.stats.processed_media}\n")
                f.write(f"# Processing time: {self.stats.processing_time:.2f}s\n\n")
                
                # Write messages
                for message in messages:
                    f.write(f"[{message.timestamp}] {message.sender}: {message.content}\n")
            
            self.logger.info(f"Enhanced chat file saved: {output_file}")
            return output_file
            
        except Exception as e:
            error_msg = f"Failed to generate enhanced chat file: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
            raise
    
    def _log_final_stats(self):
        """Log final processing statistics."""
        cost_summary = self.ai_manager.get_cost_summary()
        
        self.logger.info("=== Processing Statistics ===")
        self.logger.info(f"Total messages: {self.stats.total_messages}")
        self.logger.info(f"Media messages: {self.stats.media_messages}")
        self.logger.info(f"Successfully processed: {self.stats.processed_media}")
        self.logger.info(f"Failed to process: {self.stats.failed_media}")
        self.logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
        self.logger.info(f"Images processed: {self.stats.images_processed}")
        self.logger.info(f"Audio files processed: {self.stats.audio_processed}")
        self.logger.info(f"Videos skipped: {sum(1 for mf in self.media_files.values() if mf.file_type == 'video')}")
        self.logger.info(f"OpenAI Vision calls: {cost_summary['vision_calls']}")
        self.logger.info(f"OpenAI Whisper minutes: {cost_summary['whisper_minutes']}")
        self.logger.info(f"Estimated cost: ${cost_summary['estimated_total_cost']:.3f}")
        self.logger.info(f"Processing time: {self.stats.processing_time:.2f}s")
        
        if self.stats.errors:
            self.logger.warning(f"Errors encountered: {len(self.stats.errors)}")
            for error in self.stats.errors[:5]:  # Show first 5 errors
                self.logger.warning(f"  - {error}")
            if len(self.stats.errors) > 5:
                self.logger.warning(f"  ... and {len(self.stats.errors) - 5} more errors")
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self.stats
    
    def test_ai_services(self) -> Dict[str, bool]:
        """Test all AI services connectivity."""
        return self.ai_manager.test_all_services() 