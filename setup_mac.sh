#!/bin/bash

# Plugwise Data Collector Setup for macOS
# For testing and development

set -e

echo "🔌 Plugwise Data Collector - macOS Setup"
echo "=========================================="

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This script is designed for macOS"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Create data and logs directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p logs

# Copy example config if it doesn't exist
if [ ! -f config.json ]; then
    echo "📋 Copying example configuration..."
    cp config.example.json config.json
    echo "⚠️  Please edit config.json with your device credentials"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit configuration: nano config.json"
echo "2. Test the collector: source venv/bin/activate && python plugwise_collector.py --single"
echo "3. Run continuous collection: source venv/bin/activate && python plugwise_collector.py --continuous"
echo ""
echo "🔧 Virtual environment commands:"
echo "  Activate:   source venv/bin/activate"
echo "  Deactivate: deactivate"
echo "  Install:    pip install -r requirements.txt"
echo "" 