# 🚀 راهنمای کامل نصب ربات روی Railway

## 📋 مراحل نصب

### مرحله ۱: آماده‌سازی GitHub

#### ۱.۱ ایجاد Repository در GitHub

1. به [GitHub.com](https://github.com) بروید
2. روی "New repository" کلیک کنید
3. نام repository را `math-telegram-bot` بگذارید
4. گزینه "Public" را انتخاب کنید
5. روی "Create repository" کلیک کنید

#### ۱.۲ آپلود کد به GitHub

```bash
# در پوشه پروژه
git init
git add .
git commit -m "Initial commit: Telegram bot for math courses"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/math-telegram-bot.git
git push -u origin main
```

### مرحله ۲: راه‌اندازی Railway

#### ۲.۱ ثبت‌نام در Railway

1. به [Railway.app](https://railway.app) بروید
2. روی "Start a New Project" کلیک کنید
3. با GitHub وارد شوید
4. Railway را مجاز کنید تا به repository شما دسترسی داشته باشد

#### ۲.۲ ایجاد پروژه جدید

1. روی "Deploy from GitHub repo" کلیک کنید
2. repository `math-telegram-bot` را انتخاب کنید
3. روی "Deploy Now" کلیک کنید

#### ۲.۳ تنظیم متغیرهای محیطی

1. در Railway Dashboard، روی پروژه کلیک کنید
2. به تب "Variables" بروید
3. متغیر جدید اضافه کنید:
   - **Name:** `BOT_TOKEN`
   - **Value:** `YOUR_BOT_TOKEN_HERE`

### مرحله ۳: تست ربات

#### ۳.۱ بررسی لاگ‌ها

1. در Railway Dashboard، روی "Deployments" کلیک کنید
2. آخرین deployment را انتخاب کنید
3. لاگ‌ها را بررسی کنید تا مطمئن شوید ربات بدون خطا اجرا شده است

#### ۳.۲ تست در تلگرام

1. در تلگرام به ربات `@OstadHatami_bot` پیام دهید
2. دستور `/start` را ارسال کنید
3. منوی اصلی باید نمایش داده شود
4. همه گزینه‌ها را تست کنید

## 🔧 عیب‌یابی

### مشکل: ربات پاسخ نمی‌دهد

**راه‌حل:**

1. لاگ‌های Railway را بررسی کنید
2. مطمئن شوید `BOT_TOKEN` درست تنظیم شده است
3. ربات را restart کنید

### مشکل: خطای "BOT_TOKEN not found"

**راه‌حل:**

1. متغیر محیطی `BOT_TOKEN` را دوباره تنظیم کنید
2. پروژه را redeploy کنید

### مشکل: خطای "Cannot close a running event loop"

**راه‌حل:**

1. از فایل `hosted_bot.py` استفاده کنید
2. مطمئن شوید `Procfile` درست تنظیم شده است

## 📊 مانیتورینگ

### بررسی وضعیت ربات

1. در Railway Dashboard، روی پروژه کلیک کنید
2. تب "Metrics" را بررسی کنید
3. CPU و Memory usage را کنترل کنید

### لاگ‌ها

1. تب "Deployments" را باز کنید
2. روی deployment کلیک کنید
3. لاگ‌ها را برای عیب‌یابی بررسی کنید

## 💰 هزینه‌ها

### Railway Free Plan

- **ساعت رایگان:** 500 ساعت در ماه
- **هزینه اضافی:** $5 برای 1000 ساعت اضافی
- **محدودیت:** 1GB RAM, 1GB Storage

### ارتقا به پلن پولی

- **Pro Plan:** $20 در ماه
- **Enterprise Plan:** قیمت بر اساس نیاز

## 🔄 به‌روزرسانی ربات

### تغییرات کد

```bash
# تغییرات را در GitHub push کنید
git add .
git commit -m "Update bot features"
git push origin main
```

### Railway به‌طور خودکار

1. تغییرات را detect می‌کند
2. پروژه را rebuild می‌کند
3. ربات را restart می‌کند

## 📱 تست نهایی

### چک‌لیست تست

- [ ] ربات به دستور `/start` پاسخ می‌دهد
- [ ] منوی اصلی نمایش داده می‌شود
- [ ] گزینه "کلاس‌های ریاضی" کار می‌کند
- [ ] گزینه "کتاب" کار می‌کند
- [ ] گزینه "اطلاعات تماس" کار می‌کند
- [ ] گزینه "شبکه‌های اجتماعی" کار می‌کند
- [ ] دکمه "بازگشت به منو" کار می‌کند

## 🎉 موفقیت

اگر همه چیز درست کار می‌کند، ربات شما:

- ✅ 24/7 در دسترس است
- ✅ از هر جای دنیا قابل دسترسی است
- ✅ به‌طور خودکار restart می‌شود
- ✅ لاگ‌ها را ذخیره می‌کند

## 📞 پشتیبانی

اگر مشکلی داشتید:

- 📧 ایمیل: HamrahBaOstad@gmail.com
- 💬 تلگرام: @Ostad_Hatami
- 📱 واتساپ: +98 938 153 0556

---

**تاریخ:** ۳۱ تیر ۱۴۰۴  
**وضعیت:** ✅ آماده برای استفاده 