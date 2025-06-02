#!/usr/bin/env python3
"""
Test script for AI services integration.

Tests connection and basic functionality of all AI services.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from ai_services import AIServiceManager


def setup_logging():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_ai_services():
    """Test AI services connectivity and basic functionality."""
    print("🔍 Testing AI Services Integration...")
    
    # Load configuration
    try:
        config = Config()
        config.validate()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Initialize AI Service Manager
    try:
        ai_manager = AIServiceManager(
            gemini_key=config.gemini_api_key,
            assembly_ai_key=config.assembly_ai_api_key,
            openai_key=config.openai_api_key,
            use_cache=True
        )
        print("✅ AI Service Manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AI Service Manager: {e}")
        return False
    
    # Test service connections
    print("\n🔗 Testing service connections...")
    
    connection_results = ai_manager.test_all_services()
    
    for service, connected in connection_results.items():
        status = "✅" if connected else "❌"
        print(f"{status} {service.replace('_', ' ').title()}: {'Connected' if connected else 'Failed'}")
    
    # Check if at least one service of each type is working
    gemini_ok = connection_results.get('gemini', False)
    audio_ok = connection_results.get('assembly_ai', False) or connection_results.get('whisper', False)
    
    if gemini_ok and audio_ok:
        print("\n✅ All required services are operational!")
        return True
    else:
        print("\n⚠️  Some services are not operational:")
        if not gemini_ok:
            print("   - Gemini (images/videos) is not working")
        if not audio_ok:
            print("   - No audio transcription service is working")
        return False


def show_cost_tracking():
    """Show cost tracking capabilities."""
    print("\n💰 Cost Tracking Features:")
    print("   - Gemini API calls tracked")
    print("   - Assembly AI minutes tracked")
    print("   - OpenAI Whisper minutes tracked")
    print("   - Real-time cost estimation")
    print("   - Usage summary reports")


def show_caching_info():
    """Show caching capabilities."""
    print("\n🗄️  Caching Features:")
    print("   - File-based result caching")
    print("   - Smart cache key generation")
    print("   - Automatic cache invalidation")
    print("   - Significant cost savings on re-runs")


def main():
    """Main test function."""
    setup_logging()
    
    print("🚀 WhatsApp Chat Notes - AI Services Test\n")
    
    # Test services
    if test_ai_services():
        print("\n🎉 AI Services are ready for processing!")
        
        show_cost_tracking()
        show_caching_info()
        
        print("\n📝 Next Steps:")
        print("   1. Place WhatsApp export folder in the project directory")
        print("   2. Run: python main.py /path/to/whatsapp/folder")
        print("   3. Check output/ folder for enhanced chat files")
        
        return True
    else:
        print("\n❌ AI Services test failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your API keys in .env file")
        print("   2. Verify internet connection")
        print("   3. Check API quotas and billing")
        print("   4. Review service documentation")
        
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 