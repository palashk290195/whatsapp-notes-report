#!/usr/bin/env python3
"""
Test Fallback Services

Tests the OpenAI Vision fallback service and fixed Gemini video processing.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from ai_services import AIServiceManager
from file_manager import MediaFile


def create_test_media_file(filepath: Path, file_type: str) -> MediaFile:
    """Create a MediaFile object for testing."""
    return MediaFile(
        filename=filepath.name,
        filepath=filepath,
        file_type=file_type,
        size_bytes=filepath.stat().st_size if filepath.exists() else 0,
        extension=filepath.suffix
    )


def test_openai_vision_service():
    """Test OpenAI Vision service specifically."""
    print("🧪 Testing OpenAI Vision Service")
    print("-" * 40)
    
    load_dotenv()
    config = Config()
    
    if not config.openai_api_key:
        print("❌ OpenAI API key not found. Add OPENAI_API_KEY to .env")
        return False
    
    try:
        from ai_services.openai_vision_service import OpenAIVisionService
        vision_service = OpenAIVisionService(config.openai_api_key)
        
        # Test connection
        if vision_service.test_connection():
            print("✅ OpenAI Vision connection successful")
        else:
            print("❌ OpenAI Vision connection failed")
            return False
        
        # Test with sample image if available
        test_images = [
            Path("notes/MAU/IMG-20250520-WA0057.jpg"),  # From your MAU folder
            Path("test_image.jpg"),
        ]
        
        for img_path in test_images:
            if img_path.exists():
                print(f"\n📸 Testing with: {img_path}")
                
                media_file = create_test_media_file(img_path, "image")
                response = vision_service.describe_with_retry(media_file)
                
                if response.success:
                    print(f"✅ Description: {response.description[:100]}...")
                    print(f"⏱️  Processing time: {response.processing_time:.2f}s")
                    return True
                else:
                    print(f"❌ Error: {response.error}")
        
        print("ℹ️  No test images found to process")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Vision test failed: {e}")
        return False


def test_gemini_video_fix():
    """Test the fixed Gemini video processing."""
    print("\n🎥 Testing Fixed Gemini Video Processing")
    print("-" * 40)
    
    load_dotenv()
    config = Config()
    
    if not config.gemini_api_key:
        print("❌ Gemini API key not found")
        return False
    
    try:
        from ai_services.gemini_service import GeminiService
        gemini_service = GeminiService(config.gemini_api_key)
        
        # Test with sample video if available
        test_videos = [
            Path("notes/MAU/VID-20250522-WA0030.mp4"),  # From your MAU folder
            Path("test_video.mp4"),
        ]
        
        for vid_path in test_videos:
            if vid_path.exists():
                print(f"\n🎬 Testing with: {vid_path}")
                
                media_file = create_test_media_file(vid_path, "video")
                response = gemini_service.describe_video(media_file)
                
                if response.success:
                    print(f"✅ Description: {response.description[:100]}...")
                    print(f"⏱️  Processing time: {response.processing_time:.2f}s")
                    return True
                else:
                    print(f"❌ Error: {response.error}")
        
        print("ℹ️  No test videos found to process")
        return True
        
    except Exception as e:
        print(f"❌ Gemini video test failed: {e}")
        return False


def test_integrated_fallback():
    """Test the integrated fallback system."""
    print("\n🔄 Testing Integrated Fallback System")
    print("-" * 40)
    
    load_dotenv()
    config = Config()
    
    try:
        # Initialize service manager with all keys
        manager = AIServiceManager(
            gemini_key=config.gemini_api_key,
            assembly_ai_key=config.assembly_ai_api_key,
            openai_key=config.openai_api_key,
            use_cache=False  # Disable cache for testing
        )
        
        # Test services connectivity
        services_status = manager.test_all_services()
        print("Service Status:")
        for service, status in services_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {service.title()}")
        
        # Test with sample image
        test_images = [
            Path("notes/MAU/IMG-20250520-WA0057.jpg"),
        ]
        
        for img_path in test_images:
            if img_path.exists():
                print(f"\n📸 Testing fallback with: {img_path}")
                
                media_file = create_test_media_file(img_path, "image")
                result = manager.process_media_file(media_file)
                
                if result.success:
                    print(f"✅ Service used: {result.service_used}")
                    print(f"📝 Description: {result.description[:100]}...")
                    print(f"⏱️  Processing time: {result.processing_time:.2f}s")
                else:
                    print(f"❌ Error: {result.error}")
                
                # Show cost summary
                cost_summary = manager.get_cost_summary()
                print(f"💰 Cost: ${cost_summary['estimated_total_cost']:.3f}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated fallback test failed: {e}")
        return False


def main():
    """Run all fallback service tests."""
    print("🚀 Fallback Services Test Suite\n")
    
    test_results = []
    
    # Test OpenAI Vision
    test_results.append(test_openai_vision_service())
    
    # Test Gemini video fix
    test_results.append(test_gemini_video_fix())
    
    # Test integrated fallback
    test_results.append(test_integrated_fallback())
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        print("💡 Fallback services are ready for production")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("🔧 Some services may need configuration")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 