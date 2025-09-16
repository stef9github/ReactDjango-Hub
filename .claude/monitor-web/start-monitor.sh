#!/bin/bash

# Start Monitor Web Interface
# This script sets up and starts the Django monitoring web interface

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Agent Monitor Web Interface ===${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo -e "${YELLOW}Checking for superuser...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@monitor.local', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Initialize agents from configuration
echo -e "${YELLOW}Initializing agents...${NC}"
python manage.py init_agents

# Collect static files (for production)
# echo -e "${YELLOW}Collecting static files...${NC}"
# python manage.py collectstatic --noinput

# Start the development server
echo ""
echo -e "${GREEN}Starting monitor server...${NC}"
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Monitor URL: http://localhost:8888${NC}"
echo -e "${GREEN}Admin URL: http://localhost:8888/admin${NC}"
echo -e "${GREEN}Username: admin${NC}"
echo -e "${GREEN}Password: admin123${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Django development server
python manage.py runserver 0.0.0.0:8888