# Claude Code Slack Bot

A powerful Slack bot that integrates Claude Code SDK with GitHub to provide AI-powered coding assistance directly in your Slack workspace. Create features, review code, generate pull requests, and manage multiple repositories - all from Slack!

## ✨ Features

- **🤖 AI-Powered Coding**: Full Claude Code SDK integration with OAuth authentication
- **🔀 GitHub Integration**: Create PRs, review code, and manage repositories
- **📁 Multi-Repository Support**: Work with up to 5 different projects via environment configuration
- **💬 Multiple Interaction Methods**: @mentions, DMs, and specialized slash commands
- **🔄 Session Management**: Maintains conversation context across messages
- **📊 Smart Response Handling**: Automatic code formatting and file uploads for long responses
- **🔍 Advanced Code Review**: Security analysis, performance checks, and best practices
- **⚡ Real-time Events**: Socket Mode for instant responses without webhooks

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js** (for Claude CLI and MCP servers)
- **Slack workspace** with admin access
- **GitHub account** (optional, for PR features)
- **Anthropic account** for Claude access

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd slack-claude-code

# Install dependencies
pip install -r requirements.txt

# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Setup OAuth authentication for Claude
claude auth login
```

### 2. Slack App Setup

#### Create Slack App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: **"Claude Code Bot"**
4. Select your workspace

#### Configure Permissions
**OAuth & Permissions** → Add these **Bot Token Scopes**:
- `app_mentions:read` - Detect @mentions
- `channels:read` - Access channel information  
- `chat:write` - Send messages
- `commands` - Receive slash commands
- `files:write` - Upload files
- `reactions:write` - Add reactions
- `users:read` - Read user info
- `users:write` - Set bot presence

#### Enable Socket Mode
1. **Socket Mode** → **Enable Socket Mode**: ✅
2. **Create App-Level Token** with `connections:write` scope
3. **Copy the App-Level Token** (starts with `xapp-`)

#### Create Slash Commands
**Slash Commands** → Create these (leave **Request URL empty** for all):

| Command | Description | Usage Hint |
|---------|-------------|------------|
| `/code` | General coding tasks | `create a React component` |
| `/feature` | Create features with PR | `user authentication system` |
| `/review` | Code review with security analysis | `PR #123 or src/components/` |
| `/pr` | Create pull request | `implement user management` |

#### Event Subscriptions
1. **Event Subscriptions** → **Enable Events**: ✅
2. **Subscribe to bot events**:
   - `app_mention` - When bot is @mentioned
   - `message.im` - Direct messages to bot

#### Install App
1. **Install App** → **Install to Workspace**
2. **Copy Bot User OAuth Token** (starts with `xoxb-`)

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your tokens and paths
nano .env
```

**Required Configuration:**
```env
# Slack Tokens
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# GitHub (optional)
GITHUB_TOKEN=your-github-token

# Repository Paths
DEFAULT_REPO_PATH=/path/to/your/main/project
REPO1_PATH=/path/to/frontend
REPO1_NAME=frontend
REPO2_PATH=/path/to/backend  
REPO2_NAME=backend
```

### 4. Start the Bot

```bash
# Test configuration
python3 -c "from config import *; print('✅ Config OK')"

# Run the bot
python3 app.py
```

You should see:
```
✅ Claude Code SDK Slack Bot is running!
Available commands: /code, /feature, /review, /pr
```

### 5. Test in Slack

```bash
# Add bot to a channel
/invite @claude_code_bot

# Test basic functionality
@claude_code_bot help
/code create a simple Python function

# Test project-specific commands
/code analyze frontend components
/code fix backend API issues
```

## 🏗️ Deployment Options

### Option 1: Local Development
```bash
# Run directly
python3 app.py

# Run in background
nohup python3 app.py > bot.log 2>&1 &
```

### Option 2: Docker Deployment
```dockerfile
FROM python:3.10-slim

# Install Node.js for Claude CLI
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python3", "app.py"]
```

```bash
# Build and run
docker build -t claude-slack-bot .
docker run -d --env-file .env claude-slack-bot
```

### Option 3: Cloud Deployment

#### Railway
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

#### Heroku
```bash
# Create Procfile
echo "web: python3 app.py" > Procfile

