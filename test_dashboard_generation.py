"""
Test Conference Summary Generation

Tests the summary generator with the MAU conference enhanced chat file.

Created: January 2025
Author: AI Assistant
Changes: Updated to generate Markdown summaries instead of HTML dashboards
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from config import Config
from dashboard_generator import ConferenceDashboardManager


def test_mau_summary():
    """Test Markdown summary generation with MAU conference data."""
    
    # Setup paths
    enhanced_chat_path = Path("output/MAU/MAU_enhanced_20250601_201344.txt")
    media_folder = Path("output/MAU")  # Contains the original media files
    output_folder = Path("output/dashboard")
    
    print("🚀 Testing MAU Conference Detailed Report Generation")
    print("=" * 55)
    
    # Verify input files exist
    if not enhanced_chat_path.exists():
        print(f"❌ Enhanced chat file not found: {enhanced_chat_path}")
        return False
    
    print(f"✅ Found enhanced chat file: {enhanced_chat_path}")
    print(f"📁 Media folder: {media_folder}")
    print(f"📤 Output folder: {output_folder}")
    
    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    try:
        config = Config()
        if not config.openai_api_key:
            print("❌ OpenAI API key not found in environment")
            return False
        if not config.anthropic_api_key:
            print("❌ Anthropic API key not found in environment")
            return False
        print("✅ API keys found")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Generate detailed report
    try:
        print(f"\n🎯 Generating comprehensive MAU conference report...")
        
        manager = ConferenceDashboardManager(config)
        result = manager.create_conference_dashboard(
            enhanced_chat_path=enhanced_chat_path,
            media_folder=media_folder,
            output_folder=output_folder,
            conference_name="MAU Vegas 2025",
            generate_pdf=True
        )
        
        print(f"\n🎉 Detailed report generated successfully!")
        print(f"📄 Comprehensive Report: {result['markdown']}")
        if 'pdf' in result:
            print(f"📄 PDF Report: {result['pdf']}")
        print(f"📄 Analysis JSON: {result['analysis']}")
        
        # Check file sizes
        if Path(result['markdown']).exists():
            size_kb = Path(result['markdown']).stat().st_size / 1024
            print(f"📊 Markdown size: {size_kb:.1f} KB")
        
        if 'pdf' in result and Path(result['pdf']).exists():
            size_kb = Path(result['pdf']).stat().st_size / 1024
            print(f"📊 PDF size: {size_kb:.1f} KB")
        
        print(f"\n📖 View detailed report: {result['markdown']}")
        if 'pdf' in result:
            print(f"📖 View PDF report: {result['pdf']}")
        
        print(f"\n✅ Comprehensive report generation completed successfully!")
        
        print(f"\nNext steps:")
        print(f"1. Open the detailed Markdown report in your text editor")
        print(f"2. Open the PDF report for professional presentation")
        print(f"3. Review all comprehensive sections and insights")
        print(f"4. Check detailed action items and follow-ups")
        print(f"5. Use the complete report for strategic planning")
        print(f"6. Share relevant sections with team members")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mau_summary()
    sys.exit(0 if success else 1) 