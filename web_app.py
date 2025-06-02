"""
WhatsApp Chat Notes Web Application

Modern web interface for processing WhatsApp chat exports with real-time progress
tracking and live markdown report generation.

Features:
- Drag & drop zip file upload
- OpenAI-powered processing (Vision, Whisper, GPT)
- Real-time processing progress with WebSockets
- Editable markdown with live preview
- PDF download from edited content
- Detailed media processing logs
- Modern, responsive UI

Created: January 2025
Author: AI Assistant
Changes: Simplified to OpenAI-only processing for images, audio, and reports
"""

import os
import tempfile
import zipfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import json
import time
from datetime import datetime
import io

from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

from config import Config
from chat_processor import ChatProcessor
from dashboard_generator import ConferenceDashboardManager


class WebAppLogger:
    """Custom logger for web app that emits to clients."""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
    
    def emit_progress(self, message: str, progress: int = 0, status: str = "processing"):
        """Emit progress update to connected clients."""
        self.socketio.emit('progress_update', {
            'message': message,
            'progress': progress,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        self.logger.info(f"Progress: {message} ({progress}%)")


class OpenAIConfig(Config):
    """OpenAI-only configuration that allows custom API keys."""
    
    def __init__(self, openai_key: str = None):
        super().__init__()
        
        # Override with custom OpenAI key if provided
        if openai_key:
            self.openai_api_key = openai_key
        
        # We'll use OpenAI for everything, so ensure we have the key
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for all processing")


class ChatProcessorWebApp:
    """Web application for chat processing."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'whatsapp-chat-processor-secret'
        self.app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size for large exports
        
        # Enable CORS for all domains
        CORS(self.app, origins="*", allow_headers="*", methods=["GET", "POST", "OPTIONS"])
        
        # Initialize SocketIO with proper CORS settings
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*", 
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Initialize logger
        self.web_logger = WebAppLogger(self.socketio)
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio()
        
        # Active processing sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Create temp directory for uploads
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')
        
        @self.app.route('/health')
        def health():
            """Health check endpoint."""
            return jsonify({'status': 'healthy', 'message': 'WhatsApp Chat Processor is running'})
        
        @self.app.route('/upload', methods=['POST', 'OPTIONS'])
        def upload_file():
            """Handle file upload and start processing."""
            if request.method == 'OPTIONS':
                return '', 200
                
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not file.filename.lower().endswith('.zip'):
                    return jsonify({'error': 'Please upload a ZIP file'}), 400
                
                # Generate session ID
                session_id = f"session_{int(time.time())}"
                
                # Save uploaded file
                filename = secure_filename(file.filename)
                upload_path = self.temp_dir / f"{session_id}_{filename}"
                file.save(upload_path)
                
                # Get conference name and OpenAI API key from request
                conference_name = request.form.get('conference_name', 'Conference')
                openai_key = request.form.get('openai_key', '').strip()
                
                # Initialize session
                self.active_sessions[session_id] = {
                    'upload_path': upload_path,
                    'conference_name': conference_name,
                    'openai_key': openai_key,
                    'status': 'uploaded',
                    'progress': 0,
                    'start_time': time.time()
                }
                
                # Start processing in background
                processing_thread = threading.Thread(
                    target=self._process_chat_async,
                    args=(session_id,)
                )
                processing_thread.daemon = True
                processing_thread.start()
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'message': 'Upload successful, processing started'
                })
                
            except Exception as e:
                logging.error(f"Upload error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/convert-to-pdf', methods=['POST', 'OPTIONS'])
        def convert_to_pdf():
            """Convert edited markdown content to PDF."""
            if request.method == 'OPTIONS':
                return '', 200
            
            try:
                data = request.get_json()
                markdown_content = data.get('markdown_content', '')
                conference_name = data.get('conference_name', 'Conference')
                session_id = data.get('session_id', '')
                
                if not markdown_content:
                    return jsonify({'error': 'No markdown content provided'}), 400
                
                # Get session info for API keys
                session = self.active_sessions.get(session_id, {})
                openai_key = session.get('openai_key', '')
                
                # Create config with custom keys
                config = OpenAIConfig(openai_key)
                
                # Import PDF library
                try:
                    from markdown_pdf import MarkdownPdf, Section
                except ImportError:
                    return jsonify({'error': 'PDF generation library not available'}), 500
                
                # Generate PDF in memory
                pdf = MarkdownPdf(toc_level=3, optimize=True)
                
                # Set document metadata
                pdf.meta["title"] = f"{conference_name} - Conference Analysis Report"
                pdf.meta["author"] = "WhatsApp Chat Notes Processor"
                pdf.meta["subject"] = "AI-Generated Conference Intelligence Report"
                pdf.meta["keywords"] = "conference, analysis, business intelligence, whatsapp"
                pdf.meta["creator"] = "WhatsApp Chat Notes - AI Assistant"
                
                # Split content into sections
                sections = self._split_markdown_into_sections(markdown_content)
                
                # Professional CSS styling
                css_styles = """
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 20px;
                    }
                    
                    h1 {
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                        font-size: 2.2em;
                        margin-top: 30px;
                        margin-bottom: 20px;
                    }
                    
                    h2 {
                        color: #34495e;
                        border-left: 4px solid #3498db;
                        padding-left: 15px;
                        font-size: 1.6em;
                        margin-top: 25px;
                        margin-bottom: 15px;
                    }
                    
                    h3 {
                        color: #2c3e50;
                        font-size: 1.3em;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }
                    
                    p {
                        margin-bottom: 12px;
                        text-align: justify;
                    }
                    
                    ul, ol {
                        margin-left: 25px;
                        margin-bottom: 15px;
                    }
                    
                    blockquote {
                        border-left: 4px solid #bdc3c7;
                        padding-left: 20px;
                        margin: 15px 0;
                        font-style: italic;
                        background-color: #f8f9fa;
                        padding: 15px 15px 15px 35px;
                        border-radius: 0 8px 8px 0;
                    }
                    
                    strong {
                        color: #2c3e50;
                        font-weight: 600;
                    }
                    
                    code {
                        background-color: #f1f2f6;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: 'Monaco', 'Menlo', monospace;
                        font-size: 0.9em;
                    }
                """
                
                # Add sections to PDF
                for i, section_content in enumerate(sections):
                    if i == 0:
                        pdf.add_section(
                            Section(section_content, toc=False, paper_size="A4"),
                            user_css=css_styles
                        )
                    else:
                        pdf.add_section(
                            Section(section_content, paper_size="A4"),
                            user_css=css_styles
                        )
                
                # Save to temporary file
                temp_pdf_path = self.temp_dir / f"{session_id}_edited_report.pdf"
                pdf.save(str(temp_pdf_path))
                
                # Return PDF file
                return send_file(
                    temp_pdf_path,
                    as_attachment=True,
                    download_name=f"{conference_name.replace(' ', '_')}_report.pdf",
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                logging.error(f"PDF conversion error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status/<session_id>')
        def get_status(session_id):
            """Get processing status for a session."""
            if session_id not in self.active_sessions:
                return jsonify({'error': 'Session not found'}), 404
            
            session = self.active_sessions[session_id]
            return jsonify({
                'status': session['status'],
                'progress': session['progress'],
                'message': session.get('message', ''),
                'elapsed_time': time.time() - session['start_time']
            })
        
        @self.app.route('/download/<session_id>/<file_type>')
        def download_file(session_id, file_type):
            """Download processed files."""
            if session_id not in self.active_sessions:
                return jsonify({'error': 'Session not found'}), 404
            
            session = self.active_sessions[session_id]
            if session['status'] != 'completed':
                return jsonify({'error': 'Processing not completed'}), 400
            
            file_path = None
            if file_type == 'markdown' and 'markdown_path' in session:
                file_path = session['markdown_path']
            elif file_type == 'enhanced' and 'enhanced_path' in session:
                file_path = session['enhanced_path']
            elif file_type == 'analysis' and 'analysis_path' in session:
                file_path = session['analysis_path']
            
            if not file_path or not Path(file_path).exists():
                return jsonify({'error': 'File not found'}), 404
            
            return send_file(file_path, as_attachment=True)
    
    def _split_markdown_into_sections(self, content: str) -> list:
        """Split markdown content into sections for PDF generation."""
        sections = []
        current_section = ""
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# ') and current_section.strip():
                sections.append(current_section.strip())
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        if current_section.strip():
            sections.append(current_section.strip())
        
        return sections if sections else [content]
    
    def _setup_socketio(self):
        """Setup SocketIO events."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            print("Client connected")
            emit('connected', {'message': 'Connected to WhatsApp Chat Processor'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            print("Client disconnected")
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Join a processing session to receive updates."""
            session_id = data.get('session_id')
            if session_id in self.active_sessions:
                emit('session_joined', {'session_id': session_id})
            else:
                emit('error', {'message': 'Session not found'})
    
    def _process_chat_async(self, session_id: str):
        """Process chat asynchronously with detailed progress updates."""
        try:
            session = self.active_sessions[session_id]
            upload_path = session['upload_path']
            conference_name = session['conference_name']
            openai_key = session.get('openai_key', '')
            
            # Update status
            session['status'] = 'extracting'
            session['progress'] = 5
            self.web_logger.emit_progress("Extracting uploaded ZIP file...", 5, "processing")
            
            # Extract ZIP file
            extract_dir = self.temp_dir / f"{session_id}_extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            session['progress'] = 10
            self.web_logger.emit_progress("ZIP file extracted successfully", 10, "success")
            
            # Find chat folder (usually the main folder in the zip)
            chat_folders = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not chat_folders:
                chat_folder = extract_dir
            else:
                chat_folder = chat_folders[0]
            
            session['progress'] = 15
            self.web_logger.emit_progress("Chat folder identified", 15, "success")
            
            # Initialize configuration with custom keys
            config = OpenAIConfig(openai_key)
            
            # Validate API keys
            if not config.openai_api_key:
                raise Exception("OpenAI API key required. Provide in UI or set OPENAI_API_KEY in .env file")
            
            session['progress'] = 20
            self.web_logger.emit_progress("API keys validated", 20, "success")
            
            # Setup output folders
            output_folder = self.temp_dir / f"{session_id}_output"
            enhanced_output = output_folder / "enhanced"
            enhanced_output.mkdir(parents=True, exist_ok=True)
            
            session['status'] = 'processing'
            session['progress'] = 25
            self.web_logger.emit_progress("Starting chat processing...", 25, "processing")
            
            # Process chat with detailed logging
            processor = ChatProcessor(config)
            
            # Create a custom logger that emits to WebSocket
            original_logger = processor.logger
            
            class WebSocketChatLogger:
                def __init__(self, web_logger, original_logger):
                    self.web_logger = web_logger
                    self.original_logger = original_logger
                
                def info(self, message):
                    self.original_logger.info(message)
                    # Send detailed media processing updates
                    if any(keyword in message.lower() for keyword in ['processing', 'transcribed', 'analyzed', 'enhanced']):
                        self.web_logger.emit_progress(message, session.get('progress', 50), "processing")
                
                def error(self, message):
                    self.original_logger.error(message)
                    self.web_logger.emit_progress(f"Error: {message}", session.get('progress', 50), "error")
                
                def warning(self, message):
                    self.original_logger.warning(message)
                    self.web_logger.emit_progress(f"Warning: {message}", session.get('progress', 50), "processing")
                
                def debug(self, message):
                    self.original_logger.debug(message)
            
            # Replace logger
            processor.logger = WebSocketChatLogger(self.web_logger, original_logger)
            
            # Process with progress tracking
            session['progress'] = 50
            self.web_logger.emit_progress("Processing messages and media files...", 50, "processing")
            
            success = processor.process_chat_export(
                input_folder=chat_folder,
                output_folder=enhanced_output
            )
            
            if not success:
                raise Exception("Chat processing failed")
            
            session['progress'] = 75
            self.web_logger.emit_progress("Chat processing completed", 75, "success")
            
            # Find enhanced chat file
            enhanced_files = list(enhanced_output.glob("*_enhanced_*.txt"))
            if not enhanced_files:
                raise Exception("No enhanced chat file generated")
            
            enhanced_chat_path = enhanced_files[0]
            session['enhanced_path'] = str(enhanced_chat_path)
            
            session['status'] = 'generating_report'
            session['progress'] = 80
            self.web_logger.emit_progress("Generating comprehensive report...", 80, "processing")
            
            # Generate reports
            manager = ConferenceDashboardManager(config)
            result = manager.create_conference_dashboard(
                enhanced_chat_path=enhanced_chat_path,
                media_folder=chat_folder,
                output_folder=output_folder,
                conference_name=conference_name,
                generate_pdf=False  # Skip PDF for web interface (users can generate from UI)
            )
            
            session['markdown_path'] = result['markdown']
            session['analysis_path'] = result['analysis']
            
            # Read markdown content for live display
            with open(result['markdown'], 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            session['markdown_content'] = markdown_content
            session['status'] = 'completed'
            session['progress'] = 100
            
            # Calculate processing stats
            processing_time = time.time() - session['start_time']
            stats = processor.stats if hasattr(processor, 'stats') else None
            
            self.web_logger.emit_progress("Processing completed successfully!", 100, "success")
            
            # Emit completion with results
            self.socketio.emit('processing_complete', {
                'session_id': session_id,
                'markdown_content': markdown_content,
                'processing_time': processing_time,
                'stats': {
                    'total_messages': stats.total_messages if stats else 0,
                    'processed_media': stats.processed_media if stats else 0,
                    'estimated_cost': f"${stats.estimated_cost:.2f}" if stats else "$0.00"
                },
                'download_links': {
                    'enhanced': f'/download/{session_id}/enhanced',
                    'analysis': f'/download/{session_id}/analysis'
                }
            })
            
        except Exception as e:
            logging.error(f"Processing error for session {session_id}: {e}")
            session['status'] = 'error'
            session['error'] = str(e)
            self.web_logger.emit_progress(f"Error: {str(e)}", session.get('progress', 0), "error")
            
            self.socketio.emit('processing_error', {
                'session_id': session_id,
                'error': str(e)
            })
    
    def run(self, debug=False, host='127.0.0.1', port=8000):
        """Run the web application."""
        print(f"🚀 WhatsApp Chat Notes Web UI")
        print(f"📡 Starting server at http://{host}:{port}")
        print(f"🌐 Open your browser and navigate to: http://localhost:{port}")
        print(f"💡 To access from other devices, use: http://{host}:{port}")
        print(f"🔑 API Keys: Provide in UI or use .env file")
        print(f"📝 Features: Editable markdown, PDF export, real-time progress")
        
        self.socketio.run(self.app, debug=debug, host=host, port=port, allow_unsafe_werkzeug=True)


def create_app():
    """Create and configure the Flask app."""
    web_app = ChatProcessorWebApp()
    return web_app.app, web_app.socketio


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create and run app
    app = ChatProcessorWebApp()
    app.run(debug=False, host='127.0.0.1', port=8000) 