# 🚀 Bot Setup Guide

## 🔒 **Security First!**

This is a **public repository**. Never commit sensitive information like bot tokens or admin user IDs.

## 📋 **Setup Steps**

### 1. **Get Your Bot Token**

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token you receive

### 2. **Set Environment Variables**

**Option A: Create .env file (Recommended)**

```bash
# Create a .env file in the project root
BOT_TOKEN=your_actual_bot_token_here
ADMIN_USER_IDS=your_telegram_user_id,another_admin_id
```

**Option B: Set system environment variables**

```bash
# Windows (PowerShell)
$env:BOT_TOKEN="your_actual_bot_token_here"

# Windows (Command Prompt)
set BOT_TOKEN=your_actual_bot_token_here

# Linux/Mac
export BOT_TOKEN="your_actual_bot_token_here"
```

### 3. **Configure Admin Users**

- Get your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot)
- Add admin IDs to `ADMIN_USER_IDS` (comma-separated)

### 4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 5. **Run the Bot**

```bash
python bot.py
```

## 🔐 **Security Checklist**

- [ ] Never commit `.env` files
- [ ] Never commit `env.txt` with real tokens
- [ ] Use placeholder values in public files
- [ ] Keep bot tokens private
- [ ] Regularly rotate tokens if needed

## 📞 **Support**

For issues or questions, contact the bot administrators.

---

**⚠️ Remember: Keep your bot token secret!** 🔒
