# WhatsApp Chat Notes Processor - Project Plan

## Overview
A Python application that processes WhatsApp chat exports by replacing media file references with AI-generated descriptions, creating a comprehensive text-based record of chat conversations.

## System Architecture

### Input Processing
- **Input**: Folder containing WhatsApp export
  - `.txt` file with chat messages
  - Media files (images, videos, audio)
- **Processing**: Parse chat messages and identify media references
- **Output**: Single processed `.txt` file with AI descriptions

### AI Services Integration
1. **Google Gemini API**: Image and video description
2. **Assembly AI**: Primary speech-to-text service
3. **OpenAI Whisper**: Backup speech-to-text service

### Data Flow
```
WhatsApp Export Folder
    ↓
Parse .txt file → Identify media references
    ↓
Process Media Files:
├── Images/Videos → Gemini API → Descriptions
└── Audio (.opus) → Convert to MP3 → Assembly AI/Whisper → Transcriptions
    ↓
Generate Enhanced Chat File
    ↓
Save to output/ folder
```

## Technical Design

### Core Components
1. **File Parser**: Extract and parse WhatsApp chat format
2. **Media Processor**: Handle different media types
3. **AI Service Manager**: Manage API calls and fallbacks
4. **Output Generator**: Create enhanced chat file

### Media Processing Pipeline
- **Images**: `.jpg`, `.png` → Gemini Vision → "This is an image: [description]"
- **Videos**: `.mp4` → Gemini Vision → "This is a video: [description]"
- **Audio**: `.opus` → Convert to `.mp3` → Assembly AI → "Voice note: [transcription]"

### Error Handling & Fallbacks
- Assembly AI failure → OpenAI Whisper
- API rate limiting → Exponential backoff
- File processing errors → Skip with logged warning

## Scalability Considerations

### Performance Optimization
- **Batch Processing**: Group API calls for efficiency
- **Caching**: Store processed results to avoid reprocessing
- **Parallel Processing**: Handle multiple media files concurrently
- **Memory Management**: Stream large files instead of loading entirely

### API Management
- **Rate Limiting**: Respect API quotas and implement backoff strategies
- **Cost Control**: Monitor usage and implement budget alerts
- **Service Redundancy**: Multiple fallback options for critical services

### Future Extensibility
- **Plugin Architecture**: Easy integration of new AI services
- **Format Support**: Extensible to other chat export formats
- **Output Formats**: Support multiple output types (JSON, HTML, Markdown)

## Trade-off Analysis

### 1. Processing Strategy
**Sequential vs Parallel Processing**
- **Sequential**: Simpler implementation, predictable resource usage, easier debugging
- **Parallel**: Faster processing, better resource utilization, complex error handling
- **Decision**: Start sequential, add parallel processing for performance optimization

### 2. AI Service Strategy
**Single Provider vs Multi-Provider**
- **Single**: Simpler integration, consistent quality, vendor lock-in risk
- **Multi**: Redundancy, cost optimization, increased complexity
- **Decision**: Multi-provider with primary/backup strategy for reliability

### 3. Storage Strategy
**In-Memory vs File-Based Processing**
- **In-Memory**: Faster processing, memory limitations, data loss risk
- **File-Based**: Scalable, persistent, slower I/O operations
- **Decision**: Hybrid approach - memory for small files, streaming for large ones

### 4. Caching Strategy
**No Cache vs Persistent Cache**
- **No Cache**: Simpler, always fresh results, repeated API costs
- **Persistent**: Cost-effective, faster reprocessing, cache invalidation complexity
- **Decision**: Implement file-based cache with optional cache clearing

### 5. Output Format Strategy
**Single Format vs Multiple Formats**
- **Single**: Focused implementation, limited use cases
- **Multiple**: Flexible, increased complexity, maintenance overhead
- **Decision**: Start with enhanced text, plan for structured formats (JSON/HTML)

## Implementation Phases

### Phase 1: Core Processing Engine
- File parsing and media identification
- Basic AI service integration
- Simple text output generation

### Phase 2: Enhanced Processing
- Parallel media processing
- Comprehensive error handling
- Caching implementation

### Phase 3: Advanced Features
- Multiple output formats
- Web interface for processing
- Batch processing capabilities

### Phase 4: Analytics & Insights
- Chat analytics generation
- Trend analysis
- Interactive HTML dashboard

## Next Steps
1. Create detailed task checklist
2. Implement core parsing functionality
3. Integrate AI services
4. Build processing pipeline
5. Add error handling and optimization 