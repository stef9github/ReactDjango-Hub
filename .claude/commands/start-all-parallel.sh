#!/bin/bash
# Start all Claude Code instances in parallel using iTerm2 or Terminal tabs

echo "🚀 Starting All Parallel Claude Code Development Instances..."
echo "This will open multiple terminal tabs for parallel development:"
echo "  🔧 Backend + API Development (Django + REST + RGPD)"
echo "  🎨 Frontend Development (React + French UI)"

# Function to open new terminal tab and run command
open_terminal_tab() {
    local title=$1
    local command=$2
    
    # Check if iTerm2 is available (better color support)
    if osascript -e 'tell application "System Events" to (name of processes) contains "iTerm2"' 2>/dev/null || [ -d "/Applications/iTerm.app" ]; then
        # Use iTerm2
        osascript <<EOF
tell application "iTerm2"
    activate
    tell current window
        create tab with default profile
        tell current session of current tab
            write text "export TERM=xterm-256color CLICOLOR=1; $command"
            set name to "$title"
        end tell
    end tell
end tell
EOF
    else
        # Fallback to Terminal.app with better color handling
        osascript <<EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "export TERM=xterm-256color CLICOLOR=1; $command" in front window
    set custom title of front tab of front window to "$title"
    try
        set background color of front tab of front window to {0, 0, 0}
        set normal text color of front tab of front window to {65535, 65535, 65535}
    end try
end tell
EOF
    fi
}

# Open terminal tabs for each development instance
echo "Opening Backend + API Development tab..."
open_terminal_tab "Backend + API Dev" "cd /Users/stephanerichard/Documents/CODING/ReactDjango-Hub && bash .claude/commands/start-backend-dev.sh"

sleep 1

echo "Opening Frontend Development tab..."
open_terminal_tab "Frontend Dev" "cd /Users/stephanerichard/Documents/CODING/ReactDjango-Hub && bash .claude/commands/start-frontend-dev.sh"

echo "✅ All parallel Claude Code instances started!"
echo "Switch between terminal tabs to work with different agents simultaneously."