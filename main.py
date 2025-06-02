#!/usr/bin/env python3
"""
WhatsApp Chat Notes Processor - Main Application

Processes WhatsApp chat exports to replace media file references with
AI-generated descriptions and transcriptions.

Created: January 2025
Author: AI Assistant
Changes: Updated to use ChatProcessor for end-to-end processing pipeline
"""

import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from config import Config
from chat_processor import ChatProcessor


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def validate_input_folder(folder_path: Path) -> bool:
    """
    Validate that the input folder exists and contains WhatsApp export files.
    
    Args:
        folder_path: Path to the input folder
        
    Returns:
        True if valid, False otherwise
    """
    if not folder_path.exists():
        print(f"❌ Error: Input folder does not exist: {folder_path}")
        return False
    
    if not folder_path.is_dir():
        print(f"❌ Error: Input path is not a directory: {folder_path}")
        return False
    
    # Check for WhatsApp chat file (*.txt)
    txt_files = list(folder_path.glob("*.txt"))
    if not txt_files:
        print(f"❌ Error: No WhatsApp chat file (*.txt) found in: {folder_path}")
        print("   WhatsApp exports typically contain a .txt file with the chat messages.")
        return False
    
    return True


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Process WhatsApp chat exports with AI-enhanced media descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py /path/to/whatsapp/export/folder
  python main.py ./MAU --verbose
  python main.py ~/Downloads/WhatsApp_Chat --output ./enhanced_chats

The input folder should contain:
  - A .txt file with WhatsApp chat messages
  - Media files (images, videos, audio) referenced in the chat

Output will be saved to the output/ directory by default.
        """
    )
    
    parser.add_argument(
        'input_folder',
        type=Path,
        help='Path to WhatsApp export folder containing chat file and media'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('output'),
        help='Output directory for enhanced chat files (default: output/)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching of AI service results'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 WhatsApp Chat Notes Processor")
    print("="*50)
    
    # Validate input folder
    if not validate_input_folder(args.input_folder):
        sys.exit(1)
    
    try:
        # Load and validate configuration
        config = Config()
        if args.no_cache:
            config.use_cache = False
        
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize chat processor
        processor = ChatProcessor(config)
        
        # Display processing info
        print(f"📁 Input Folder: {args.input_folder}")
        print(f"📂 Output Folder: {args.output}")
        print(f"🗄️  Caching: {'Enabled' if config.use_cache else 'Disabled'}")
        print()
        
        # Process the chat export
        success = processor.process_chat_export(args.input_folder, args.output)
        
        if success:
            print("\n✅ Chat processing completed successfully!")
            print(f"📋 Check {args.output}/ for enhanced chat files and processing reports")
            sys.exit(0)
        else:
            print("\n❌ Chat processing failed!")
            print("💡 Check the logs above for error details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        print("💡 Run with --verbose flag for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main() 