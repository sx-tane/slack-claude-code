#!/usr/bin/env python3
"""Slack bot that integrates with Claude Code SDK for advanced coding assistance."""

import asyncio
import json
import re
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Claude Code SDK imports
import anyio
from claude_code_sdk import query, ClaudeCodeOptions, Message

from config import (
    SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_MODEL,
    MAX_MESSAGE_LENGTH, GITHUB_TOKEN, DEFAULT_REPO_PATH,
    MAX_TURNS, OUTPUT_FORMAT, MCP_CONFIG_PATH,
    REPO_PATHS, REPO_ALIASES,
    setup_workspace, logger
)

# Initialize Slack clients (will be set in main)
web_client = None
socket_client = None
bot_user_id = None

# Session storage for conversation management
active_sessions: Dict[str, str] = {}

# Help message with new features
HELP_MESSAGE = """
*Claude Code SDK Bot - Help*

I'm an advanced bot that uses Claude Code SDK with GitHub integration. Here's how to use me:

*Commands:*
• `@ClaudeCode <your request>` - Mention me in any channel
• Send me a direct message
• `/code <request>` - General coding tasks
• `/feature <description>` - Create new features with PR
• `/review <target>` - Code review (PR, files, directories)
• `/fix <issue>` - Bug fixing with automated commits
• `/pr <description>` - Create pull request from current changes

*Examples:*
• `@ClaudeCode create a React login component with TypeScript`
• `/code add authentication to tourii project`
• `/code fix the API in kkg_booking_record`
• `/feature user authentication system with JWT`
• `/review PR #123 for security issues`
• `/pr implement user profile management`

*Project Selection:*
• **Default**: Works in `/home/sx/tourii`
• **Auto-detect**: Mention project name in command
  - `tourii` → `/home/sx/tourii`
  - `kkg_booking` → `/home/sx/kkg_booking_record`
  - `slack-claude-code` → `/home/sx/slack-claude-code`

*Advanced Features:*
• GitHub integration for PR creation
• Session management for multi-turn conversations
• Code review with security analysis
• Automated testing and deployment preparation
• Multi-project repository management

*Tips:*
• I maintain conversation context across messages
• I can work with your GitHub repositories directly
• Long responses are uploaded as files
• I format code blocks automatically
"""

