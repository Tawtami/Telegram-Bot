# 🎓 Ostad Hatami Math Classes Bot

**ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی**

## 🎯 Overview

A professional Telegram bot for registering students in free online math classes conducted by "Ostad Hatami" via Skyroom.

## ✨ Features

- **7-step registration process** with FSM
- **Real-time validation** for Persian names and Iranian phone numbers
- **Interactive keyboards** for easy selection
- **JSON-based data storage** with individual user files
- **Edit functionality** for all registered fields
- **Contact sharing** support for phone numbers
- **Admin notifications** for new registrations
- **YouTube channel integration** for free tutorials

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
cp env.txt .env
# Edit .env with your BOT_TOKEN
```

### 3. Run Bot
```bash
python bot.py
```

## 📁 Project Structure

```
📦 Telegram-Bot/
├── 🐍 bot.py              # Main optimized bot (28KB)
├── 📄 requirements.txt     # Essential dependencies only
├── ⚙️ env.txt             # Environment configuration
├── 📖 README.md           # Complete documentation
├── 🚫 .gitignore          # Proper Git ignore rules
├── 📊 data/               # User data storage
│   └── students.json      # Student registrations
└── 🐍 .venv/              # Virtual environment
```

## 🔄 Bot Flow

1. **Welcome** - Personalized greeting with user's name
2. **Registration** - 7-step process:
   - First Name (text input)
   - Last Name (text input)
   - Grade (inline keyboard: دهم/یازدهم/دوازدهم)
   - Major (inline keyboard: ریاضی/تجربی/انسانی/هنر)
   - Province (inline keyboard: استان‌ها)
   - City (inline keyboard: شهرهای استان)
   - Phone (contact sharing or manual input)
3. **Confirmation** - Review and confirm data
4. **Main Menu** - Access to classes, book info, contact, and profile editing

## 📊 Data Storage

User data is stored in JSON format:
```json
{
  "user_id": 123456789,
  "first_name": "علی",
  "last_name": "رضایی",
  "grade": "یازدهم",
  "major": "ریاضی",
  "province": "خراسان رضوی",
  "city": "مشهد",
  "phone": "+989121234567",
  "registration_date": "2024-01-15T10:30:00",
  "last_updated": "2024-01-15T10:30:00"
}
```

## 🛠️ Configuration

### Supported Grades
- دهم (10th Grade)
- یازدهم (11th Grade)
- دوازدهم (12th Grade)

### Supported Majors
- ریاضی (Mathematics)
- تجربی (Biology)
- انسانی (Humanities)
- هنر (Arts)

### Phone Number Formats
- `+989121234567`
- `09121234567`
- `9121234567`
- `09121234567`

## 🔒 Security

- **Input validation** for all fields
- **User-specific files** - No cross-user data access
- **Error handling** and logging
- **Data sanitization** and normalization

## 📞 Contact

- **Telegram:** @Ostad_Hatami
- **Email:** info@ostadhatami.ir
- **Website:** www.ostadhatami.ir

---

**🎓 Ready to revolutionize your math class registration experience! 🚀** 