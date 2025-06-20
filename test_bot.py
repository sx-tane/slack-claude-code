#!/usr/bin/env python3
"""Test script to verify Slack-Claude Code bot configuration."""

import asyncio
import subprocess
import sys
from pathlib import Path

try:
    from slack_sdk.web.async_client import AsyncWebClient
    from slack_sdk.errors import SlackApiError
    from dotenv import load_dotenv
    import os
except ImportError:
    print("Error: Dependencies not installed. Run: python setup.py")
    sys.exit(1)

# Load environment variables
load_dotenv()

async def test_slack_connection():
    """Test Slack API connection."""
    print("\n1. Testing Slack connection...")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    app_token = os.getenv('SLACK_APP_TOKEN')
    
    if not bot_token or not app_token:
        print("✗ Missing Slack credentials in .env file")
        return False
    
    print("  - Bot token: " + ("✓" if bot_token.startswith("xoxb-") else "✗ Invalid format"))
    print("  - App token: " + ("✓" if app_token.startswith("xapp-") else "✗ Invalid format"))
    
    # Test bot token
    client = AsyncWebClient(token=bot_token)
    try:
        response = await client.auth_test()
        print(f"✓ Connected as: {response['user']} in team: {response['team']}")
        
        # Test permissions
        print("\n2. Testing bot permissions...")
        perms = await client.auth_test()
        print("✓ Bot has basic permissions")
        
        return True
    except SlackApiError as e:
        print(f"✗ Slack API error: {e.response['error']}")
        if e.response['error'] == 'invalid_auth':
            print("  Check your SLACK_BOT_TOKEN in .env")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_claude_cli():
    """Test Claude CLI functionality."""
    print("\n3. Testing Claude CLI...")
    
    try:
        # Test basic command
        result = subprocess.run(
            ["claude", "-p", "Say 'test successful' and nothing else"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"✓ Claude CLI working: {output[:50]}...")
            return True
        else:
            print(f"✗ Claude CLI error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Claude CLI timed out")
        return False
    except FileNotFoundError:
        print("✗ Claude CLI not found in PATH")
        print("  Install with: npm install -g @anthropic-ai/claude-code")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_workspace():
    """Test workspace directory."""
    print("\n4. Testing workspace setup...")
    
    workspace = os.getenv('CLAUDE_WORKSPACE', '/tmp/claude-workspace')
    workspace_path = Path(workspace)
    
    try:
        workspace_path.mkdir(parents=True, exist_ok=True)
        test_file = workspace_path / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print(f"✓ Workspace directory writable: {workspace}")
        return True
    except Exception as e:
        print(f"✗ Workspace error: {e}")
        return False

async def main():
    """Run all tests."""
    print("Slack-Claude Code Bot Configuration Test")
    print("=" * 50)
    
    # Run tests
    slack_ok = await test_slack_connection()
    claude_ok = test_claude_cli()
    workspace_ok = test_workspace()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Slack connection: {'✓ PASS' if slack_ok else '✗ FAIL'}")
    print(f"  Claude CLI:       {'✓ PASS' if claude_ok else '✗ FAIL'}")
    print(f"  Workspace:        {'✓ PASS' if workspace_ok else '✗ FAIL'}")
    
    if all([slack_ok, claude_ok, workspace_ok]):
        print("\n✓ All tests passed! You can now run: python app.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)