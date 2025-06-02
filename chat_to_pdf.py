"""
Chat to PDF Converter

One-command solution to convert WhatsApp chat exports to professional PDF reports.

Usage:
    python chat_to_pdf.py /path/to/chat/folder [output_folder]

Created: January 2025
Author: AI Assistant
Changes: Initial implementation for direct chat-to-PDF conversion
"""

import sys
import logging
from pathlib import Path
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from config import Config
from chat_processor import ChatProcessor
from dashboard_generator import ConferenceDashboardManager


def find_chat_file(chat_folder: Path) -> Path:
    """Find the main chat text file in the folder."""
    txt_files = list(chat_folder.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt chat files found in {chat_folder}")
    
    # Look for the main chat file (usually largest or contains "chat")
    main_file = None
    for txt_file in txt_files:
        if "chat" in txt_file.name.lower() or txt_file.stat().st_size > 1000:
            main_file = txt_file
            break
    
    return main_file or txt_files[0]


def main():
    """Main function for chat to PDF conversion."""
    parser = argparse.ArgumentParser(
        description="Convert WhatsApp chat folder to professional PDF report"
    )
    parser.add_argument(
        "chat_folder",
        type=str,
        help="Path to folder containing WhatsApp chat export"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output/pdf_reports",
        help="Output folder for generated reports (default: output/pdf_reports)"
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        help="Conference/chat name (default: auto-detected from folder)"
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Generate only Markdown, skip PDF conversion"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    chat_folder = Path(args.chat_folder)
    output_folder = Path(args.output)
    
    if not chat_folder.exists():
        print(f"❌ Chat folder not found: {chat_folder}")
        return 1
    
    # Auto-detect conference name
    conference_name = args.name or chat_folder.name
    
    print("🚀 WhatsApp Chat to PDF Converter")
    print("=" * 40)
    print(f"📁 Chat folder: {chat_folder}")
    print(f"📤 Output folder: {output_folder}")
    print(f"📊 Conference name: {conference_name}")
    print(f"📄 Generate PDF: {not args.no_pdf}")
    
    try:
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        config = Config()
        if not config.openai_api_key:
            print("❌ OpenAI API key required. Set OPENAI_API_KEY in .env file")
            return 1
        if not config.anthropic_api_key:
            print("❌ Anthropic API key required. Set ANTHROPIC_API_KEY in .env file")
            return 1
        
        print("✅ API keys found")
        
        # Find chat file
        chat_file = find_chat_file(chat_folder)
        print(f"📄 Found chat file: {chat_file.name}")
        
        # Step 1: Process chat to enhanced format
        print("\n🔄 Step 1: Processing WhatsApp chat...")
        processor = ChatProcessor(config)
        
        # Setup processing paths
        enhanced_output = output_folder / "enhanced"
        enhanced_output.mkdir(exist_ok=True)
        
        success = processor.process_chat_export(
            input_folder=chat_folder,
            output_folder=enhanced_output
        )
        
        if not success:
            print("❌ Chat processing failed")
            return 1
        
        print(f"✅ Chat processing completed successfully")
        print(f"📊 Processed {processor.stats.total_messages} messages, {processor.stats.processed_media} media files")
        
        # Find the enhanced chat file
        enhanced_files = list(enhanced_output.glob("*_enhanced_*.txt"))
        if not enhanced_files:
            print("❌ No enhanced chat file generated")
            return 1
        
        enhanced_chat_path = enhanced_files[0]
        print(f"📄 Enhanced chat: {enhanced_chat_path.name}")
        
        # Step 2: Generate reports
        print(f"\n🔄 Step 2: Generating {'PDF and Markdown' if not args.no_pdf else 'Markdown'} reports...")
        
        manager = ConferenceDashboardManager(config)
        result = manager.create_conference_dashboard(
            enhanced_chat_path=enhanced_chat_path,
            media_folder=chat_folder,
            output_folder=output_folder,
            conference_name=conference_name,
            generate_pdf=not args.no_pdf
        )
        
        # Display results
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📄 Markdown Report: {result['markdown']}")
        if 'pdf' in result:
            print(f"📄 PDF Report: {result['pdf']}")
        print(f"📊 Analysis Data: {result['analysis']}")
        
        # File sizes
        md_size = Path(result['markdown']).stat().st_size / 1024
        print(f"📊 Markdown size: {md_size:.1f} KB")
        
        if 'pdf' in result:
            pdf_size = Path(result['pdf']).stat().st_size / 1024
            print(f"📊 PDF size: {pdf_size:.1f} KB")
        
        print(f"\n✅ All files saved to: {output_folder}")
        print(f"\nNext steps:")
        print(f"1. Review the generated report")
        print(f"2. Share with team members")
        print(f"3. Use for follow-up actions")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        logging.exception("Conversion failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 