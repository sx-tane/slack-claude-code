"""Configuration management for Slack-Claude Code bot."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Required environment variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')

# Optional configurations
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL')
CLAUDE_WORKSPACE = os.getenv('CLAUDE_WORKSPACE', '/tmp/claude-workspace')
MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '3000'))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# GitHub integration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DEFAULT_REPO_PATH = os.getenv('DEFAULT_REPO_PATH', '/tmp/repos')

# Multiple repository configuration
REPO_PATHS = {
    'default': os.getenv('DEFAULT_REPO_PATH', '/tmp/repos'),
    'repo1': os.getenv('REPO1_PATH', ''),
    'repo2': os.getenv('REPO2_PATH', ''),
    'repo3': os.getenv('REPO3_PATH', ''),
    'repo4': os.getenv('REPO4_PATH', ''),
    'repo5': os.getenv('REPO5_PATH', ''),
}

# Repository aliases (can be customized via env)
REPO_ALIASES = {
    os.getenv('REPO1_NAME', 'project1').lower(): 'repo1',
    os.getenv('REPO2_NAME', 'project2').lower(): 'repo2', 
    os.getenv('REPO3_NAME', 'project3').lower(): 'repo3',
    os.getenv('REPO4_NAME', 'project4').lower(): 'repo4',
    os.getenv('REPO5_NAME', 'project5').lower(): 'repo5',
}

# Claude Code SDK settings
MAX_TURNS = int(os.getenv('MAX_TURNS', '8'))  # Increased default
OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'json')
MCP_CONFIG_PATH = os.getenv('MCP_CONFIG_PATH', 'mcp-config.json')

# Logging configuration
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('slack-claude-bot.log')
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('slack_sdk').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def validate_config():
    """Validate required configuration."""
    errors = []
    
    if not SLACK_BOT_TOKEN:
        errors.append("SLACK_BOT_TOKEN is required")
    
    if not SLACK_APP_TOKEN:
        errors.append("SLACK_APP_TOKEN is required")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease copy .env.example to .env and fill in the required values.")
        sys.exit(1)

def setup_workspace():
    """Create workspace directory if it doesn't exist."""
    workspace = Path(CLAUDE_WORKSPACE)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace

# Run validation on import
validate_config()
logger = setup_logging()