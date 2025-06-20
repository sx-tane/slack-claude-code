#!/bin/bash

# Claude Code Slack Bot Setup Script
# This script helps you set up the bot quickly

set -e

echo "🚀 Claude Code Slack Bot Setup"
echo "================================="

# Check Python version
echo "📋 Checking Python version..."
if ! python3 --version | grep -E "3\.(10|11|12)"; then
    echo "❌ Python 3.10+ required. Please install Python 3.10 or higher."
    exit 1
fi
echo "✅ Python version OK"

# Check Node.js
echo "📋 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi
echo "✅ Node.js found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Claude CLI
echo "🤖 Installing Claude CLI..."
if ! command -v claude &> /dev/null; then
    npm install -g @anthropic-ai/claude-code
    echo "✅ Claude CLI installed"
else
    echo "✅ Claude CLI already installed"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created from template"
    echo ""
    echo "🔧 IMPORTANT: Edit .env file with your tokens:"
    echo "   - SLACK_BOT_TOKEN=xoxb-your-bot-token"
    echo "   - SLACK_APP_TOKEN=xapp-your-app-token" 
    echo "   - GITHUB_TOKEN=your-github-token"
    echo "   - Update repository paths"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Create workspace directory
echo "📁 Creating workspace directory..."
mkdir -p /tmp/claude-workspace
echo "✅ Workspace directory created"

# Test configuration
echo "🧪 Testing configuration..."
if python3 -c "from config import *; print('Configuration loaded successfully')" 2>/dev/null; then
    echo "✅ Configuration test passed"
else
    echo "⚠️ Configuration test failed - please check your .env file"
fi

# Claude authentication check
echo "🔐 Checking Claude authentication..."
if claude auth status 2>/dev/null | grep -q "authenticated\|Authenticated"; then
    echo "✅ Claude authentication OK"
else
    echo "⚠️ Claude not authenticated. Run: claude auth login"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Slack tokens"
echo "2. Authenticate Claude: claude auth login"
echo "3. Start the bot: python3 app.py"
echo ""
echo "For full setup instructions, see README.md"