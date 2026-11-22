<div align="center">

<img src="assets/pompnet-super-jinx-hero.svg" alt="POMP NET MOHAMMAD — SUPER JINX" width="100%"/>

<br/>

[![Brand](https://img.shields.io/badge/BRAND-POMP%20NET%20MOHAMMAD-8B35FF?style=for-the-badge)](https://github.com/uxurx7rh7e7xr73uue73e8)
[![Core](https://img.shields.io/badge/CORE-MARZBAN-168CFF?style=for-the-badge)](https://github.com/Gozargah/Marzban)
[![Engine](https://img.shields.io/badge/ENGINE-XRAY-8B35FF?style=for-the-badge)](https://github.com/XTLS/Xray-core)
[![Status](https://img.shields.io/badge/STATUS-IN%20DEVELOPMENT-orange?style=for-the-badge)](#-وضعیت-واقعی-پروژه)

### قدرت ساخت، آزادی انتخاب، کنترل در دستان تو

**پنل اختصاصی مدیریت Marzban با هویت POMP NET و رابط کاربری SUPER JINX**

[گروه پمپ‌نت](https://t.me/PompNett) • [کانال رسمی](https://t.me/pompnet) • [کانال پروکسی](https://t.me/Myporoxy18) • [GitHub سازنده](https://github.com/uxurx7rh7e7xr73uue73e8)

</div>

---

## ✦ درباره پروژه

**POMP NET MOHAMMAD — SUPER JINX** یک پروژه سفارشی‌سازی‌شده بر پایه Marzban است. هدف، حفظ هسته و منطق اصلی مدیریت کاربران و سرویس‌ها، در کنار ارائه هویت بصری اختصاصی پمپ‌نت است.

> این مخزن در مرحله تکمیل و اعتبارسنجی است؛ وجود فایل در GitHub به معنی تست‌شدن یا آماده‌بودن آن برای استفاده عملیاتی نیست.

## ◈ هویت بصری

| بخش | مشخصات |
|---|---|
| نام پروژه | POMP NET MOHAMMAD — SUPER JINX |
| زبان رابط | فارسی و راست‌چین (RTL) |
| پس‌زمینه | مشکی عمیق `#050509` |
| رنگ اصلی | بنفش نئونی `#8B35FF` |
| رنگ مکمل | آبی نئونی `#168CFF` |
| پیام صفحه ورود | کدنویسی و توسعه توسط تیم پمپ نت |
| عنوان اشتراک | POMP NET MOHAMMAD |
| پشتیبانی | [@PompNett](https://t.me/PompNett) |

## ⚡ امکانات و اجزای موجود در سورس

- هسته مدیریتی مبتنی بر Marzban
- فایل‌های رابط و پوسته اختصاصی Jinx
- صفحه اشتراک سفارشی
- تنظیمات Nginx و مسیرهای WebSocket
- فایل‌های پیکربندی Xray و ابزار قفل/ساخت تنظیمات
- ابزارهای مدیریتی و بررسی سلامت
- مدیریت امن حساب مدیر در نصب تازه و ری‌استارت
- صفحه حمایت و تنظیمات مربوط به آن

**توجه:** این فهرست، اجزای موجود در مخزن را معرفی می‌کند و تأیید عملکرد عملیاتی تک‌تک آن‌ها نیست.

## 🔐 امنیت حساب مدیر

در نصب تازه، ورود پیش‌فرض `admin/admin` استفاده نمی‌شود.

متغیرهای لازم برای ساخت مدیر اولیه:

| متغیر | الزام |
|---|---|
| `ADMIN_USERNAME` | حداقل ۳ نویسه |
| `ADMIN_PASSWORD` | حداقل ۱۴ نویسه و غیرقابل حدس |

- در ری‌استارت عادی، حساب و رمز مدیر موجود باید حفظ شود.
- تغییر رمز فقط با تنظیم صریح `RESET_ADMIN_PASSWORD=1` و ارائه نام کاربری و رمز جدید انجام می‌شود.
- پس از بازیابی رمز، متغیر `RESET_ADMIN_PASSWORD` را حذف کنید.
- هیچ رمز، توکن یا کلید محرمانه‌ای را داخل کد یا GitHub قرار ندهید.

## 🧭 وضعیت واقعی پروژه

<div align="center">

| مورد | وضعیت |
|:---|:---:|
| مخزن اختصاصی POMP NET | 🟢 ایجاد شده |
| سفارشی‌سازی برند و لینک‌های رسمی | 🟢 انجام شده |
| انتقال ۱۹ فایل اجرایی مرجع | 🟢 همه موجود؛ فایل‌های برند/امنیت به‌صورت هدفمند اصلاح شده‌اند |
| بررسی وابستگی‌ها و اجرای image در کانتینر | 🟢 موفق در CI |
| بررسی نحوی Shell/Python/JSON | 🟢 موفق در GitHub Actions |
| ساخت Docker image | 🟢 موفق در GitHub Actions |
| ورود مدیر و ساخت حساب اولیه | 🟢 تست runtime موفق |
| ساخت کاربر واقعی از API | 🟢 تست runtime موفق |
| هندشیک WebSocket از Nginx تا Xray | 🟢 پاسخ 101 موفق |
| دریافت URL و پاسخ endpoint اشتراک | 🟢 تست runtime موفق |
| ماندگاری دیتابیس و مسیر ساب پس از بازسازی کانتینر | 🟢 تست runtime موفق |
| تست نهایی دامنه عمومی/TLS و اتصال از کلاینت واقعی | ⚪ باقی‌مانده |
| آماده استقرار تولیدی | 🟡 پس از تست روی VPS مجاز |

</div>

### 📦 وضعیت انتقال فایل‌ها

- سورس مرجع [MarzbanUpdate](https://github.com/x4gpanell/MarzbanUpdate) در زمان بررسی شامل ۸۴ مورد (فایل و پوشه) بود.
- بخش زیادی از این موارد، مستندات چندزبانه، تصاویر، badgeها و اسکرین‌شات‌ها هستند و فایل اجرایی پنل نیستند.
- مخزن اختصاصی شامل فایل‌های عملیاتی سفارشی، پوسته، API کمکی، صفحه اشتراک، تنظیمات Xray/Nginx و ابزارهای مدیریتی است.
- هسته Marzban از image پایه `gozargah/marzban:latest` دریافت می‌شود؛ بنابراین این پروژه بسته استقرار و سفارشی‌سازی MarzbanUpdate است، نه کپی کامل سورس Marzban.
- فایل `iran-relay.sh` عمداً منتقل نشده؛ برای اجرای خود پنل لازم نیست و به مسیر‌دهی ترافیک از طریق میزبان ثالث مربوط است.

### 🧪 تست‌های عملیاتی ثبت‌شده

در GitHub Actions، نسخه‌ی ساخته‌شده داخل کانتینر واقعی Docker اجرا شد (نه فقط lint یا build). تست Run #9 با موفقیت تمام شد:

1. ساخت image Docker: موفق.
2. اجرای سرویس و پاسخ Health: موفق.
3. ورود مدیر از API با رمز موقت آزمایشی: موفق.
4. ساخت کاربر آزمایشی از API و دریافت URL اشتراک: موفق.
5. درخواست endpoint اشتراک: موفق.
6. هندشیک واقعی WebSocket از Nginx به inbound مربوط به Xray و دریافت HTTP 101: موفق.
7. توقف و بازسازی کانتینر با همان Volume؛ ورود دوباره، باقی‌ماندن کاربر و ثابت‌ماندن مسیر مخفی ساب: موفق.

**محدودیت تست:** این آزمایش در محیط موقت GitHub runner انجام شده است. اتصال از اینترنت عمومی با دامنه و TLS واقعی، واردکردن لینک در v2rayNG/Hiddify و عبور ترافیک واقعی از یک VPS هنوز روی زیرساخت نهایی کاربر آزمایش نشده است. بنابراین تست runtime موفق است، اما هنوز ادعای استقرار تولیدی یا تست کلاینت بیرونی نداریم.

**گزارش کامل اجرا:** [GitHub Actions — Run #9](https://github.com/uxurx7rh7e7xr73uue73e8/POMP-NET-MOHAMMAD-SUPER-JINX/actions/runs/45068792432)

## 🚀 استقرار و زیرساخت

این پروژه سرویس VPN/Proxy مبتنی بر Xray است. پیش از انتخاب میزبان، سیاست استفاده ارائه‌دهنده را بررسی کنید و در صورت نیاز تأیید کتبی بگیرید. **برای دور زدن محدودیت‌های میزبان، ماهیت سرویس را پنهان نکنید.**

برای استقرار عملیاتی، محیطی انتخاب شود که میزبانی این نوع سرویس را صراحتاً مجاز بداند و امکان ذخیره‌سازی پایدار فراهم کند. مسیر داده برنامه در این نسخه:

`/var/lib/marzban`

پورت داخلی وب در پیکربندی فعلی:

`8080`

وجود این مقادیر به معنی تست موفق استقرار نیست. استقرار روی Railway در این پروژه تأیید نشده و به‌دلیل محدودیت‌های میزبانی سرویس‌های VPN/Proxy، توصیه نمی‌شود مگر اینکه مجوز صریح ارائه‌دهنده دریافت شود.

## 🧩 منابع و اعتبار

- پروژه پایه: [Marzban](https://github.com/Gozargah/Marzban)
- سورس مرجع سفارشی‌سازی: [MarzbanUpdate](https://github.com/x4gpanell/MarzbanUpdate)
- هسته ارتباطی: [Xray-core](https://github.com/XTLS/Xray-core)

این پروژه بر پایه نرم‌افزارهای بالادستی ساخته می‌شود. حقوق، مجوزها و اعلان‌های حق‌نشر هر جزء باید مطابق مجوز اصلی آن حفظ شوند. این مخزن ادعای مالکیت هسته Marzban، Xray یا کد اشخاص ثالث را ندارد.

## 💬 ارتباط با پمپ‌نت

<div align="center">

[![Telegram Group](https://img.shields.io/badge/TELEGRAM-GROUP-168CFF?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/PompNett)
[![Telegram Channel](https://img.shields.io/badge/TELEGRAM-CHANNEL-8B35FF?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/pompnet)
[![Proxy Channel](https://img.shields.io/badge/PROXY-CHANNEL-168CFF?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/Myporoxy18)
[![GitHub](https://img.shields.io/badge/GITHUB-PROFILE-8B35FF?style=for-the-badge&logo=github&logoColor=white)](https://github.com/uxurx7rh7e7xr73uue73e8)

**POMP NET MOHAMMAD — SUPER JINX**

- گروه گفتگو: [@PompNett](https://t.me/PompNett)
- کانال رسمی: [@pompnet](https://t.me/pompnet)
- کانال پروکسی: [@Myporoxy18](https://t.me/Myporoxy18)
- پشتیبانی: [@NovaTunneli](https://t.me/NovaTunneli)
- توسعه‌دهنده: [@developer_as](https://t.me/developer_as)
- GitHub: [uxurx7rh7e7xr73uue73e8](https://github.com/uxurx7rh7e7xr73uue73e8)

قدرت ساخت، آزادی انتخاب، کنترل در دستان تو

</div>
