# 🔧 راهنمای نصب آفلاین ربات استاد حاتمی

Offline Setup Guide for Ostad Hatami Bot

## 🚨 مشکل شبکه

به نظر می‌رسد که مشکلات شبکه مانع از نصب کتابخانه‌ها می‌شود. در اینجا چند راه حل ارائه می‌شود:

## 📦 روش ۱: نصب با تنظیمات شبکه

### تنظیم pip برای دور زدن مشکلات SSL:

```bash
pip install python-telegram-bot --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

### یا با تنظیمات proxy:

```bash
pip install python-telegram-bot --proxy http://your-proxy:port
```

## 🌐 روش ۲: نصب از منابع جایگزین

### از GitHub:
```bash
pip install git+https://github.com/python-telegram-bot/python-telegram-bot.git
```

### از PyPI با mirror:
```bash
pip install python-telegram-bot -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 💾 روش ۳: دانلود دستی

1. به [PyPI](https://pypi.org/project/python-telegram-bot/#files) بروید
2. فایل `.whl` مناسب را دانلود کنید
3. با دستور زیر نصب کنید:
```bash
pip install python-telegram-bot-20.7-py3-none-any.whl
```

## 🔍 بررسی نصب

پس از نصب، این دستور را اجرا کنید:

```bash
python -c "import telegram; print('✅ python-telegram-bot installed successfully')"
```

## 🚀 اجرای ربات

پس از نصب موفق کتابخانه:

```bash
cd D:\dad
python run_bot.py
```

## 📱 تست ربات

1. در تلگرام، ربات `@OstadHatami_bot` را پیدا کنید
2. دستور `/start` را ارسال کنید
3. فرآیند ثبت‌نام را تست کنید

## 🆘 در صورت عدم موفقیت

اگر همچنان مشکل دارید:

1. **استفاده از VPN**: VPN را فعال کنید
2. **تغییر DNS**: DNS را به 8.8.8.8 تغییر دهید
3. **استفاده از Anaconda**: 
   ```bash
   conda install -c conda-forge python-telegram-bot
   ```
4. **استفاده از Docker**: 
   ```bash
   docker run -it python:3.9 pip install python-telegram-bot
   ```

## 📞 پشتیبانی

در صورت نیاز به کمک بیشتر، لطفاً:
- خطاهای دقیق را کپی کنید
- نسخه Python خود را مشخص کنید
- تنظیمات شبکه خود را بررسی کنید

---

**💡 نکته**: ربات شما آماده است و فقط نیاز به نصب کتابخانه دارد! 