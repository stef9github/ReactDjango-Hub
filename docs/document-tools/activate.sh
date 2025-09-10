#!/bin/bash
# Document Tools Environment Activation Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     📚 Document Conversion Tools Environment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Show available tools
echo -e "${YELLOW}Available Commands:${NC}"
echo -e "  ${GREEN}python convert.py${NC} - Main conversion tool"
echo -e "  ${GREEN}python convert.py formats${NC} - List supported formats"
echo -e "  ${GREEN}python convert.py --help${NC} - Show all commands"
echo ""

echo -e "${YELLOW}Quick Examples:${NC}"
echo -e "  ${GREEN}python convert.py md2pdf input.md output.pdf${NC}"
echo -e "  ${GREEN}python convert.py pdf2text document.pdf text.txt${NC}"
echo -e "  ${GREEN}python convert.py merge-pdf output.pdf file1.pdf file2.pdf${NC}"
echo ""

echo -e "${YELLOW}Batch Operations:${NC}"
echo -e "  ${GREEN}python convert.py batch ./docs md pdf${NC}"
echo ""

# Check if all packages are installed
echo -e "${YELLOW}Checking installation status...${NC}"
python -c "
import sys
try:
    import weasyprint, reportlab, pypdf, markdown2, pypandoc
    import docx, pptx, openpyxl, xlsxwriter
    print('✅ All core packages installed successfully')
except ImportError as e:
    print(f'⚠️  Some packages may still be installing: {e}')
    print('   Run: pip install -r requirements.txt')
"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Ready to convert documents! Type 'deactivate' to exit.${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"