async def run_claude_sdk(
    prompt: str,
    options: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Execute Claude Code using the official SDK."""
    try:
        # Set up default options
        repo_path = working_dir or DEFAULT_REPO_PATH
        default_options = {
            'max_turns': MAX_TURNS,
            'cwd': str(Path(repo_path))  # Convert to string
        }
        
        # Override with provided options
        if options:
            default_options.update(options)
        
        # Add model if specified
        if ANTHROPIC_MODEL:
            default_options['model'] = ANTHROPIC_MODEL
            
        # Add session management
        if session_id:
            default_options['resume'] = session_id

        try:
            claude_options = ClaudeCodeOptions(**default_options)
        except TypeError as e:
            logger.error(f"ClaudeCodeOptions error: {e}")
            # Fallback to minimal options
            claude_options = ClaudeCodeOptions(
                max_turns=default_options.get('max_turns', MAX_TURNS)
            )
        
        logger.info(f"Running Claude SDK with prompt: {prompt[:100]}...")
        logger.debug(f"Options: {default_options}")
        
        messages: List[Message] = []
        
        # Use the SDK's query function with proper error handling
        try:
            async for message in query(
                prompt=prompt,
                options=claude_options
            ):
                messages.append(message)
                logger.debug(f"Received message: {message}")
        except Exception as query_error:
            logger.error(f"Query error: {query_error}")
            # Handle JSON decode errors gracefully
            if "JSONDecodeError" in str(query_error) or "TaskGroup" in str(query_error):
                # The task may have partially completed, check what we have
                if messages:
                    logger.warning("Task interrupted due to JSON parsing error, but we have partial results")
                    # Continue with what we have
                else:
                    # Completely failed, try fallback to CLI
                    logger.info("Attempting fallback to Claude CLI directly")
                    try:
                        import subprocess
                        import json as json_module
                        
                        # Build CLI command
                        cli_cmd = [
                            "claude", "-p", prompt,
                            "--output-format", "json",
                            "--max-turns", str(default_options.get('max_turns', MAX_TURNS))
                        ]
                        
                        if default_options.get('cwd'):
                            # Change to the working directory
                            result_proc = subprocess.run(
                                cli_cmd,
                                cwd=default_options['cwd'],
                                capture_output=True,
                                text=True,
                                timeout=300  # 5 minute timeout
                            )
                        else:
                            result_proc = subprocess.run(
                                cli_cmd,
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                        
                        if result_proc.returncode == 0:
                            # Try to parse JSON response
                            try:
                                cli_result = json_module.loads(result_proc.stdout)
                                return {
                                    'success': True,
                                    'result': cli_result.get('result', result_proc.stdout),
                                    'messages': [],
                                    'session_id': None,
                                    'cost': 0.0
                                }
                            except json_module.JSONDecodeError:
                                # Use raw output
                                return {
                                    'success': True,
                                    'result': result_proc.stdout,
                                    'messages': [],
                                    'session_id': None,
                                    'cost': 0.0
                                }
                        else:
                            raise RuntimeError(f"CLI fallback failed: {result_proc.stderr}")
                            
                    except Exception as cli_error:
                        logger.error(f"CLI fallback also failed: {cli_error}")
                        raise RuntimeError("Both SDK and CLI failed. Try breaking your request into smaller, more specific parts.")
            else:
                raise
        
        # Extract the final result
        result_text = ""
        session_id = None
        total_cost = 0.0
        assistant_responses = []
        
        for msg in messages:
            if hasattr(msg, 'subtype'):
                if msg.subtype in ['success', 'error_max_turns']:
                    session_id = getattr(msg, 'session_id', None)
                    total_cost = getattr(msg, 'total_cost_usd', 0.0)
                    result_text = getattr(msg, 'result', None)
            elif hasattr(msg, 'content'):
                # Extract text from assistant messages
                for content_item in msg.content:
                    if hasattr(content_item, 'text'):
                        assistant_responses.append(content_item.text)
        
        # If no final result but we have assistant responses, combine them
        if not result_text and assistant_responses:
            result_text = "\n\n".join(assistant_responses)
            
        # If we hit max turns, add a note about continuation
        if not result_text or len(result_text.strip()) < 50:
            if assistant_responses:
                result_text = "\n\n".join(assistant_responses)
                result_text += "\n\n⚠️ **Analysis incomplete** - Hit maximum turn limit. The task was complex and may need continuation. Use the same command again to continue the analysis, or try breaking it into smaller parts."
            else:
                result_text = "⚠️ **Task interrupted** - The analysis hit the maximum turn limit before completion. Try breaking the request into smaller, more specific parts or use a more focused query."
        
        return {
            'success': True,
            'result': result_text.strip(),
            'messages': messages,
            'session_id': session_id,
            'cost': total_cost
        }
        
    except Exception as e:
        logger.exception("Error running Claude SDK")
        error_message = str(e)
        
        # Provide more user-friendly error messages
        if "TaskGroup" in error_message or "JSONDecodeError" in error_message:
            error_message = "⚠️ Claude encountered a parsing error with complex output. This often happens with very large responses. Try:\n\n• Breaking your request into smaller parts\n• Being more specific about what you want\n• Using a simpler query format"
        elif "cwd" in error_message:
            error_message = f"Working directory issue. Please check {DEFAULT_REPO_PATH} exists."
        elif "timeout" in error_message.lower():
            error_message = "⏱️ Task timed out. Try breaking it into smaller parts or being more specific."
        elif "parsing error" in error_message:
            error_message = "🔧 Try using a more focused request or breaking complex tasks into steps."
        
        return {
            'success': False,
            'error': error_message,
            'result': error_message
        }

def format_code_blocks(text: str) -> str:
    """Format code blocks for Slack markdown."""
    # Replace markdown code blocks with Slack format
    text = re.sub(r'```(\w+)?\n(.*?)```', r'```\2```', text, flags=re.DOTALL)
    return text

async def send_response(
    channel: str, 
    text: str, 
    thread_ts: Optional[str] = None,
    blocks: Optional[List[Dict]] = None
) -> None:
    """Send a response to Slack, handling long messages."""
    # Format code blocks
    formatted_text = format_code_blocks(text)
    
    # Check message length
    if len(formatted_text) > MAX_MESSAGE_LENGTH:
        # Send a truncated message with file upload
        truncated = formatted_text[:500] + "\n\n... (response truncated, see attached file for full output)"
        
        await web_client.chat_postMessage(
            channel=channel,
            text=truncated,
            thread_ts=thread_ts,
            blocks=blocks
        )
        
        # Upload full response as file
        await web_client.files_upload_v2(
            channel=channel,
            thread_ts=thread_ts,
            content=text,
            filename="claude_response.md",
            title="Full Claude Response"
        )
    else:
        # Send regular message
        await web_client.chat_postMessage(
            channel=channel,
            text=formatted_text,
            thread_ts=thread_ts,
            blocks=blocks
        )

def detect_project_from_command(command_text: str) -> Optional[str]:
    """Detect which project to work in based on command text."""
    command_lower = command_text.lower()
    
    # Check configured aliases first
    for alias, repo_key in REPO_ALIASES.items():
        if alias and alias in command_lower:
            repo_path = REPO_PATHS.get(repo_key, '')
            if repo_path and repo_path.strip():
                return repo_path
    
    # Check direct repository names from paths
    for repo_key, repo_path in REPO_PATHS.items():
        if repo_path and repo_path.strip():
            # Extract project name from path
            project_name = repo_path.split('/')[-1].lower()
            if project_name in command_lower:
                return repo_path
    
    return None

async def handle_code_command(command_text: str, channel: str, thread_ts: str, user: str) -> None:
    """Handle /code slash command."""
    if not command_text:
        await send_response(
            channel,
            "Please provide a coding task. Example: `/code create a React login component`",
            thread_ts
        )
        return

    # Get or create session for user
    session_key = f"{user}:{channel}"
    session_id = active_sessions.get(session_key)
    
    # Detect project directory
    working_dir = detect_project_from_command(command_text)
    project_name = ""
    if working_dir:
        project_name = f" (in {working_dir.split('/')[-1]})"

    # Detect if this is a complex analysis task that needs more turns
    analysis_keywords = ['analyze', 'review', 'examine', 'check', 'audit', 'overview', 'summary', 'structure']
    is_analysis_task = any(keyword in command_text.lower() for keyword in analysis_keywords)
    
    max_turns_for_task = MAX_TURNS + 5 if is_analysis_task else MAX_TURNS

    # Send working indicator
    await send_response(
        channel,
        f"🤖 Claude Code SDK is working on{project_name}: \"{command_text}\"",
        thread_ts
    )

    # Run Claude Code SDK with appropriate turn limit
    result = await run_claude_sdk(
        command_text,
        session_id=session_id,
        working_dir=working_dir,
        options={'max_turns': max_turns_for_task}
    )

    # Update session
    if result.get('session_id'):
        active_sessions[session_key] = result['session_id']

    # Send result
    response_text = "✅ **Task Completed**\n\n"
    if result['success']:
        response_text += result['result']
        if result.get('cost', 0) > 0:
            response_text += f"\n\n_Cost: ${result['cost']:.4f}_"
    else:
        response_text = f"❌ **Error**: {result['result']}"

    await send_response(channel, response_text, thread_ts)

async def handle_feature_command(command_text: str, channel: str, thread_ts: str, user: str) -> None:
    """Handle /feature slash command for creating new features with PR."""
    if not command_text:
        await send_response(
            channel,
            "Please describe the feature. Example: `/feature user authentication with JWT`",
            thread_ts
        )
        return

    session_key = f"{user}:{channel}"
    session_id = active_sessions.get(session_key)

    await send_response(
        channel,
        f"🚀 Creating feature: \"{command_text}\"",
        thread_ts
    )

    # Enhanced prompt for feature development
    enhanced_prompt = f"""
Create a new feature: {command_text}

Please follow this complete workflow:
1. Create a new feature branch with descriptive name
2. Implement the feature with proper code structure and best practices
3. Write comprehensive unit tests for the feature
4. Update documentation and README if needed
5. Run tests to ensure everything works
6. Create a pull request with detailed description
7. Provide a summary of all changes made

Focus on:
- Clean, maintainable code
- Proper error handling
- Security best practices
- Performance considerations
- Comprehensive testing
"""

    result = await run_claude_sdk(
        enhanced_prompt,
        session_id=session_id
    )

    if result.get('session_id'):
        active_sessions[session_key] = result['session_id']

    # Create blocks for better formatting
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"✅ **Feature \"{command_text}\" completed!**"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": result['result'] if result['success'] else f"❌ Feature creation failed: {result['result']}"
            }
        }
    ]

    await send_response(channel, "", thread_ts, blocks=blocks)

async def handle_review_command(command_text: str, channel: str, thread_ts: str, user: str) -> None:
    """Handle /review slash command for code review."""
    if not command_text:
        await send_response(
            channel,
            "Specify what to review. Example: `/review PR #123` or `/review src/components/`",
            thread_ts
        )
        return

    session_key = f"{user}:{channel}"
    session_id = active_sessions.get(session_key)

    await send_response(
        channel,
        f"🔍 Starting comprehensive code review: \"{command_text}\"",
        thread_ts
    )

    review_prompt = f"""
Perform a comprehensive code review of: {command_text}

Please analyze and provide detailed feedback on:

1. **Code Quality & Best Practices**
   - Code structure and organization
   - Naming conventions
   - Design patterns usage
   - DRY principle adherence

2. **Security Analysis**
   - Input validation
   - Authentication/authorization
   - SQL injection risks
   - XSS vulnerabilities
   - Sensitive data exposure

3. **Performance Considerations**
   - Algorithm efficiency
   - Database query optimization
   - Memory usage
   - Potential bottlenecks

4. **Testing & Reliability**
   - Test coverage analysis
   - Edge case handling
   - Error handling robustness
   - Logging adequacy

5. **Documentation & Maintainability**
   - Code comments quality
   - Documentation completeness
   - API documentation
   - README updates needed

Provide specific, actionable recommendations for each area.
"""

    result = await run_claude_sdk(
        review_prompt,
        session_id=session_id
    )

    if result.get('session_id'):
        active_sessions[session_key] = result['session_id']

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📋 **Code Review Results for \"{command_text}\"**"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": result['result'] if result['success'] else f"❌ Code review failed: {result['result']}"
            }
        }
    ]

    await send_response(channel, "", thread_ts, blocks=blocks)

async def handle_pr_command(command_text: str, channel: str, thread_ts: str, user: str) -> None:
    """Handle /pr slash command for creating pull requests."""
    if not command_text:
        await send_response(
            channel,
            "Please describe the PR. Example: `/pr implement user profile management`",
            thread_ts
        )
        return

    session_key = f"{user}:{channel}"
    session_id = active_sessions.get(session_key)

    await send_response(
        channel,
        f"📝 Creating pull request: \"{command_text}\"",
        thread_ts
    )

    pr_prompt = f"""
Create a pull request for the changes related to: {command_text}

Please:
1. Review all current changes in the repository
2. Ensure all changes are properly staged
3. Create commits with clear, descriptive messages
4. Push changes to a new branch
5. Create a pull request with:
   - Clear, descriptive title
   - Detailed description of changes
   - List of what was added/modified/removed
   - Testing notes
   - Any breaking changes
6. Provide the PR URL and summary

Make sure the PR follows best practices and includes all necessary information for reviewers.
"""

    result = await run_claude_sdk(
        pr_prompt,
        session_id=session_id
    )

    if result.get('session_id'):
        active_sessions[session_key] = result['session_id']

    response_text = "✅ **Pull Request Created!**\n\n" if result['success'] else "❌ **PR Creation Failed**\n\n"
    response_text += result['result']

    await send_response(channel, response_text, thread_ts)

async def handle_message(event: Dict[str, Any]) -> None:
    """Handle incoming messages."""
    global bot_user_id
    
    channel = event.get("channel")
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    user = event.get("user")
    
    # Skip bot's own messages
    if user == bot_user_id:
        return
    
    # Remove bot mention from text
    text = re.sub(f'<@{bot_user_id}>', '', text).strip()
    
    # Check for help command
    if text.lower() in ['help', 'help me', '?']:
        await send_response(channel, HELP_MESSAGE, thread_ts)
        return
    
    # Ensure we have a prompt
    if not text:
        await send_response(
            channel,
            "Please provide a request. Type `help` for usage instructions.",
            thread_ts
        )
        return
    
    # Send typing indicator
    logger.info(f"Processing request from {user}: {text[:50]}...")
    
    # Handle as general coding request
    await handle_code_command(text, channel, thread_ts, user)

async def handle_slash_command(ack, command: Dict[str, Any]) -> None:
    """Handle slash commands."""
    # Don't call ack() here - it's handled in process_event
    
    command_name = command.get("command", "").lower()
    command_text = command.get("text", "").strip()
    channel = command["channel_id"]
    user = command["user_id"]
    thread_ts = None  # Slash commands don't use threads by default
    
    logger.info(f"Handling slash command: {command_name} from {user}")
    
    # Route to appropriate handler
    if command_name == "/code":
        await handle_code_command(command_text, channel, thread_ts, user)
    elif command_name == "/feature":
        await handle_feature_command(command_text, channel, thread_ts, user)
    elif command_name == "/review":
        await handle_review_command(command_text, channel, thread_ts, user)
    elif command_name == "/pr":
        await handle_pr_command(command_text, channel, thread_ts, user)
    else:
        await send_response(
            channel,
            f"Unknown command: {command_name}. Type `help` for available commands.",
            thread_ts
        )

async def process_event(client: SocketModeClient, req: SocketModeRequest) -> None:
    """Process Socket Mode events."""
    logger.info(f"📥 Received event type: {req.type}")
    logger.debug(f"Event payload: {req.payload}")
    
    if req.type == "events_api":
        response = SocketModeResponse(envelope_id=req.envelope_id)
        await client.send_socket_mode_response(response)
        
        event = req.payload.get("event", {})
        event_type = event.get("type")
        
        if event_type == "message":
            await handle_message(event)
        elif event_type == "app_mention":
            await handle_message(event)
    
    elif req.type == "slash_commands":
        # Acknowledge the slash command first
        response = SocketModeResponse(envelope_id=req.envelope_id)
        await client.send_socket_mode_response(response)
        
        # Handle the command
        await handle_slash_command(None, req.payload)

async def main():
    """Main application entry point."""
    global web_client, socket_client, bot_user_id
    
    logger.info("Starting Claude Code SDK Slack Bot...")
    
    # Initialize Slack clients
    web_client = AsyncWebClient(token=SLACK_BOT_TOKEN)
    socket_client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=web_client
    )
    
    # Get bot user ID
    try:
        auth_result = await web_client.auth_test()
        bot_user_id = auth_result["user_id"]
        logger.info(f"Bot user ID: {bot_user_id}")
    except Exception as e:
        logger.error(f"Failed to get bot user ID: {e}")
        bot_user_id = None
    
    # Validate GitHub token if provided
    if GITHUB_TOKEN and GITHUB_TOKEN != "ghp_your_github_token_here":
        logger.info("GitHub integration enabled")
    else:
        logger.warning("GitHub token not provided - GitHub features will be limited")
    
    # Set up workspace
    workspace = setup_workspace()
    logger.info(f"Workspace directory: {workspace}")
    
    # Set up MCP configuration
    mcp_config_path = Path(MCP_CONFIG_PATH)
    if mcp_config_path.exists():
        logger.info(f"MCP configuration loaded from: {mcp_config_path}")
    else:
        logger.warning(f"MCP configuration not found at: {mcp_config_path}")
    
    # Set up event handler
    socket_client.socket_mode_request_listeners.append(process_event)
    
    # Start the client
    await socket_client.connect()
    
    # Set bot presence to active
    try:
        await web_client.users_setPresence(presence="auto")
        logger.info("✅ Bot presence set to active")
    except Exception as e:
        logger.warning(f"Could not set bot presence: {e}")
    
    logger.info("✅ Claude Code SDK Slack Bot is running!")
    logger.info("Available commands: /code, /feature, /review, /pr")
    logger.info("Authentication method: OAuth (Claude Code SDK)")
    
    # Keep the connection alive with periodic presence updates
    async def keep_active():
        while True:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                await web_client.users_setPresence(presence="auto")
                logger.debug("🟢 Presence updated to active")
            except Exception as e:
                logger.warning(f"Failed to update presence: {e}")
    
    try:
        # Start presence keeper task
        presence_task = asyncio.create_task(keep_active())
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if 'presence_task' in locals():
            presence_task.cancel()
    finally:
        await socket_client.close()

if __name__ == "__main__":
    asyncio.run(main())