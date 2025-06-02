"""
WhatsApp Chat Notes - Dashboard Generator

Advanced dashboard and report generation for WhatsApp chat analysis using
OpenAI for comprehensive content analysis and markdown report generation.

Features:
- OpenAI GPT-4o powered conference analysis with strategic insights
- OpenAI GPT-4o powered markdown report generation  
- Professional PDF generation using markdown-pdf
- Comprehensive business intelligence extraction
- Action items and follow-up identification
- Contact directory with evidence links

Created: June 2025
Author: AI Assistant  
Changes: Simplified to use OpenAI only for all analysis and report generation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re
import time
from datetime import datetime

# Import the new PDF library
from markdown_pdf import MarkdownPdf, Section

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

from config import Config


@dataclass
class DashboardSection:
    """Represents a section in the dashboard."""
    title: str
    content_type: str  # 'learnings', 'followups', 'insights', 'media', 'todos'
    content: Dict[str, Any]
    priority: int = 1


@dataclass
class MediaReference:
    """Represents a media file reference in the chat."""
    filename: str
    filepath: str
    media_type: str  # 'image', 'video', 'audio'
    description: str
    timestamp: str
    context: str


class ConferenceAnalyzer:
    """Analyzes conference chat content using OpenAI GPT-4."""
    
    def __init__(self, openai_api_key: str):
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=openai_api_key)
        self.logger = logging.getLogger(__name__)
    
    def analyze_conference_content(self, chat_content: str, 
                                 conference_name: str = "Conference") -> Dict[str, Any]:
        """
        Analyze conference chat content to identify key sections and insights.
        
        Args:
            chat_content: The enhanced chat content
            conference_name: Name of the conference
            
        Returns:
            Structured analysis with sections and insights
        """
        prompt = f"""
You are analyzing a WhatsApp chat from the {conference_name} conference. This chat contains:
- Key learnings and insights from sessions
- Networking conversations and follow-ups
- Business opportunities and partnerships
- Technical discussions
- Media descriptions (images, videos, voice notes)

Please analyze this content and structure it into logical sections for a conference dashboard.

ANALYSIS REQUIREMENTS:
1. **Key Learnings**: Group by themes/hypotheses (e.g., "AI Apps Monetization", "Playable Ads", "User Acquisition")
2. **Follow-ups**: Extract people to contact, meetings planned, potential partnerships
3. **Business Insights**: Market trends, competitive analysis, opportunities
4. **Technical Insights**: Tools, platforms, technical solutions discussed
5. **Media Highlights**: Important images/videos that support key points
6. **Action Items**: Concrete next steps and TODOs

For each section, provide:
- Title and description
- Priority (1-5, where 1 is highest)
- Key points with supporting quotes/evidence
- Relevant timestamps
- Connected people/companies

Format your response as valid JSON with this structure:
{{
  "conference_overview": {{
    "name": "{conference_name}",
    "total_messages": "count",
    "key_topics": ["topic1", "topic2", ...],
    "attendees": ["person1", "person2", ...]
  }},
  "sections": [
    {{
      "id": "unique_id",
      "title": "Section Title",
      "type": "learnings|followups|insights|media|todos",
      "priority": 1-5,
      "description": "Brief description",
      "content": {{
        "key_points": [
          {{
            "point": "Main insight",
            "evidence": "Supporting quote or context",
            "timestamp": "timestamp if available",
            "people": ["person1", "person2"],
            "companies": ["company1", "company2"]
          }}
        ],
        "subcategories": {{"category": ["items"]}}
      }}
    }}
  ],
  "media_references": [
    {{
      "description": "Media description from chat",
      "context": "Surrounding conversation context",
      "timestamp": "when it was shared",
      "relevance": "Why it's important"
    }}
  ],
  "action_items": [
    {{
      "task": "What to do",
      "person": "Who to contact",
      "priority": "high|medium|low",
      "deadline": "timeframe",
      "context": "Why it's important"
    }}
  ]
}}

