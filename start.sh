#!/bin/bash
# Quick start script for Slack-Claude Code Bot

echo "Starting Slack-Claude Code Bot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and add your credentials."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import slack_sdk" 2>/dev/null; then
    echo "Dependencies not installed. Running setup..."
    python3 setup.py
fi

# Start the bot
echo "Starting bot..."
python3 app.py