# 🚀 راهنمای نصب و راه‌اندازی ربات تلگرام استاد حاتمی

## 📋 پیش‌نیازها

### **1. Python**
- Python 3.8 یا بالاتر
- pip (مدیر بسته‌های Python)

### **2. Bot Token**
- دریافت Bot Token از @BotFather در تلگرام

## 🔧 مراحل نصب

### **مرحله 1: نصب وابستگی‌ها**

```bash
# نصب python-telegram-bot
pip install python-telegram-bot==21.7

# نصب python-dotenv
pip install python-dotenv==1.0.0
```

**یا با استفاده از فایل requirements:**
```bash
pip install -r requirements_final.txt
```

### **مرحله 2: تنظیم متغیرهای محیطی**

```bash
# کپی فایل نمونه
cp env_template.txt .env

# ویرایش فایل .env
# BOT_TOKEN=your_actual_bot_token_here
```

### **مرحله 3: اجرای ربات**

```bash
python final_bot.py
```

## 📁 ساختار فایل‌ها

```
📦 Telegram-Bot/
├── 📄 final_bot.py              # ربات اصلی
├── 📄 requirements_final.txt     # وابستگی‌ها
├── 📄 env_template.txt          # نمونه متغیرهای محیطی
├── 📄 .env                      # متغیرهای محیطی (باید ایجاد شود)
├── 📁 data/
│   └── 📁 users/                # فایل‌های کاربران
├── 📄 bot.log                   # فایل لاگ (خودکار ایجاد می‌شود)
└── 📄 SETUP_GUIDE.md           # این فایل
```

## 🎯 ویژگی‌های ربات

### **✅ Onboarding کامل:**
- پیام خوش‌آمدی شخصی‌سازی شده
- فرآیند ثبت‌نام ۶ مرحله‌ای
- ذخیره‌سازی امن اطلاعات

### **✅ منوی اصلی:**
- دوره‌های استاد حاتمی
- تهیه کتاب انفجار خلاقیت
- ارتباط با ما
- شبکه‌های اجتماعی
- کانال و گروه

### **✅ امنیت و پایداری:**
- ذخیره‌سازی جداگانه هر کاربر
- مدیریت خطاها
- Logging کامل

## 🔍 تست ربات

### **1. تست اتصال:**
```bash
python -c "import telegram; print('python-telegram-bot installed successfully')"
```

### **2. تست متغیرهای محیطی:**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('BOT_TOKEN:', 'SET' if os.getenv('BOT_TOKEN') else 'NOT SET')"
```

### **3. تست ربات:**
```bash
python final_bot.py
```

## 🚨 عیب‌یابی

### **مشکل: ModuleNotFoundError**
```bash
# حل: نصب مجدد وابستگی‌ها
pip install --upgrade python-telegram-bot python-dotenv
```

### **مشکل: BOT_TOKEN not found**
```bash
# حل: بررسی فایل .env
cat .env
# اطمینان از وجود BOT_TOKEN=your_token
```

### **مشکل: Permission denied**
```bash
# حل: ایجاد دایرکتوری‌ها
mkdir -p data/users
chmod 755 data/users
```

## 📊 مانیتورینگ

### **فایل‌های لاگ:**
- `bot.log` - لاگ‌های ربات
- بررسی خطاها و عملکرد

### **داده‌های کاربران:**
- `data/users/user_[ID].json` - اطلاعات هر کاربر
- فرمت JSON قابل خواندن

## 🚀 Deploy

### **Railway:**
```bash
# اتصال به Railway
railway login
railway init
railway up
```

### **Heroku:**
```bash
# ایجاد Procfile
echo "worker: python final_bot.py" > Procfile

# Deploy
git add .
git commit -m "Deploy bot"
git push heroku main
```

### **VPS:**
```bash
# نصب systemd service
sudo nano /etc/systemd/system/telegram-bot.service

# محتوای فایل:
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 final_bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# فعال‌سازی سرویس
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

## 📞 پشتیبانی

در صورت بروز مشکل:
1. بررسی فایل `bot.log`
2. اطمینان از نصب صحیح وابستگی‌ها
3. بررسی تنظیمات متغیرهای محیطی
4. تماس با پشتیبانی

## ✅ چک‌لیست نهایی

- [ ] Python 3.8+ نصب شده
- [ ] وابستگی‌ها نصب شده‌اند
- [ ] فایل .env ایجاد و تنظیم شده
- [ ] BOT_TOKEN معتبر تنظیم شده
- [ ] دایرکتوری data/users ایجاد شده
- [ ] ربات اجرا می‌شود
- [ ] دستور /start کار می‌کند
- [ ] ثبت‌نام کاربران کار می‌کند
- [ ] منوی اصلی نمایش داده می‌شود

---

**🎉 ربات آماده استفاده است!** 