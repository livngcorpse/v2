# 🧠 JARVIS v2 — Self-Evolving AI Telegram Bot

> An intelligent, self-evolving AI-powered Telegram assistant built with Python, Gemini/GPT, and modular plugin support.

---

## 🔰 Overview

**JARVIS v2** is a modular, AI-powered Telegram bot that:

- Understands natural language prompts
- Dynamically edits or generates code and features
- Uses plugins and file-based features
- Tracks memory and supports file diffs, undo, and logging
- Offers fine-grained access control for dev-only operations

It runs entirely inside Telegram, processing messages, files, and commands.

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/youruser/jarvis_bot.git
cd jarvis_bot
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Environment File

Copy `.env.example` to `.env` and fill in your details:

```env
API_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
OWNER_ID=your_telegram_user_id
```

### 4. Run the Bot

```bash
python main.py
```

---

## 💬 How to Use

### Private Chat

* Send **any message** (no `/`) to trigger AI processing

### Group Chat

* Mention `jarvis` in your message to activate the bot

### File Uploads

* Upload a `.txt` file only → AI reads and begins building
* Upload with a caption → Caption is treated as instruction, file as context

---

## 📦 Features

### ✅ AI Capabilities

* Converts prompts into working bots, games, handlers, utilities
* Uses Gemini or GPT to generate JSON with file paths + content
* Automatically writes files into the project directory
* Supports AI code reviews with `/review`

### 🧠 Memory System

* Logs every AI task to `logs/memory.json`
* View with `/memory`
* Clear with `/clearmemory`

### 🧩 Plugin & Feature Loader

* Plugin modules live in `plugins/`
* Legacy file-based features in `features/`
* Auto-discovered and registered
* Enable/disable plugins dynamically via commands

### 📁 File Management

* `.bak` backups created before file edits
* Use `/diff <file>` to see changes
* Use `/undo <file>` to revert last edit

---

## 🔐 Access Control

| Role          | Rights                                                  |
| ------------- | ------------------------------------------------------- |
| **Owner**     | Set via `OWNER_ID`; can add/remove devs                 |
| **Developer** | Granted access via `/adddev`; can use dev-only commands |
| **Public**    | Controlled via `/access dev` or `/access public`        |

---

## 🔧 Commands

| Command               | Description                   | Access     |
| --------------------- | ----------------------------- | ---------- |
| `/start`              | Welcome message               | All        |
| `/help`               | Show all commands             | All        |
| `/info`               | Show status & plugin info     | All        |
| `/access dev\|public` | Toggle access mode            | Dev        |
| `/adddev <id>`        | Add developer                 | Owner only |
| `/removedev <id>`     | Remove developer              | Owner only |
| `/memory`             | View recent memory entries    | All        |
| `/clearmemory`        | Clear memory history          | Dev        |
| `/tree`               | View bot folder structure     | All        |
| `/diff <file>`        | Show file diff                | Dev        |
| `/undo <file>`        | Undo file to last state       | Dev        |
| `/log`                | View recent AI logs           | Dev        |
| `/enable <plugin>`    | Enable plugin                 | Dev        |
| `/disable <plugin>`   | Disable plugin                | Dev        |
| `/plugins`            | List all plugins              | Dev        |
| `/features`           | List legacy features          | Dev        |
| `/loadfeatures`       | Manually load legacy features | Dev        |
| `/review <file>`      | Run AI-powered code review    | Dev        |

---

## 🧠 AI Response Format

The bot expects LLMs (e.g. Gemini/GPT) to return responses like:

```json
{
  "files": {
    "main.py": "...",
    "features/my_plugin/handler.py": "...",
    "db/data.json": "{}"
  }
}
```

**No Markdown or chat formatting. Just JSON.**

---

## 🧱 Project Structure

```
jarvis_bot/
├── features/               # Legacy plugin handlers
├── plugins/                # Modern plugin modules
├── bots/                   # Generated bot modules
├── db/                     # Local JSON DBs
├── logs/                   # Activity & memory logs
├── uploads/                # Uploaded user files
├── config/
│   └── settings.json       # Persistent config (access mode, devs, etc.)
├── .env                    # API keys and secrets
├── main.py                 # Bot entrypoint
├── jarvis_engine.py        # AI handler
├── plugin_manager.py       # Plugin controller
├── file_manager.py         # Diff, undo, write
├── db_manager.py           # Storage logic
├── error_handler.py        # Logging + fallbacks
├── requirements.txt
```

---

## 📖 Advanced Features

* ✅ Modular plugin system (`/enable`, `/disable`, `/plugins`)
* ✅ Dynamic file editing with backups
* ✅ Error logging and graceful handling
* ✅ Memory, review, and rollback capabilities
* ✅ Gemini or GPT powered AI engine

---

## 📌 Tips

* Use **`/access public`** to let others test
* Use **`/memory`** and **`/log`** to debug AI behavior
* Always add a caption when uploading `.txt` files for precise results
* Use **inline keyboards** to navigate menus (optional via `/start`)

---

## 📝 License

Open-source and developer friendly. Modify and extend freely.

---

**JARVIS v2** — Your AI-powered assistant, evolving with every message.

```