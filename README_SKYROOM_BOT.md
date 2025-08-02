# 🎓 Skyroom Registration Bot for Ostad Hatami

**ربات ثبت‌نام کلاس‌های رایگان استاد حاتمی در اسکای‌روم**

## 🎯 **Overview**

A professional, fully interactive Telegram bot designed for registering students in free online math classes conducted by "Ostad Hatami" via Skyroom. The bot provides a seamless registration experience with comprehensive data validation, user-friendly interface, and secure JSON-based data storage.

## ✨ **Key Features**

### 🔄 **Complete Registration Flow**
- **7-step registration process** with FSM (Finite State Machine)
- **Real-time validation** for all input fields
- **Persian/Arabic name validation** with Unicode support
- **Iranian phone number validation** with multiple formats
- **Province/City selection** with dynamic keyboards

### 🎨 **User Experience**
- **Personalized welcome messages** using user's first name
- **Interactive keyboards** for easy selection
- **Progress indicators** throughout registration
- **Contact sharing** support for phone numbers
- **Edit functionality** for all registered fields

### 🔒 **Data Management**
- **JSON-based storage** in `users/` directory
- **Individual user files** (`user_{user_id}.json`)
- **Data validation** and normalization
- **Timestamp tracking** for registration and updates
- **Error handling** and logging

### 📱 **Telegram Integration**
- **Modern aiogram 3.x** framework
- **Inline keyboards** for better UX
- **Reply keyboards** for phone input
- **Callback query handling** for all interactions
- **State management** for multi-step processes

## 🏗️ **Architecture**

### **Core Components**
```
📦 Skyroom Bot/
├── 📄 skyroom_registration_bot.py    # Main bot file
├── 📄 requirements_skyroom.txt        # Dependencies
├── 📄 env_skyroom.txt                # Environment template
├── 📄 README_SKYROOM_BOT.md          # This file
├── 📁 users/                         # User data storage
│   ├── user_123456789.json
│   ├── user_987654321.json
│   └── ...
└── 📁 logs/                          # Application logs
```

### **Class Structure**
- **`RegistrationStates`** - FSM states for registration flow
- **`DataValidator`** - Input validation utilities
- **`UserDataManager`** - JSON data storage management
- **`KeyboardBuilder`** - Dynamic keyboard generation
- **`MessageTemplates`** - Message templates and formatting

## 🚀 **Installation & Setup**

### **1. Prerequisites**
```bash
# Python 3.8 or higher
python --version

# Git (for cloning)
git --version
```

### **2. Clone Repository**
```bash
git clone <repository-url>
cd skyroom-registration-bot
```

### **3. Install Dependencies**
```bash
# Install core dependencies
pip install -r requirements_skyroom.txt

# Or install manually
pip install aiogram==3.4.1 python-dotenv==1.0.0
```

### **4. Environment Setup**
```bash
# Copy environment template
cp env_skyroom.txt .env

# Edit .env file with your bot token
nano .env
```

### **5. Configure Bot Token**
```bash
# In .env file
BOT_TOKEN=your_telegram_bot_token_here
```

### **6. Run the Bot**
```bash
python skyroom_registration_bot.py
```

## 🔄 **Bot Flow**

### **1. Welcome & Start**
```
User sends /start
↓
Bot greets user by name
↓
Shows welcome message + "شروع ثبت‌نام" button
```

### **2. Registration Process**
```
Step 1: First Name (text input)
Step 2: Last Name (text input)
Step 3: Grade (inline keyboard: دهم/یازدهم/دوازدهم)
Step 4: Major (inline keyboard: ریاضی/تجربی/انسانی/هنر)
Step 5: Province (inline keyboard: استان‌ها)
Step 6: City (inline keyboard: شهرهای استان انتخاب شده)
Step 7: Phone (contact sharing or manual input)
```

### **3. Confirmation & Completion**
```
Show profile summary
↓
User confirms or edits
↓
Save to JSON file
↓
Show success message + main menu
```

### **4. Main Menu Features**
```
🗓 مشاهده کلاس‌های قابل ثبت‌نام
📘 تهیه کتاب انفجار خلاقیت
🧑‍🏫 ارتباط با استاد حاتمی
⚙️ ویرایش اطلاعات
```

## 📊 **Data Storage**

### **JSON Structure**
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

### **File Organization**
- **Directory:** `users/`
- **Naming:** `user_{user_id}.json`
- **Encoding:** UTF-8
- **Format:** Pretty-printed JSON

## 🔧 **Configuration**

