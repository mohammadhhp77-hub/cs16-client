# ASiA-GaME — Source Patch v4 (C++ / CS16Client)

**این آرشیو APK نیست؛ پچ سورس منوی همان بازی CS16Client است.** فایل APK اصلی، اسکین‌ها، فایل‌های cstrike/valve و بک‌گراند تأییدشده تغییر نکرده‌اند.

## اصلاحات واقعی نسخه v4

- چهار گزینه `CMenuAction` **متنی و قابل کلیک** در منوی اصلی؛ بدون تصویر، بک‌گراند یا مستطیل.
- Public 1 با نام دقیق `ASiA-GaME | Top Player's ServeR` و اتصال به `Servercs.ir:27015`، و Public 2 تا 4 به پورت‌های 27013، 27022، 27012. فرمان‌ها اکنون مطابق رویه `OnActivateEntry` خود سورس، آرگومان‌های نقل‌قول‌شده دارند: `connect "host:port" "gs"`.
- حذف توصیف‌های توضیحی منو با برداشتن `QMF_NOTIFY` بدون حذف دکمه‌های منوی اصلی.
- ذخیره **هر دو وضعیت** Favorite و Unfavorite بلافاصله پس از تغییر، افزون بر ذخیره فوری Add Server.
- Add Server از همان ابتدا `favorited=true` ثبت می‌شود؛ قبلاً `false` بود و در ذخیره‌سازی نادیده گرفته می‌شد.
- اولین اجرای منوی Browser: ۱۸ سرور ASiA-GaME با **حفظ Favoriteهای قدیمی** و **بدون تکرار** اضافه می‌شوند. نشانگر `asiagame_favorites_initialized.dat` باعث می‌شود حذف‌های عمدی کاربر در اجراهای بعدی برنگردند.
- پشتیبانی از مسیر صحیح سورس `cs16-client/3rdparty/mainui_cpp`، همراه با بررسی تمام anchorها قبل از نوشتن، بکاپ `.asiagame.bak` و جلوگیری از دوباره‌نویسی.

## اجرای آماده‌سازی در محیط لینوکس

بهتر است از همان سورس CS16Client استفاده شود که APK پایه از آن ساخته شده؛ مراجعه به نسخه `main` به‌تنهایی **هم‌خوانی ABI با APK فعلی را تضمین نمی‌کند**. در صورت استفاده از سورس جدید:

```bash
git clone --recursive https://github.com/FWGS/cs16-client.git
python3 tests/test_patch.py
python3 tests/compile_patch_fragments.py
python3 apply_source_patch.py /path/to/cs16-client
python3 apply_source_patch.py /path/to/cs16-client --apply
```

دستورهای Python را از داخل پوشه استخراج‌شده همین پچ اجرا کن. خط اول در محلی دلخواه سورس را دانلود می‌کند؛ مسیر `/path/to/cs16-client` باید به مسیر واقعی کلون تغییر داده شود. اگر سورس با anchorها مطابقت نداشته باشد، **پچ بدون تغییر فایل‌ها متوقف می‌شود** تا قبل از کامپایل به سورس غلط آسیب نزند.

### پیش‌نیازهای مرحله ساخت APK

- **Android NDK/SDK و ابزارهای بیلد رسمی CS16Client**؛ فایل‌های سورس کامل خود پروژه و submoduleها.
- در کتابخانه arm64 داخل APK پایه، نشانه ابزار کامپایل **Android NDK r28c / clang 19.0.1** و API 21 مشاهده شد. این فقط راهنمای تطبیق محیط است.
- همان سه ABI پایه: `arm64-v8a`, `armeabi-v7a`, `x86`؛ نام فایل‌های جایگزین باید دقیقاً مشابه کتابخانه‌های داخل APK باشد.
- APK پس از تغییر، به بسته‌بندی و امضای جدید نیاز دارد. نصب کنار نسخه اصلی، علاوه بر package ID جداگانه، نیازمند بررسی مسیر داده مشترک Xash است: تغییر شناسه APK به‌تنهایی داده‌های `Xash/cstrike` را مستقل نمی‌کند.
- فایل `assets/cstrike/favorite_servers.lst` یک **فایل مرجع ۱۸ سرور** است؛ کد v4 این فهرست را در اولین اجرا به طور خودکار می‌سازد. آن را روی دیتای فعلی گوشی کپی نکن.

## آزمون‌هایی که در این محیط واقعاً اجرا شده‌اند

- `tests/test_patch.py`: ۱۸ آدرس و ۴ اتصال؛ جلوگیری از اعمال دوباره؛ بکاپ‌گیری؛ عدم تغییر منبع ناسازگار؛ درستی عبارت فرمان.
- `tests/compile_patch_fragments.py`: کامپایل و اجرای C++ بخش‌های تزریق‌شده با **API شبیه‌سازی‌شده**؛ بررسی merge سرورهای قبلی، جلوگیری از تکرار، پاک‌کردن Favorites و seed نصب تازه.
- آزمون‌های فوق **کامپایل کامل mainui_cpp با Android NDK نیستند**. هنوز نمی‌شود تضمین کرد بیلد در تلاش اول بدون خطا خواهد بود. پچ برای توقف زودهنگام و واضح در صورت ناسازگاری طراحی شده است.

## منبع واقعی ساختار فایل‌ها

- https://github.com/FWGS/cs16-client
- https://github.com/FWGS/mainui_cpp
- https://raw.githubusercontent.com/FWGS/mainui_cpp/master/menus/Main.cpp
- https://raw.githubusercontent.com/FWGS/mainui_cpp/master/menus/ServerBrowser.cpp
- https://raw.githubusercontent.com/FWGS/mainui_cpp/master/controls/BaseItem.h

**مهم:** بدون سورس منطبق با دقیقاً همان revision کتابخانه APK و یک کامپایل کامل در NDK، هیچ کس نمی‌تواند صحت بی‌خطای اولین بیلد و کارکرد موبایل را تضمین کند. این پچ برای آماده‌سازی آن بیلد است؛ APK نهایی محسوب نمی‌شود.
