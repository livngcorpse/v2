# 🧠 JARVIS v2 — Self-Evolving AI Telegram Bot

## 🚀 Quick Setup

1. **Clone and Install**:
   ```bash
   git clone <your-repo>
   cd jarvis_bot
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your Telegram Bot Token (`API_TOKEN`)
   - Add your Gemini API Key (`GEMINI_API_KEY`)
   - Add your Telegram User ID (`OWNER_ID`)

3. **Run**:
   ```bash
   python main.py
   ```

## 🔑 Environment Variables

```env
API_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OWNER_ID=your_telegram_user_id_here
```

## 💬 Usage

### DM Chat
- Send any text directly to get AI responses
- No `/` prefix needed

### Group Chat
- Include "jarvis" in your message
- Example: "Hey jarvis, create a calculator bot"

### File Processing
- Send `.txt` file only → AI reads and builds
- Send file + caption → AI uses caption as instruction

## 🎯 Core Commands

| Command | Description | Access |
|---------|-------------|---------|
| `/start` | Welcome message | All |
| `/help` | Show help | All |
| `/info` | Bot status | All |
| `/access dev\|public` | Toggle access mode | Dev |
| `/adddev <id>` | Add developer | Owner |
| `/removedev <id>` | Remove developer | Owner |
| `/memory` | View recent tasks | All |
| `/clearmemory` | Clear memory | Dev |
| `/tree` | Show folder structure | All |
| `/diff <file>` | Show file changes | Dev |
| `/undo <file>` | Revert file changes | Dev |
| `/log` | View AI activity | Dev |
| `/enable <feature>` | Enable plugin | Dev |
| `/disable <feature>` | Disable plugin | Dev |
| `/review <file>` | AI code review | Dev |

## 🏗️ Architecture

```
jarvis_bot/
├── features/           # Plugin modules
│   └── example/
│       └── handler.py
├── bots/              # Generated sub-bots
├── db/                # JSON databases
├── logs/              # Activity & error logs
├── uploads/           # Temporary files
├── config/
│   └── settings.json  # Bot configuration
├── main.py            # Core bot logic
├── jarvis_engine.py   # AI processing
├── file_manager.py    # File operations
└── error_handler.py   # Error management
```

## 🔌 Creating Features

Create new features in `features/<name>/handler.py`:

```python
from telegram.ext import CommandHandler

def register_handlers(dp):
    dp.add_handler(CommandHandler("mycommand", my_handler))

async def my_handler(update, context):
    await update.message.reply_text("Feature working!")
```

## 🛡️ Security

- **Owner**: Full access (set via `OWNER_ID`)
- **Developers**: Can be added/removed by owner
- **Access Modes**:
  - `dev`: Only developers can use AI features
  - `public`: Anyone can use basic features

## 🤖 AI Capabilities

JARVIS can create:
- Complete Telegram bots
- Games and interactive features
- Command handlers
- Database systems
- Utility tools
- Feature plugins

## 📝 AI Response Format

For file operations, AI returns:
```json
{
  "files": {
    "path/to/file.py": "file content",
    "db/data.json": "{}"
  }
}
```

## 🔧 Advanced Features

### Memory System
- Tracks recent AI tasks
- Viewable with `/memory`
- Clearable with `/clearmemory`

### File Management
- Auto-backup before changes
- Diff viewing with `/diff`
- Rollback with `/undo`

### Plugin System
- Auto-discovery of features
- Enable/disable dynamically
- Modular architecture

### Error Handling
- Comprehensive logging
- Graceful failure recovery
- Debug information

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check API_TOKEN in `.env`
   - Verify bot is started with BotFather

2. **AI not working**:
   - Check GEMINI_API_KEY in `.env`
   - Verify API key has proper permissions

3. **Permission denied**:
   - Check OWNER_ID matches your Telegram ID
   - Use `/adddev` to add developers

4. **File operations failing**:
   - Check file permissions
   - Ensure proper directory structure

### Getting Help

- Check logs in `logs/` directory
- Use `/log` command for recent activity
- Review memory with `/memory`

## 📄 License

This project is open source. Modify and distribute as needed.

---

**JARVIS v2** - Built with ❤️ for the AI community