### **Supported Grades**
- دهم (10th Grade)
- یازدهم (11th Grade)
- دوازدهم (12th Grade)

### **Supported Majors**
- ریاضی (Mathematics)
- تجربی (Biology)
- انسانی (Humanities)
- هنر (Arts)

### **Supported Provinces**
- تهران, خراسان رضوی, اصفهان, فارس
- آذربایجان شرقی, مازندران, گیلان
- خوزستان, قم, البرز, سایر

### **Phone Number Formats**
- `+989121234567`
- `09121234567`
- `9121234567`
- `09121234567`

## 🎨 **User Interface**

### **Keyboard Types**
- **Inline Keyboards** - For selections (grade, major, province, city)
- **Reply Keyboards** - For phone number input
- **Dynamic Layouts** - Adjusts based on content

### **Message Formatting**
- **Bold text** for headers
- **Emojis** for visual appeal
- **Structured layout** for readability
- **Persian RTL** support

### **Validation Messages**
- **Clear error messages** in Persian
- **Helpful suggestions** for corrections
- **Progress indicators** throughout process

## 🔒 **Security & Validation**

### **Input Validation**
- **Name validation** - Persian/Arabic characters only
- **Phone validation** - Iranian phone number patterns
- **Length checks** - Minimum requirements
- **Format normalization** - Standardized output

### **Data Protection**
- **User-specific files** - No cross-user data access
- **Input sanitization** - Prevents injection attacks
- **Error handling** - Graceful failure management
- **Logging** - Audit trail for debugging

## 📈 **Performance & Scalability**

### **Optimizations**
- **Memory storage** - Fast state management
- **Efficient JSON handling** - Minimal I/O operations
- **Async operations** - Non-blocking performance
- **Modular design** - Easy maintenance and extension

### **Scalability Features**
- **File-based storage** - No database dependency
- **Individual user files** - Parallel processing support
- **State management** - Handles concurrent users
- **Error recovery** - Robust failure handling

## 🛠️ **Development & Customization**

### **Adding New Features**
1. **Extend FSM states** in `RegistrationStates`
2. **Add validation** in `DataValidator`
3. **Create keyboards** in `KeyboardBuilder`
4. **Add handlers** for new callbacks
5. **Update templates** in `MessageTemplates`

### **Modifying Data Structure**
1. **Update JSON schema** in `UserDataManager`
2. **Add new fields** to registration flow
3. **Extend validation** for new data types
4. **Update confirmation** display

### **Customizing Messages**
1. **Edit templates** in `MessageTemplates`
2. **Modify keyboard** layouts in `KeyboardBuilder`
3. **Update validation** messages in handlers
4. **Customize success** and error messages

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Install missing dependencies
pip install -r requirements_skyroom.txt
```

#### **2. Bot Token Issues**
```bash
# Check .env file
cat .env

# Verify token format
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### **3. Permission Errors**
```bash
# Fix directory permissions
chmod 755 users/
chmod 644 *.py
```

#### **4. Encoding Issues**
```bash
# Ensure UTF-8 encoding
export PYTHONIOENCODING=utf-8
```

### **Debug Mode**
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 **Support & Maintenance**

### **Logging**
- **File logging** - `skyroom_bot.log`
- **Console output** - Real-time monitoring
- **Error tracking** - Detailed error information
- **User activity** - Registration and interaction logs

### **Monitoring**
- **User registration** statistics
- **Error rate** monitoring
- **Performance** metrics
- **Storage** usage tracking

### **Backup & Recovery**
- **Regular backups** of `users/` directory
- **Data validation** scripts
- **Migration tools** for schema updates
- **Recovery procedures** for data loss

## 🚀 **Deployment Options**

### **Local Development**
```bash
python skyroom_registration_bot.py
```

### **VPS Deployment**
```bash
# Create systemd service
sudo nano /etc/systemd/system/skyroom-bot.service

# Start service
sudo systemctl enable skyroom-bot
sudo systemctl start skyroom-bot
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements_skyroom.txt
CMD ["python", "skyroom_registration_bot.py"]
```

### **Cloud Platforms**
- **Railway** - Easy deployment
- **Heroku** - Scalable hosting
- **AWS** - Enterprise-grade
- **Google Cloud** - High performance

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📞 **Contact**

- **Email:** support@ostadhatami.ir
- **Telegram:** @Ostad_Hatami
- **Website:** www.ostadhatami.ir

---

**🎓 Ready to revolutionize your Skyroom class registration experience! 🚀** 