# Deploy
heroku create your-bot-name
heroku config:set SLACK_BOT_TOKEN=your-token
# ... set other env vars
git push heroku main
```

#### DigitalOcean App Platform
1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically

### Option 4: VPS/Server
```bash
# Using systemd (recommended)
sudo cp slack-claude-bot.service /etc/systemd/system/
sudo systemctl enable slack-claude-bot
sudo systemctl start slack-claude-bot

# Using PM2
npm install -g pm2
pm2 start app.py --name claude-bot --interpreter python3
pm2 save
pm2 startup
```

## 📚 Usage Guide

### Basic Commands

**General Coding:**
```
/code create a REST API with FastAPI
/code explain this error: [paste error]
/code refactor this function for better performance
```

**Project-Specific:**
```
/code analyze frontend components
/code fix backend database connection
/code update mobile app authentication
```

### Advanced Features

**Feature Development:**
```
/feature user authentication system
/feature real-time notifications
/feature payment integration
```

**Code Review:**
```
/review PR #123
/review src/components/
/review check security vulnerabilities
```

**Pull Requests:**
```
/pr implement user dashboard
/pr fix authentication issues  
/pr add new API endpoints
```

### Multi-Repository Setup

Configure multiple projects in `.env`:
```env
DEFAULT_REPO_PATH=/home/user/main-project

REPO1_PATH=/home/user/frontend
REPO1_NAME=frontend
REPO2_PATH=/home/user/backend
REPO2_NAME=backend
REPO3_PATH=/home/user/mobile
REPO3_NAME=mobile
```

Use in commands:
```
/code fix the frontend login component
/code update backend API documentation
/code test mobile app performance
```

## 🔧 Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token | - | ✅ |
| `SLACK_APP_TOKEN` | App-Level Token | - | ✅ |
| `GITHUB_TOKEN` | GitHub Personal Access Token | - | Optional |
| `DEFAULT_REPO_PATH` | Main project directory | `/tmp/repos` | ✅ |
| `REPO1_PATH` - `REPO5_PATH` | Additional project paths | - | Optional |
| `REPO1_NAME` - `REPO5_NAME` | Project aliases | `project1` - `project5` | Optional |
| `MAX_TURNS` | Max AI conversation turns | `8` | Optional |
| `MAX_MESSAGE_LENGTH` | Max Slack message length | `3000` | Optional |
| `DEBUG` | Enable debug logging | `false` | Optional |

### Slack App Requirements

**Bot Token Scopes:**
- `app_mentions:read`, `channels:read`, `chat:write`
- `commands`, `files:write`, `reactions:write`
- `users:read`, `users:write`

**App-Level Token Scopes:**
- `connections:write`

**Event Subscriptions:**
- `app_mention`, `message.im`

**Features Required:**
- Socket Mode: ✅ Enabled
- Slash Commands: ✅ Configured
- Request URLs: ❌ Empty (Socket Mode)

## 🛠️ Troubleshooting

### Bot Not Responding
```bash
# Check bot status
ps aux | grep app.py

# Check logs
tail -f slack-claude-bot.log

# Test configuration
python3 -c "from config import *; print('Config OK')"
```

### Authentication Issues
```bash
# Claude authentication
claude auth status
claude auth login

# Test Claude CLI
claude -p "hello" --output-format json
```

### Slack Connection Issues
```bash
# Verify tokens
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
     https://slack.com/api/auth.test

# Check Socket Mode
# Ensure Request URLs are empty in slash commands
```

### Repository Access Issues
```bash
# Check permissions
ls -la /path/to/your/repos

# Test repository detection
python3 -c "
from app import detect_project_from_command
print(detect_project_from_command('fix frontend issue'))
"
```

## 🔒 Security Best Practices

- **Environment Variables**: Store secrets in `.env`, never in code
- **API Tokens**: Use minimal required scopes
- **Repository Access**: Limit to necessary directories only
- **Network**: Use HTTPS and secure connections
- **Updates**: Keep dependencies updated regularly

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Documentation**: Check this README and inline comments
- **Claude Code**: https://docs.anthropic.com/claude/docs/claude-code
- **Slack API**: https://api.slack.com/docs

## 🎯 Roadmap

- [ ] Web dashboard for bot management
- [ ] Integration with more git providers (GitLab, Bitbucket)
- [ ] Custom tool development framework
- [ ] Team collaboration features
- [ ] Advanced analytics and metrics
- [ ] Voice commands via Slack calls

---

**Happy Coding! 🚀**

Built with ❤️ using Claude Code SDK, Slack API, and Python.