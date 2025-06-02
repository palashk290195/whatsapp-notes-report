#!/usr/bin/env python3
"""
End-to-End Test for WhatsApp Chat Processing Pipeline

Creates sample data and tests the complete processing pipeline.
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from chat_processor import ChatProcessor


def create_sample_whatsapp_export(temp_dir: Path) -> Path:
    """Create a sample WhatsApp export folder for testing."""
    
    # Ensure the directory exists
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Create chat content
    chat_content = """25/12/2024, 10:30 - Alice: Hey everyone! Happy holidays! 🎄
25/12/2024, 10:32 - Bob: IMG-20241225-WA0001.jpg (file attached)
25/12/2024, 10:33 - Bob: Check out this amazing sunset!
25/12/2024, 10:35 - Charlie: That's beautiful! 
25/12/2024, 10:37 - Alice: PTT-20241225-WA0001.opus (file attached)
25/12/2024, 10:38 - Bob: What did you say Alice? Can't listen right now
25/12/2024, 10:40 - Charlie: VID-20241225-WA0001.mp4 (file attached)
25/12/2024, 10:41 - Charlie: Here's a quick video from the party!
25/12/2024, 10:42 - Alice: Looks like everyone's having fun!
25/12/2024, 10:45 - Bob: Thanks for sharing! Best holiday ever 🎉
"""
    
    # Create chat file
    chat_file = temp_dir / "WhatsApp Chat - Test Group.txt"
    chat_file.write_text(chat_content, encoding='utf-8')
    
    # Create dummy media files (empty files for testing)
    media_files = [
        "IMG-20241225-WA0001.jpg",
        "PTT-20241225-WA0001.opus", 
        "VID-20241225-WA0001.mp4"
    ]
    
    for media_file in media_files:
        media_path = temp_dir / media_file
        media_path.write_bytes(b"dummy_content")  # Create empty files
    
    print(f"📁 Created sample WhatsApp export in: {temp_dir}")
    print(f"   - Chat file: {chat_file.name}")
    print(f"   - Media files: {len(media_files)}")
    
    return temp_dir


def test_processing_pipeline():
    """Test the complete processing pipeline."""
    print("🧪 Starting End-to-End Pipeline Test")
    print("="*50)
    
    # Load environment
    load_dotenv()
    
    try:
        # Test configuration
        config = Config()
        config.validate()
        print("✅ Configuration loaded and validated")
        
        # Create sample data in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample WhatsApp export
            input_folder = create_sample_whatsapp_export(temp_path / "sample_export")
            output_folder = temp_path / "output"
            
            print("\n🔧 Initializing Chat Processor...")
            processor = ChatProcessor(config)
            
            print("\n🚀 Starting Processing Pipeline...")
            success = processor.process_chat_export(input_folder, output_folder)
            
            if success:
                print("\n✅ END-TO-END TEST PASSED!")
                print("🎉 Complete pipeline is working correctly")
                
                # List output files
                if output_folder.exists():
                    output_files = list(output_folder.glob("*"))
                    print(f"\n📋 Generated {len(output_files)} output files:")
                    for file in output_files:
                        print(f"   - {file.name}")
                
                return True
            else:
                print("\n❌ END-TO-END TEST FAILED!")
                print("💡 Check the logs above for detailed error information")
                return False
                
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 WhatsApp Chat Processor - End-to-End Test\n")
    
    success = test_processing_pipeline()
    
    if success:
        print("\n🎯 RESULT: All tests passed!")
        print("💡 The processing pipeline is ready for production use")
    else:
        print("\n⚠️  RESULT: Tests failed!")
        print("🔧 Please check configuration and AI service connectivity")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 