# نود واقعی POMP NET (Marzban Node)

این سرویس یک نود Xray مستقل برای هسته Marzban پنل فعلی POMP NET است؛ جایگزین پنل نیست و به SideRail متصل نمی‌شود.

## پیش‌نیاز
- یک VPS لینوکسی مستقل با IP عمومی و دسترسی root
- Docker و Docker Compose
- دسترسی به پنل POMP NET برای دریافت گواهی کلاینت نود

## نصب
1. در پنل POMP NET وارد Node Settings شوید و یک Node جدید بسازید/گواهی کلاینت (Client Certificate) را نمایش دهید.
2. این پوشه را روی VPS نود دریافت کنید.
3. اجرا کنید: `sudo bash install.sh`
4. گواهی PEM را در ورودی اسکریپت Paste کنید.
5. در پنل، Node را با IP عمومی VPS و پورت سرویس `62050` ثبت کنید. API Port پیش‌فرض `62051` است.
6. پورت TCP سرویس نود را فقط از سمت پنل قابل دسترس کنید؛ پورت‌های inbound انتخاب‌شده باید برای کلاینت‌ها باز باشند.

## بررسی
```bash
docker compose --env-file /opt/pompnet-node.env -f /opt/pompnet-node-compose.yml ps
docker compose --env-file /opt/pompnet-node.env -f /opt/pompnet-node-compose.yml logs --tail=100
```

نکته: GitHub و Railway نمی‌توانند بدون یک VPS دارای IP عمومی، نود VPN مستقل ایجاد کنند. این پوشه سرویس نود را آماده می‌کند؛ اجرای آن روی VPS و ثبت IP/گواهی در پنل الزامی است. این مخزن به‌تنهایی VPS جدید provision نمی‌کند.
