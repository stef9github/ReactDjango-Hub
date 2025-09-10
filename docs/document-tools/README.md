# 📚 Document Conversion Tools

A comprehensive suite of document conversion tools with support for multiple formats including PDF, Word, Excel, Markdown, HTML, and more.

## 🚀 Quick Start

```bash
# Activate the environment
source activate.sh

# Or manually activate
source venv/bin/activate

# Check available commands
python convert.py --help

# List supported formats
python convert.py formats
```

## 📦 Installed Tools

### Core Conversion Libraries
- **WeasyPrint** - HTML/CSS to PDF conversion with excellent styling
- **ReportLab** - Professional PDF generation with charts and graphics
- **PyPDF** - PDF manipulation (merge, split, rotate, encrypt)
- **PDFPlumber** - PDF text and table extraction
- **Camelot** - Advanced table extraction from PDFs

### Document Format Support
- **Markdown** - Multiple parsers (markdown2, mistune, markdown-it-py)
- **Pandoc** - Universal document converter (via pypandoc)
- **python-docx** - Word document creation and manipulation
- **python-pptx** - PowerPoint presentation handling
- **OpenPyXL & XlsxWriter** - Excel file processing
- **BeautifulSoup & lxml** - HTML/XML processing

### Visualization & Graphics
- **Matplotlib & Seaborn** - Charts and graphs for reports
- **Plotly** - Interactive visualizations
- **Pillow** - Image processing
- **CairoSVG** - SVG to PNG/PDF conversion

### Documentation Generation
- **Sphinx** - Professional documentation generation
- **MkDocs** - Project documentation with Material theme
- **Jinja2** - Template engine for document generation

## 🔧 Available Commands

### Markdown Conversions
```bash
# Markdown to PDF
python convert.py md2pdf input.md output.pdf

# Markdown to PDF with custom CSS
python convert.py md2pdf input.md output.pdf --style custom.css

# Markdown to Word Document
python convert.py md2docx input.md output.docx
```

### PDF Operations
```bash
# Extract text from PDF
python convert.py pdf2text document.pdf extracted.txt

# Extract tables from PDF to CSV
python convert.py pdf2tables document.pdf ./output_dir/

# Merge multiple PDFs
python convert.py merge-pdf merged.pdf file1.pdf file2.pdf file3.pdf
```

### Excel/CSV Operations
```bash
# Convert Excel to CSV (creates one CSV per sheet)
python convert.py excel2csv spreadsheet.xlsx output.csv
```

### Image Conversions
```bash
# Convert SVG to PNG
python convert.py svg2png image.svg output.png --width 1920 --height 1080
```

### Batch Operations
```bash
# Convert all markdown files in a directory to PDF
python convert.py batch ./docs md pdf

# Convert all Excel files to CSV
python convert.py batch ./data xlsx csv
```

## 📝 Python API Usage

```python
from convert import DocumentConverter

# Initialize converter
converter = DocumentConverter("input.md", "output.pdf")

# Convert markdown to PDF with custom styling
converter.convert_markdown_to_pdf(style_file="custom.css")

# Extract text from PDF
converter = DocumentConverter("document.pdf", "text.txt")
converter.convert_pdf_to_text()

# Merge PDFs
converter = DocumentConverter("dummy", "merged.pdf")
converter.merge_pdfs(["file1.pdf", "file2.pdf", "file3.pdf"])
```

## 🎨 Custom PDF Styling

Create a CSS file for custom PDF styling:

```css
/* custom-style.css */
@page {
    size: A4;
    margin: 2.5cm;
}

body {
    font-family: 'Georgia', serif;
    font-size: 12pt;
    line-height: 1.8;
}

h1 {
    color: #2c3e50;
    font-size: 24pt;
    border-bottom: 3px solid #3498db;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background-color: #3498db;
    color: white;
    padding: 10px;
}
```

Use with: `python convert.py md2pdf input.md output.pdf --style custom-style.css`

## 📊 Supported Conversions

| Source Format | Target Formats |
|--------------|----------------|
| **Markdown** | HTML, PDF, DOCX, LaTeX, RST, EPUB |
| **HTML** | PDF, Markdown, DOCX, Text |
| **PDF** | Text, HTML, Images, Tables (CSV) |
| **Word (DOCX)** | PDF, HTML, Markdown, Text |
| **Excel** | CSV, HTML, PDF |
| **CSV** | Excel, HTML, Markdown |
| **YAML** | JSON, TOML, XML |
| **JSON** | YAML, TOML, XML |
| **SVG** | PNG, PDF, JPG |
| **Images** | PDF, Resize, Format Change |

## 🛠️ Advanced Features

### Document Generation with Templates

```python
from jinja2 import Template
import markdown2
from weasyprint import HTML

# Create template
template = Template("""
# {{ title }}

Generated on: {{ date }}

## Summary
{{ summary }}

## Data
| Name | Value |
|------|-------|
{% for item in data %}
| {{ item.name }} | {{ item.value }} |
{% endfor %}
""")

# Render with data
content = template.render(
    title="Monthly Report",
    date="2025-09-10",
    summary="This month's performance metrics",
    data=[
        {"name": "Sales", "value": "$100,000"},
        {"name": "Growth", "value": "15%"}
    ]
)

# Convert to PDF
html = markdown2.markdown(content, extras=['tables'])
HTML(string=html).write_pdf("report.pdf")
```

### Batch Processing with Progress

```python
from pathlib import Path
from tqdm import tqdm

files = list(Path("./docs").glob("*.md"))

for file in tqdm(files, desc="Converting files"):
    converter = DocumentConverter(file, file.with_suffix(".pdf"))
    converter.convert_markdown_to_pdf()
```

## 🔍 Troubleshooting

### Missing Pandoc
If pypandoc operations fail:
```bash
# macOS
brew install pandoc

# Linux
sudo apt-get install pandoc

# Or download from: https://pandoc.org/installing.html
```

### WeasyPrint Issues
For font or rendering issues:
```bash
# Install system dependencies
brew install cairo pango gdk-pixbuf libffi
```

### Large File Processing
For large PDFs or batch operations:
```python
# Use memory-efficient processing
import gc

for file in large_files:
    process_file(file)
    gc.collect()  # Force garbage collection
```

## 📚 Additional Resources

- [WeasyPrint Documentation](https://weasyprint.org/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Pandoc Manual](https://pandoc.org/MANUAL.html)
- [Python-docx Documentation](https://python-docx.readthedocs.io/)
- [PDFPlumber Documentation](https://github.com/jsvine/pdfplumber)

## 🤝 Contributing

To add new conversion formats:

1. Add the conversion method to `DocumentConverter` class
2. Create a CLI command using `@cli.command()`
3. Update `SUPPORTED_CONVERSIONS` dictionary
4. Add tests and documentation

## 📄 License

This tool collection is part of the ReactDjango-Hub project.