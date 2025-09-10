#!/usr/bin/env python3
"""
Generate Professional PDF from ChirurgieProX Markdown Files
Creates a comprehensive PDF document with proper formatting, tables, and styling
"""

import os
import re
from datetime import datetime
from pathlib import Path
import markdown2
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Configuration
INPUT_DIR = Path(__file__).parent
OUTPUT_FILE = INPUT_DIR / "ChirurgieProX_Complete_Documentation.pdf"

# Professional CSS styling for the PDF
PDF_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

@page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    max-width: 100%;
}

/* Headers */
h1 {
    color: #1e40af;
    font-size: 24pt;
    margin-top: 0;
    margin-bottom: 20pt;
    border-bottom: 3px solid #1e40af;
    padding-bottom: 10pt;
    page-break-after: avoid;
}

h2 {
    color: #1e3a8a;
    font-size: 18pt;
    margin-top: 24pt;
    margin-bottom: 12pt;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 6pt;
    page-break-after: avoid;
}

h3 {
    color: #334155;
    font-size: 14pt;
    margin-top: 18pt;
    margin-bottom: 8pt;
    font-weight: 600;
    page-break-after: avoid;
}

h4 {
    color: #475569;
    font-size: 12pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
    font-weight: 600;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16pt 0;
    page-break-inside: avoid;
    font-size: 10pt;
}

