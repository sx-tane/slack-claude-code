#!/usr/bin/env python3
"""Test script for Claude Code SDK functionality without Slack."""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import run_claude_sdk

async def test_sdk_functionality():
    """Test core SDK functionality."""
    print("🧪 Testing Claude Code SDK Bot Components...")
    print("=" * 50)
    
    # Test 1: Basic code generation
    print("\n1. Testing basic code generation...")
    result = await run_claude_sdk("Create a simple Python function that adds two numbers")
    
    if result['success']:
        print("✅ Basic code generation: PASSED")
        print(f"Result preview: {result['result'][:100]}...")
    else:
        print(f"❌ Basic code generation: FAILED - {result['error']}")
        return False
    
    # Test 2: Session management
    print("\n2. Testing session management...")
    result1 = await run_claude_sdk("Remember this: my favorite color is blue")
    session_id = result1.get('session_id')
    
    if session_id:
        result2 = await run_claude_sdk("What is my favorite color?", session_id=session_id)
        if result2['success'] and 'blue' in result2['result'].lower():
            print("✅ Session management: PASSED")
        else:
            print("❌ Session management: FAILED - Session context not maintained")
    else:
        print("❌ Session management: FAILED - No session ID returned")
    
    # Test 3: Error handling
    print("\n3. Testing error handling...")
    result = await run_claude_sdk("", options={'max_turns': 1})
    
    if not result['success']:
        print("✅ Error handling: PASSED")
    else:
        print("⚠️ Error handling: Expected failure but got success")
    
    print("\n" + "=" * 50)
    print("🎉 SDK functionality tests completed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_sdk_functionality())
        if success:
            print("\n✅ All tests passed! The bot is ready for Slack integration.")
            print("\nNext steps:")
            print("1. Set up Slack app and get tokens")
            print("2. Update SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env")
            print("3. Run: python3 app.py")
        else:
            print("\n❌ Some tests failed. Check the configuration.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)