CHAT CONTENT:
{chat_content[:15000]}...
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert conference analyst who extracts actionable insights from event communications. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Clean up the response to ensure valid JSON
            # Remove markdown formatting if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            analysis = json.loads(content)
            self.logger.info(f"Successfully analyzed conference content with {len(analysis.get('sections', []))} sections")
            return analysis
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse GPT-4o response as JSON: {e}")
            # Return a fallback structure
            return self._create_fallback_analysis(chat_content, conference_name)
        except Exception as e:
            self.logger.error(f"Error analyzing content with GPT-4o: {e}")
            return self._create_fallback_analysis(chat_content, conference_name)
    
    def _create_fallback_analysis(self, chat_content: str, conference_name: str) -> Dict[str, Any]:
        """Create a basic fallback analysis structure."""
        return {
            "conference_overview": {
                "name": conference_name,
                "total_messages": "N/A",
                "key_topics": ["Conference Discussions"],
                "attendees": []
            },
            "sections": [
                {
                    "id": "fallback_content",
                    "title": "Conference Content",
                    "type": "insights",
                    "priority": 1,
                    "description": "Raw conference content",
                    "content": {
                        "key_points": [
                            {
                                "point": "Conference content available",
                                "evidence": "Full chat content needs manual review",
                                "timestamp": "",
                                "people": [],
                                "companies": []
                            }
                        ]
                    }
                }
            ],
            "media_references": [],
            "action_items": []
        }

    def generate_markdown_summary(self, analysis: Dict[str, Any], 
                                output_path: Path) -> str:
        """
        Generate a comprehensive Markdown summary from the analysis using OpenAI.
        
        Args:
            analysis: Structured analysis from ConferenceAnalyzer
            output_path: Where to save the Markdown file
            
        Returns:
            Path to generated Markdown file
        """
        
        prompt = f"""
Create a comprehensive, detailed conference report in Markdown format. This should be a COMPLETE DETAILED REPORT, not a summary. Include ALL information from the analysis data with full context, evidence, and detailed analysis.

ANALYSIS DATA:
{json.dumps(analysis, indent=2)}

Create a detailed Markdown document with the following structure:

# {analysis.get('conference_overview', {}).get('name', 'Conference')} - Comprehensive Conference Report

## 📊 Conference Overview & Statistics
- Detailed conference information with all available metrics
- Complete attendee list with roles and context
- Comprehensive topic breakdown with detailed descriptions
- Timeline and duration information

## 🎓 Detailed Key Learnings & Insights

For EACH learning section, provide:
- **Complete Context**: Full background and circumstances
- **Detailed Evidence**: All quotes and conversations in full
- **Comprehensive Analysis**: What this means for business/industry
- **People Involved**: Detailed information about each person
- **Company Intelligence**: Complete information about each company mentioned
- **Timestamps**: All timing information
- **Subcategories**: All subcategory items with full details
- **Implications**: Business and strategic implications
- **Follow-up Questions**: What to explore further

## 🤝 Comprehensive Networking & Follow-ups

For EACH contact and interaction:
- **Complete Contact Information**: Names, phone numbers, emails, companies, roles
- **Detailed Meeting Context**: What was discussed, why it's important
- **Full Conversation Details**: Complete quotes and context
- **Collaboration Opportunities**: Detailed potential partnerships
- **Scheduled Activities**: All meetings, calls, follow-ups with timing
- **Company Background**: What we learned about their companies
- **Strategic Value**: Why each contact is important
- **Next Steps**: Detailed action plans for each relationship

## 💡 Comprehensive Business Intelligence

For EACH business insight:
- **Detailed Market Analysis**: Complete trends and opportunities
- **Company Strategies**: Full details of what companies are doing
- **Competitive Intelligence**: Detailed competitive landscape information
- **Business Implications**: Comprehensive analysis of what this means
- **Supporting Evidence**: All quotes and conversations in full
- **Strategic Opportunities**: Detailed potential business opportunities
- **Market Trends**: Comprehensive trend analysis
- **Revenue Implications**: Potential financial impact

## 🔧 Detailed Technical Insights & Solutions

For EACH technical discussion:
- **Complete Technical Details**: All technical information discussed
- **Platform Capabilities**: Detailed feature sets and capabilities
- **Integration Possibilities**: Comprehensive integration opportunities
- **Implementation Details**: How things actually work
- **Technical Challenges**: Problems and solutions discussed
- **Supporting Evidence**: All technical conversations in full
- **Future Opportunities**: Technical development possibilities

## 🖼️ Complete Media Documentation

For EACH media item:
- **Detailed Descriptions**: Complete descriptions of all media
- **Full Context**: Complete surrounding conversations
- **Business Relevance**: Detailed explanation of importance
- **Supporting Analysis**: How media supports key points
- **Technical Details**: Any technical aspects shown
- **Strategic Value**: Why this media matters

## ✅ Comprehensive Action Items & Next Steps

For EACH action item:
- **Complete Task Description**: Full details of what needs to be done
- **Detailed Context**: Why this is important and urgent
- **Full Contact Information**: Complete details for all people involved
- **Timeline & Deadlines**: All timing and urgency information
- **Success Criteria**: How to measure completion
- **Dependencies**: What needs to happen first
- **Resources Needed**: What's required to complete
- **Strategic Impact**: Why this matters for business

## 📞 Complete Contact Directory & Relationship Map

For EACH person mentioned:
- **Complete Profile**: Name, role, company, contact details
- **Relationship Context**: How we know them, interaction history
- **Business Value**: Why this relationship matters
- **Follow-up Strategy**: How to maintain and develop relationship
- **Company Intelligence**: Detailed company information
- **Collaboration Potential**: Specific partnership opportunities

## 🎯 Strategic Analysis & Recommendations

- **Key Themes**: Major patterns and themes from the conference
- **Strategic Priorities**: What should be prioritized based on learnings
- **Competitive Positioning**: How findings affect competitive position
- **Market Opportunities**: Detailed market opportunities identified
- **Risk Assessment**: Potential risks and challenges identified
- **Investment Implications**: What investments or resources are needed

## 📈 Detailed Conference ROI & Impact Assessment

- **Business Value Generated**: Quantifiable value from attendance
- **Strategic Insights Gained**: Key strategic intelligence
- **Relationship Value**: Value of new relationships and connections
- **Market Intelligence**: Competitive and market intelligence gained
- **Future Opportunities**: Pipeline opportunities identified

CRITICAL REQUIREMENTS:
- Include EVERY piece of information from the analysis with full detail
- Use extensive quotes and evidence for everything
- Provide comprehensive context and analysis
- Include ALL subcategories and their complete items
- Add detailed business and strategic analysis
- Include ALL timestamps, people, companies, and contact details
- Make it a comprehensive business intelligence report
- Provide actionable insights with full supporting evidence
- Include complete conversation excerpts where relevant
- Add strategic recommendations based on all findings

This should be a DETAILED COMPREHENSIVE REPORT, not a summary. Include everything with full context and analysis.

Return ONLY the detailed Markdown content.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192,
                temperature=0.1
            )
            
            markdown_content = response.choices[0].message.content
            
            # Save Markdown file
            md_path = output_path / "conference_summary.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Generated Markdown summary: {md_path}")
            return str(md_path)
            
        except Exception as e:
            self.logger.error(f"Error generating Markdown summary: {e}")
            # Generate a simple fallback Markdown
            return self._generate_fallback_markdown(analysis, output_path)
    
    def _generate_fallback_markdown(self, analysis: Dict[str, Any], output_path: Path) -> str:
        """Generate a simple fallback Markdown summary."""
        overview = analysis.get('conference_overview', {})
        sections = analysis.get('sections', [])
        action_items = analysis.get('action_items', [])
        media_refs = analysis.get('media_references', [])
        
        markdown_content = f"""# Conference Summary: {overview.get('name', 'Conference')}

