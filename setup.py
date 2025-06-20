#!/usr/bin/env python3
"""Setup script for Slack-Claude Code bot."""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Ensure Python 3.8+ is being used."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required Python packages."""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        sys.exit(1)

def check_claude_cli():
    """Verify Claude CLI is installed."""
    print("\nChecking Claude CLI...")
    if shutil.which("claude"):
        try:
            result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
            print(f"✓ Claude CLI found: {result.stdout.strip()}")
        except:
            print("✓ Claude CLI found")
    else:
        print("✗ Claude CLI not found in PATH")
        print("\nPlease install Claude Code CLI:")
        print("  npm install -g @anthropic-ai/claude-code")
        print("\nOr follow the installation guide at:")
        print("  https://github.com/anthropics/claude-code")
        sys.exit(1)

def setup_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✓ .env file created")
        print("\n⚠️  IMPORTANT: Edit .env and add your Slack credentials:")
        print("  - SLACK_BOT_TOKEN")
        print("  - SLACK_APP_TOKEN")
        return False
    elif env_file.exists():
        print("\n✓ .env file exists")
        return True
    else:
        print("\n✗ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories."""
    dirs = ["logs", "claude-workspace"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✓ Created necessary directories")

def main():
    """Run the setup process."""
    print("Setting up Slack-Claude Code Bot")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Check Claude CLI
    check_claude_cli()
    
    # Create directories
    create_directories()
    
    # Setup environment file
    env_configured = setup_env_file()
    
    print("\n" + "=" * 40)
    print("Setup complete!")
    
    if not env_configured:
        print("\nNext steps:")
        print("1. Edit .env file with your Slack credentials")
        print("2. Create a Slack app at https://api.slack.com/apps")
        print("3. Run: python test_bot.py")
        print("4. Start the bot: python app.py")
    else:
        print("\nYou can now run:")
        print("  python test_bot.py  # Test configuration")
        print("  python app.py       # Start the bot")
    
    print("\nFor detailed instructions, see README.md")

if __name__ == "__main__":
    main()