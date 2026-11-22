# POMP NET MOHAMMAD — SUPER JINX
قدرت ساخت، آزادی انتخاب، کنترل در دستان تو

نسخه اختصاصی مبتنی بر Marzban و Xray با رابط فارسی و هویت POMP NET.

## سورس مرجع
- https://github.com/x4gpanell/MarzbanUpdate
- https://github.com/Gozargah/Marzban

## برند
- فارسی و RTL
- مشکی #050509، بنفش نئونی #8B35FF و آبی #168CFF
- پیام ورود: کدنویسی و توسعه توسط تیم پمپ نت
- عنوان اشتراک: POMP NET MOHAMMAD
- پشتیبانی: https://t.me/PompNett

## امنیت نصب تازه
در نصب تازه رمز پیش‌فرض admin/admin وجود ندارد. پیش از Deploy در Railway این متغیرها را تنظیم کن:
- ADMIN_USERNAME: نام مدیر، حداقل ۳ نویسه
- ADMIN_PASSWORD: رمز قوی و یکتا، حداقل ۱۴ نویسه
در نصب موجود، حساب مدیر فعلی حفظ می‌شود. بازیابی رمز فقط با RESET_ADMIN_PASSWORD=1 به همراه ADMIN_USERNAME و ADMIN_PASSWORD انجام می‌شود؛ پس از بازیابی RESET را حذف کن.
هرگز رمز، توکن ربات، کلید خصوصی یا Recovery Code را در GitHub قرار نده.

## Railway
- Builder: Dockerfile
- پورت داخلی HTTP: 8080
- Healthcheck: /health
- Volume پایدار الزامی: /var/lib/marzban
- دامنه HTTPS از Railway
- مسیر ساب از endpoint واقعی هسته می‌آید؛ افزودن :2096 به دامنه Railway به‌تنهایی پورت عمومی 2096 نمی‌سازد.

## وضعیت تحویل
فایل‌های اصلی اجرایی شامل Dockerfile، start.sh، nginx.conf، jinx.css/js، jinx_api.py، sub.html، فایل‌های پیکربندی Xray، lock.py، enforce_hosts.py، ensure_admin.py، doctor.py، donate و قطعات Nginx وارد شده و برای برند POMP NET تغییر داده شده‌اند.
این نسخه هنوز Deploy یا تست عملیاتی نشده است. انتقال همه دارایی‌های جانبی، Docker build، API، Xray، ورود، ساخت کاربر، لینک اشتراک و ماندگاری Volume باید آزمایش شود.

## مجوز
مجوزها و اعلان‌های حق‌نشر کدهای بالادستی باید حفظ شوند. این مخزن ادعای مالکیت هسته Marzban یا کد اشخاص ثالث را ندارد.