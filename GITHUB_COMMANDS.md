# 🚀 دستورات GitHub برای آپلود پروژه

## 📋 مراحل آپلود به GitHub

### ۱. ایجاد Repository در GitHub
1. به [GitHub.com](https://github.com) بروید
2. روی "New repository" کلیک کنید
3. نام repository را `math-telegram-bot` بگذارید
4. گزینه "Public" را انتخاب کنید
5. روی "Create repository" کلیک کنید

### ۲. آپلود کد (کپی و اجرای این دستورات)

```bash
# در پوشه D:\dad
git remote add origin https://github.com/YOUR_USERNAME/math-telegram-bot.git
git branch -M main
git push -u origin main
```

### ۳. جایگزینی YOUR_USERNAME
در دستور بالا، `YOUR_USERNAME` را با نام کاربری GitHub خود جایگزین کنید.

## ✅ وضعیت فعلی

پروژه شما آماده است:
- ✅ Git repository ایجاد شده
- ✅ همه فایل‌ها commit شده‌اند
- ✅ فقط نیاز به push به GitHub دارید

## 🎯 فایل‌های مهم

### برای Railway:
- `hosted_bot.py` - ربات اصلی
- `Procfile` - دستور اجرا
- `runtime.txt` - نسخه Python
- `requirements.txt` - کتابخانه‌ها

### برای مستندات:
- `README.md` - راهنمای اصلی
- `RAILWAY_SETUP.md` - راهنمای Railway
- `PROJECT_SUMMARY.md` - خلاصه پروژه

## 🚀 بعد از آپلود

1. به [Railway.app](https://railway.app) بروید
2. با GitHub وارد شوید
3. پروژه جدید ایجاد کنید
4. از GitHub import کنید
5. متغیر `BOT_TOKEN` را تنظیم کنید

## 🎉 موفقیت!

پس از آپلود، ربات شما:
- ✅ در GitHub ذخیره می‌شود
- ✅ قابل deploy روی Railway است
- ✅ 24/7 در دسترس خواهد بود

---

**آماده برای آپلود! 🚀** 