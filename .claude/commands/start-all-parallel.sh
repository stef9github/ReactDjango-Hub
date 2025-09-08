#!/bin/bash
# Start all Claude Code instances in parallel using iTerm2 or Terminal tabs

echo "🚀 Starting All Parallel Claude Code Development Instances..."
echo "This will open multiple terminal tabs for parallel development:"
echo "  🔧 Backend Development (Django + RGPD)"
echo "  🎨 Frontend Development (React + French UI)"
echo "  🔌 API Development (REST + Docs)"

# Function to open new terminal tab and run command
open_terminal_tab() {
    local title=$1
    local command=$2
    
    # Use osascript to open new terminal tab
    osascript <<EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    do script "$command" in front window
    set custom title of front tab of front window to "$title"
end tell
EOF
}

# Open terminal tabs for each development instance
echo "Opening Backend Development tab..."
open_terminal_tab "Backend Dev" "cd /Users/stephanerichard/Documents/CODING/ReactDjango-Hub && bash .claude/commands/start-backend-dev.sh"

sleep 1

echo "Opening Frontend Development tab..."
open_terminal_tab "Frontend Dev" "cd /Users/stephanerichard/Documents/CODING/ReactDjango-Hub && bash .claude/commands/start-frontend-dev.sh"

sleep 1

echo "Opening API Development tab..."
open_terminal_tab "API Dev" "cd /Users/stephanerichard/Documents/CODING/ReactDjango-Hub && bash .claude/commands/start-api-dev.sh"

echo "✅ All parallel Claude Code instances started!"
echo "Switch between terminal tabs to work with different agents simultaneously."