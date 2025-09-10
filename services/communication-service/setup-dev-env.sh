#!/bin/bash

# ====================================
# Communication Service Development Environment Setup
# ====================================
# This script sets up a Python virtual environment for local development
# and testing when system Python is externally managed.
#
# Usage: ./setup-dev-env.sh
#
# Created by: Communication Agent
# Last Updated: 2025-09-10

set -e  # Exit on any error

echo "🧪 Communication Service - Development Environment Setup"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the communication-service directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔄 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "🔄 Installing production dependencies..."
pip install -r requirements-standalone.txt

# Install test dependencies
echo "🔄 Installing test dependencies..."
pip install -r test_requirements.txt

# Verify installation
echo "🔄 Verifying installation..."
python -c "import fastapi, sqlalchemy, celery, psutil; print('✅ Core dependencies imported successfully')"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment in future sessions, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python run_tests.py"
echo ""
echo "To start the service:"
echo "  python main.py"
echo ""
echo "To deactivate the environment:"
echo "  deactivate"