## 📊 Overview
- **Total Messages**: {overview.get('total_messages', 'N/A')}
- **Attendees**: {len(overview.get('attendees', []))}
- **Key Topics**: {', '.join(overview.get('key_topics', []))}

### Attendees
{chr(10).join([f"- {attendee}" for attendee in overview.get('attendees', [])])}

## 📋 Conference Sections

"""
        
        for section in sections:
            markdown_content += f"### {section.get('title', 'Section')}\n"
            markdown_content += f"**Priority**: {section.get('priority', 'N/A')} | **Type**: {section.get('type', 'N/A')}\n\n"
            markdown_content += f"{section.get('description', '')}\n\n"
            
            key_points = section.get('content', {}).get('key_points', [])
            for point in key_points:
                markdown_content += f"#### {point.get('point', 'Point')}\n"
                if point.get('evidence'):
                    markdown_content += f"> {point.get('evidence', '')}\n\n"
                if point.get('timestamp'):
                    markdown_content += f"**Time**: {point.get('timestamp', '')}\n"
                if point.get('people'):
                    markdown_content += f"**People**: {', '.join(point.get('people', []))}\n"
                if point.get('companies'):
                    markdown_content += f"**Companies**: {', '.join(point.get('companies', []))}\n"
                markdown_content += "\n"
        
        if action_items:
            markdown_content += "## ✅ Action Items\n\n"
            for item in action_items:
                markdown_content += f"### {item.get('task', 'Task')}\n"
                markdown_content += f"- **Contact**: {item.get('person', '')}\n"
                markdown_content += f"- **Priority**: {item.get('priority', '').title()}\n"
                if item.get('deadline'):
                    markdown_content += f"- **Deadline**: {item.get('deadline', '')}\n"
                markdown_content += f"- **Context**: {item.get('context', '')}\n\n"
        
        if media_refs:
            markdown_content += "## 🖼️ Media Highlights\n\n"
            for media in media_refs:
                markdown_content += f"### {media.get('description', 'Media Item')}\n"
                markdown_content += f"- **Context**: {media.get('context', '')}\n"
                markdown_content += f"- **Relevance**: {media.get('relevance', '')}\n"
                if media.get('timestamp'):
                    markdown_content += f"- **Time**: {media.get('timestamp', '')}\n"
                markdown_content += "\n"
        
        # Save fallback Markdown file
        md_path = output_path / "conference_summary.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(md_path)


class ConferenceDashboardManager:
    """Main manager for generating conference dashboards."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        if config.openai_api_key:
            self.analyzer = ConferenceAnalyzer(config.openai_api_key)
        else:
            raise ValueError("OpenAI API key required for content analysis")
    
    def create_conference_dashboard(self, enhanced_chat_path: Path,
                                  media_folder: Path,
                                  output_folder: Path,
                                  conference_name: str = "Conference",
                                  generate_pdf: bool = True) -> Dict[str, str]:
        """
        Create a comprehensive conference summary in Markdown format and optionally PDF.
        
        Args:
            enhanced_chat_path: Path to enhanced chat file
            media_folder: Path to media files
            output_folder: Output directory
            conference_name: Name of the conference
            generate_pdf: Whether to generate PDF version
            
        Returns:
            Dictionary with paths to generated files
        """
        self.logger.info(f"Creating conference report for {conference_name}")
        
        # Read enhanced chat content
        with open(enhanced_chat_path, 'r', encoding='utf-8') as f:
            chat_content = f.read()
        
        # Analyze content with GPT-4o
        self.logger.info("Analyzing conference content...")
        analysis = self.analyzer.analyze_conference_content(chat_content, conference_name)
        
        # Save analysis as JSON for reference
        analysis_path = output_folder / f"{conference_name}_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Generate Markdown summary with OpenAI
        self.logger.info("Generating Markdown report...")
        markdown_path = self.analyzer.generate_markdown_summary(
            analysis, output_folder
        )
        
        self.logger.info(f"Conference report created successfully: {markdown_path}")
        
        result = {
            'markdown': markdown_path,
            'analysis': analysis_path
        }
        
        if generate_pdf:
            self.logger.info("Converting to PDF...")
            
            # Read the markdown content for PDF generation
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            pdf_output_path = output_folder / f"{conference_name.replace(' ', '_')}_report.pdf"
            pdf_success = self.generate_pdf_report(
                markdown_content, pdf_output_path, conference_name
            )
            if pdf_success:
                pdf_path = str(pdf_output_path)
                self.logger.info(f"PDF report generated: {pdf_path}")
                result['pdf'] = pdf_path
            else:
                self.logger.warning("PDF generation failed, but markdown report is available")
        
        return result

    def generate_pdf_report(self, markdown_content: str, output_path: Path, conference_name: str) -> bool:
        """
        Generate a professional PDF report from markdown content using markdown-pdf.
        
        Args:
            markdown_content: The markdown content to convert
            output_path: Path where the PDF should be saved
            conference_name: Name of the conference for document metadata
            
        Returns:
            bool: True if PDF was generated successfully, False otherwise
        """
        try:
            self.logger.info("Starting PDF generation with markdown-pdf library")
            
            # Create PDF with table of contents up to level 3 headings
            pdf = MarkdownPdf(toc_level=3, optimize=True)
            
            # Set document metadata
            pdf.meta["title"] = f"{conference_name} - Conference Analysis Report"
            pdf.meta["author"] = "WhatsApp Chat Notes Processor"
            pdf.meta["subject"] = "AI-Generated Conference Intelligence Report"
            pdf.meta["keywords"] = "conference, analysis, business intelligence, whatsapp"
            pdf.meta["creator"] = "WhatsApp Chat Notes - AI Assistant"
            
            # Split content into logical sections for better page breaks
            sections = self._split_markdown_into_sections(markdown_content)
            
            # Define professional CSS styling
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
                
                h4, h5, h6 {
                    color: #555;
                    margin-top: 15px;
                    margin-bottom: 8px;
                }
                
                p {
                    margin-bottom: 12px;
                    text-align: justify;
                }
                
                ul, ol {
                    margin-left: 25px;
                    margin-bottom: 15px;
                }
                
                li {
                    margin-bottom: 5px;
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
                
                em {
                    color: #555;
                }
                
                code {
                    background-color: #f1f2f6;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', monospace;
                    font-size: 0.9em;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                
                th {
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #2c3e50;
                }
                
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                .page-break {
                    page-break-before: always;
                }
            """
            
            # Add each section to the PDF
            for i, section_content in enumerate(sections):
                if i == 0:
                    # First section (title) - don't include in TOC and use portrait orientation
                    pdf.add_section(
                        Section(section_content, toc=False, paper_size="A4"),
                        user_css=css_styles
                    )
                else:
                    # Regular sections - include in TOC
                    pdf.add_section(
                        Section(section_content, paper_size="A4"),
                        user_css=css_styles
                    )
            
            # Save the PDF
            pdf.save(str(output_path))
            
            self.logger.info(f"PDF report generated successfully: {output_path}")
            return True
            
        except ImportError:
            self.logger.error("markdown-pdf library not installed. Install with: pip install markdown-pdf")
            return False
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            return False
    
    def _split_markdown_into_sections(self, content: str) -> List[str]:
        """
        Split markdown content into logical sections for better PDF page breaks.
        
        Args:
            content: The full markdown content
            
        Returns:
            List of markdown section strings
        """
        # Split by main headings (# headers)
        sections = []
        current_section = ""
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# ') and current_section.strip():
                # Start a new section
                sections.append(current_section.strip())
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        # Add the last section
        if current_section.strip():
            sections.append(current_section.strip())
        
        return sections if sections else [content]


def main():
    """Main function for testing dashboard generation."""
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python dashboard_generator.py <enhanced_chat_file> [media_folder] [output_folder]")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse arguments
    enhanced_chat_path = Path(sys.argv[1])
    media_folder = Path(sys.argv[2]) if len(sys.argv) > 2 else enhanced_chat_path.parent
    output_folder = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("output/dashboard")
    
    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    config = Config()
    
    # Create dashboard
    manager = ConferenceDashboardManager(config)
    summary_path = manager.create_conference_dashboard(
        enhanced_chat_path=enhanced_chat_path,
        media_folder=media_folder,
        output_folder=output_folder,
        conference_name="MAU Vegas 2025"
    )
    
    print(f"Conference summary generated: {summary_path}")


if __name__ == "__main__":
    main() 