thead {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

th {
    padding: 10pt 8pt;
    text-align: left;
    font-weight: 600;
    border: 1px solid #e2e8f0;
}

td {
    padding: 8pt;
    border: 1px solid #e2e8f0;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background-color: #f8fafc;
}

tbody tr:hover {
    background-color: #f1f5f9;
}

/* Lists */
ul, ol {
    margin: 12pt 0;
    padding-left: 24pt;
}

li {
    margin: 4pt 0;
}

ul li::marker {
    color: #1e40af;
}

/* Code blocks */
code {
    background-color: #f1f5f9;
    padding: 2pt 4pt;
    border-radius: 3pt;
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    color: #0f172a;
}

pre {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 12pt;
    border-radius: 6pt;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    color: #e2e8f0;
    padding: 0;
}

/* Blockquotes */
blockquote {
    border-left: 4pt solid #1e40af;
    padding-left: 16pt;
    margin: 16pt 0;
    color: #475569;
    font-style: italic;
    background-color: #f8fafc;
    padding: 12pt 16pt;
    border-radius: 0 6pt 6pt 0;
}

/* Links */
a {
    color: #1e40af;
    text-decoration: none;
    border-bottom: 1px dotted #1e40af;
}

a:hover {
    color: #1e3a8a;
    border-bottom-style: solid;
}

/* Strong emphasis */
strong {
    color: #0f172a;
    font-weight: 600;
}

/* Page breaks */
.page-break {
    page-break-after: always;
}

/* Title page */
.title-page {
    text-align: center;
    padding: 100pt 0;
    page-break-after: always;
}

.title-page h1 {
    font-size: 36pt;
    border: none;
    margin-bottom: 24pt;
}

.subtitle {
    font-size: 18pt;
    color: #475569;
    margin-bottom: 48pt;
}

.metadata {
    font-size: 12pt;
    color: #64748b;
}

/* Table of contents */
.toc {
    page-break-after: always;
}

.toc h2 {
    color: #1e40af;
    border-bottom: 2px solid #1e40af;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    margin: 8pt 0;
    padding-left: 20pt;
}

.toc a {
    color: #334155;
    text-decoration: none;
    border: none;
}

.toc a:hover {
    color: #1e40af;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2pt 8pt;
    border-radius: 12pt;
    font-size: 9pt;
    font-weight: 600;
    margin: 0 4pt;
}

.badge-success {
    background-color: #10b981;
    color: white;
}

.badge-warning {
    background-color: #f59e0b;
    color: white;
}

.badge-info {
    background-color: #3b82f6;
    color: white;
}

.badge-danger {
    background-color: #ef4444;
    color: white;
}

/* Timeline styling */
.timeline {
    border-left: 3px solid #1e40af;
    padding-left: 20pt;
    margin: 20pt 0;
}

.timeline-item {
    position: relative;
    margin-bottom: 20pt;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -26pt;
    top: 0;
    width: 10pt;
    height: 10pt;
    border-radius: 50%;
    background-color: #1e40af;
    border: 2pt solid white;
}

/* Feature boxes */
.feature-box {
    border: 1px solid #e2e8f0;
    border-radius: 8pt;
    padding: 12pt;
    margin: 12pt 0;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.feature-box h3 {
    color: #1e40af;
    margin-top: 0;
}

/* Footer */
.footer {
    margin-top: 48pt;
    padding-top: 12pt;
    border-top: 1px solid #cbd5e1;
    font-size: 10pt;
    color: #64748b;
    text-align: center;
}
"""

def read_markdown_files():
    """Read all markdown files in the correct order"""
    files = [
        "ChirurgieProX_Business_Plan_Complete.md",
        "ChirurgieProX_Technical_Specifications.md",
        "ChirurgieProX_Go_To_Market_Strategy.md",
        "ChirurgieProX_Competitive_Analysis.md",
        "ChirurgieProX_Operational_Timeline_Complete.md",
        "ChirurgieProX_Risk_Analysis.md"
    ]
    
    content = []
    toc_entries = []
    
    for i, filename in enumerate(files):
        filepath = INPUT_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
                # Extract title from first H1
                title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1)
                    toc_entries.append((title, f"section-{i+1}"))
                
                # Add section anchor
                md_content = f'<div id="section-{i+1}">\n\n{md_content}\n\n</div>\n<div class="page-break"></div>'
                content.append(md_content)
    
    return '\n\n'.join(content), toc_entries

def create_title_page():
    """Create a professional title page"""
    return f"""
    <div class="title-page">
        <h1>ChirurgieProX</h1>
        <div class="subtitle">Complete Business & Technical Documentation</div>
        <div class="metadata">
            <p><strong>Version:</strong> 1.0</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            <p><strong>Status:</strong> <span class="badge badge-success">Final</span></p>
        </div>
    </div>
    """

def create_table_of_contents(toc_entries):
    """Create table of contents"""
    toc_html = '<div class="toc"><h2>Table of Contents</h2><ul>'
    for title, anchor in toc_entries:
        toc_html += f'<li><a href="#{anchor}">{title}</a></li>'
    toc_html += '</ul></div>'
    return toc_html

def enhance_markdown_content(content):
    """Enhance markdown content with better formatting"""
    # Convert markdown to HTML with tables support
    html = markdown2.markdown(content, extras=[
        'tables', 
        'fenced-code-blocks', 
        'header-ids',
        'strike',
        'task_list',
        'footnotes'
    ])
    
    # Enhance tables with better styling
    html = re.sub(r'<table>', '<table class="data-table">', html)
    
    # Add timeline styling for dates
    html = re.sub(r'(\d{4}-\d{2}-\d{2})', r'<span class="timeline-date">\1</span>', html)
    
    # Enhance lists with icons
    html = re.sub(r'<li>✅', '<li class="check">', html)
    html = re.sub(r'<li>❌', '<li class="cross">', html)
    html = re.sub(r'<li>⚠️', '<li class="warning">', html)
    
    return html

def generate_pdf():
    """Generate the PDF document"""
    print("📚 Reading markdown files...")
    markdown_content, toc_entries = read_markdown_files()
    
    print("🎨 Creating styled HTML...")
    # Create full HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ChirurgieProX Documentation</title>
        <style>{PDF_STYLE}</style>
    </head>
    <body>
        {create_title_page()}
        {create_table_of_contents(toc_entries)}
        {enhance_markdown_content(markdown_content)}
        <div class="footer">
            <p>© 2025 ChirurgieProX - Confidential Business Documentation</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>
    </body>
    </html>
    """
    
    print("🔧 Generating PDF...")
    # Configure fonts
    font_config = FontConfiguration()
    
    # Generate PDF
    HTML(string=html_content).write_pdf(
        OUTPUT_FILE,
        stylesheets=[CSS(string=PDF_STYLE, font_config=font_config)],
        font_config=font_config
    )
    
    print(f"✅ PDF generated successfully: {OUTPUT_FILE}")
    print(f"📄 File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    try:
        generate_pdf()
    except ImportError as e:
        print(f"⚠️  Missing required package: {e}")
        print("Installing required packages...")
        import subprocess
        subprocess.run(["pip3", "install", "markdown2", "weasyprint"], check=True)
        print("Packages installed. Running PDF generation...")
        generate_pdf()