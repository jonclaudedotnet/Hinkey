#!/bin/bash

# Dolores Control Panel Launcher
# Run this script to start the comprehensive Dolores control panel

echo "🚀 Starting Dolores Control Panel..."
echo "=================================="

# Check for required dependencies
echo "Checking dependencies..."

python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ tkinter not available"
    echo "Installing tkinter..."
    sudo dnf install -y python3-tkinter || sudo apt-get install -y python3-tk
}

python3 -c "import psutil" 2>/dev/null || {
    echo "❌ psutil not available"
    echo "Installing psutil..."
    pip3 install psutil
}

# Check for config file
if [ ! -f "config.json" ]; then
    echo "⚠️  No config.json found"
    echo "Creating template config.json..."
    cat > config.json << EOF
{
    "deepseek_api_key": "YOUR_API_KEY_HERE"
}
EOF
    echo "Please edit config.json with your DeepSeek API key"
fi

# Check for database
if [ ! -f "./dolores_knowledge/dolores_memory.db" ]; then
    echo "🔧 Initializing database..."
    python3 -c "from dolores_core import DoloresMemory; DoloresMemory()"
fi

echo "✅ All dependencies ready"
echo ""
echo "🎯 Launching Dolores Control Panel..."
echo ""

# Launch the control panel
python3 dolores_control_panel.py

echo ""
echo "👋 Dolores Control Panel closed"