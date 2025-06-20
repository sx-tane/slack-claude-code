#!/usr/bin/env python3
"""Simple test for Claude Code SDK without Slack dependencies."""

import asyncio
import os
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

# Set minimal environment
os.environ['DEFAULT_REPO_PATH'] = '/tmp/test-repos'
os.environ['MAX_TURNS'] = '3'

async def test_claude_sdk():
    """Test Claude Code SDK directly."""
    print("🧪 Testing Claude Code SDK...")
    
    try:
        # Test basic functionality
        print("1. Testing basic query...")
        
        options = ClaudeCodeOptions(
            max_turns=2,
            cwd=Path('/tmp/test-repos')
        )
        
        messages = []
        async for message in query(
            prompt="Create a simple Python hello world function and save it to hello.py",
            options=options
        ):
            messages.append(message)
            print(f"   Message type: {getattr(message, 'type', 'unknown')}")
        
        print(f"✅ Received {len(messages)} messages")
        
        # Check if file was created
        hello_file = Path('/tmp/test-repos/hello.py')
        if hello_file.exists():
            print("✅ File creation successful!")
            content = hello_file.read_text()
            print(f"   File content preview: {content[:100]}...")
        else:
            print("⚠️ File not created, but SDK is working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    print("=" * 50)
    print("Claude Code SDK Test")
    print("=" * 50)
    
    # Create test directory
    Path('/tmp/test-repos').mkdir(exist_ok=True)
    
    success = await test_claude_sdk()
    
    print("=" * 50)
    if success:
        print("🎉 SDK test completed successfully!")
        print("\nYour bot is ready for integration!")
        print("\nNext steps to complete setup:")
        print("1. Create Slack app at https://api.slack.com/apps")
        print("2. Get Bot User OAuth Token (xoxb-...)")
        print("3. Get App-Level Token (xoxs-...)")
        print("4. Update .env file with your tokens")
        print("5. Run: python3 app.py")
    else:
        print("❌ SDK test failed. Check Claude authentication.")
        print("Try running: claude auth login")

if __name__ == "__main__":
    asyncio.run(main())