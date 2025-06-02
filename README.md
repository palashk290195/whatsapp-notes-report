# WhatsApp Chat Notes Processor

Transform your WhatsApp chat exports into AI-enhanced text records with detailed descriptions of media files.

## 🎯 What It Does

Takes WhatsApp export folders containing:
- Chat text file (`.txt`)
- Media files (images, videos, voice notes)

And produces:
- **Enhanced chat file** with AI-generated descriptions replacing media references
- **Processing reports** with statistics and costs
- **Cached results** for efficient reprocessing

## ✨ Key Features

### 🤖 **Multi-Service AI Processing**
- **Images & Videos**: Google Gemini with OpenAI Vision fallback
- **Audio**: Assembly AI with OpenAI Whisper fallback  
- **Smart Fallbacks**: Automatic service switching on rate limits/failures

### 📁 **Media Support**
- **Images**: `.jpg`, `.png`, `.webp`, `.heic` → Detailed descriptions
- **Videos**: `.mp4`, `.mov`, `.avi` → Scene and action descriptions  
- **Audio**: `.opus`, `.mp3`, `.wav` → Full transcriptions

### 💡 **Smart Features**
- **Rate Limiting**: Respects API limits (15 req/min for Gemini)
- **Caching**: Avoids reprocessing identical files
- **Cost Tracking**: Real-time cost estimation 
- **Batch Processing**: Handles entire chat histories
- **Error Recovery**: Robust retry mechanisms

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
# Create virtual environment
python -m venv whatsapp-chat-env
source whatsapp-chat-env/bin/activate  # On Windows: whatsapp-chat-env\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. **Setup API Keys**
Create `.env` file with your API keys:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
ASSEMBLY_AI_API_KEY=your_assembly_ai_key_here

# Optional (for enhanced fallbacks)
OPENAI_API_KEY=your_openai_api_key_here
```

**Get API Keys:**
- **Gemini (Free)**: [Google AI Studio](https://ai.google.dev/)
- **Assembly AI (Free tier)**: [AssemblyAI](https://www.assemblyai.com/)
- **OpenAI (Optional)**: [OpenAI Platform](https://platform.openai.com/)

### 3. **Prepare WhatsApp Export**
1. Open WhatsApp → Chat → Export Chat → Include Media
2. Extract to folder (e.g., `notes/MyChat/`)
3. Ensure folder contains:
   - `WhatsApp Chat with [Name].txt`
   - Media files (`IMG-*`, `PTT-*`, `VID-*`)

### 4. **Process Your Chat**
```bash
# Basic processing
python main.py notes/MyChat --output output/

# With verbose logging  
python main.py notes/MyChat --output output/ --verbose

# Disable caching (for testing)
python main.py notes/MyChat --output output/ --no-cache
```

## 📊 Example Output

### **Original WhatsApp Export:**
```
25/12/2024, 10:30 - Alice: Happy holidays everyone! 🎄
25/12/2024, 10:32 - Bob: IMG-20241225-WA0001.jpg (file attached)
25/12/2024, 10:33 - Bob: Check out this sunset!
25/12/2024, 10:35 - Charlie: PTT-20241225-WA0001.opus (file attached)
```

### **Enhanced Output:**
```
25/12/2024, 10:30 - Alice: Happy holidays everyone! 🎄
25/12/2024, 10:32 - Bob: This is an image: A beautiful sunset over the ocean with vibrant orange and pink clouds reflecting on the water. A silhouette of palm trees is visible in the foreground.
25/12/2024, 10:33 - Bob: Check out this sunset!
25/12/2024, 10:35 - Charlie: Voice note: "Hey everyone, just wanted to say I'm so grateful for our friendship. Hope you all have an amazing holiday season!"
```

## 🛠️ Advanced Configuration

### **Environment Variables**
```bash
# Processing settings
PARALLEL_PROCESSING=false           # Enable parallel processing (experimental)
USE_CACHE=true                     # Enable result caching

# Service priorities (optional)
PREFER_OPENAI_VISION=false         # Use OpenAI Vision as primary for images
PREFER_WHISPER=false               # Use Whisper as primary for audio
```

### **Command Line Options**
```bash
python main.py <input_folder> [options]

Options:
  --output DIR          Output directory (default: output/)
  --verbose            Enable detailed logging
  --no-cache           Disable result caching  
  --parallel           Enable parallel processing (experimental)
  --dry-run            Analyze files without processing
```

## 💰 Cost Estimates

**Typical chat processing costs:**

| Service | Usage | Cost per Unit | Example Cost |
|---------|-------|---------------|--------------|
| **Gemini** | Images/Videos | ~$0.01 each | 30 images = $0.30 |
| **Assembly AI** | Audio transcription | $0.20/minute | 10 min audio = $2.00 |
| **OpenAI Vision** | Image fallback | $0.003 each | 10 images = $0.03 |
| **OpenAI Whisper** | Audio fallback | $0.006/minute | 5 min audio = $0.03 |

**Real example:** 147 messages + 53 media files = **$0.45 total**

## 🔧 Troubleshooting

### **Common Issues**

**Rate Limits:**
- Gemini: 15 requests/minute (free tier)
- Solution: System automatically uses OpenAI Vision fallback

**API Key Errors:**
```bash
# Test your configuration
python -c "from config import Config; print(Config().validate())"
```

**File Size Limits:**
- Images: 20MB max
- Videos: 10MB max (inline processing)
- Audio: 25MB max

**Performance:**
- Enable caching: `USE_CACHE=true`
- Process smaller batches for large chats
- Use `--verbose` for detailed progress

### **Debug Mode**
```bash
# Test AI services
python test_fallback_services.py

# Test end-to-end pipeline  
python test_end_to_end.py

# Detailed logs
python main.py input/ --output output/ --verbose
```

## 📁 Project Structure

```
app/
├── main.py                 # Main application entry point
├── config.py              # Configuration and API key management  
├── chat_parser.py          # WhatsApp chat parsing logic
├── chat_processor.py       # Main processing pipeline
├── file_manager.py         # Media file discovery and management
├── ai_services/           # AI service integrations
│   ├── __init__.py
│   ├── service_manager.py  # Service orchestration with fallbacks
│   ├── gemini_service.py   # Google Gemini vision API
│   ├── assembly_service.py # Assembly AI transcription  
│   ├── whisper_service.py  # OpenAI Whisper transcription
│   └── openai_vision_service.py # OpenAI Vision fallback
├── output/                # Generated files and cache
├── docs/                  # Documentation and planning
└── tests/                 # Test scripts
```

## 🤝 Contributing

Found a bug or want to add a feature?

1. **Test your changes**
2. **Update documentation** 
3. **Check cost implications**
4. **Maintain fallback compatibility**

## 📄 License

MIT License - Feel free to modify and distribute!

---

**Built with:** Python, Google Gemini, Assembly AI, OpenAI, ❤️ 