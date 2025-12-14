# Bog‘cha CRM (Django)

Bu loyiha — bog‘cha uchun oddiy full-stack Django 5.x + Bootstrap 5 ilovasi. U quyidagilarni boshqarish uchun mo‘ljallangan:
- Guruhlar
- Bolalar
- Vasiylar

## GitHub’dan klonlash

Repo’ni kompyuteringizga yuklab olish:

```bash
git clone <REPO_URL>
cd kindergarten-crm
```

`<REPO_URL>` o‘rniga GitHub’dagi repo havolasini qo‘ying.

## Lokal ishga tushirish (SQLite)

Quyidagi qadamlar SQLite bilan tez ishga tushirish uchun:

### 1) Virtual muhit (venv) yaratish

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Kutubxonalarni o‘rnatish

```bash
pip install -r requirements.txt
```

### 3) Muhit sozlamalari (.env)

```bash
cp .env.example .env
```

So‘ng `.env` ichida kamida `SECRET_KEY` ni o‘rnating.

### 4) Migratsiyalar

```bash
python manage.py migrate
```

### 5) Superadmin (superuser) yaratish

Admin panelga kirish uchun superuser yarating:

```bash
python manage.py createsuperuser
```

Kiritgan login/parolingiz bilan `/admin/` ga kira olasiz.

### 6) Demo maʼlumotlar (seeder)

```bash
python manage.py seed_demo_data
```

### 7) Serverni ishga tushirish

```bash
python manage.py runserver
```

`core` ilovasi CRUD sahifalarini (kirish talab qilinadi) va ommaviy bosh sahifani taqdim etadi.

## Talablar

- Python 3.11+ (ushbu repo 3.11/3.12 bilan ishlaydi)
- PostgreSQL (ixtiyoriy; SQLite standart holatda ishlaydi)

Ochish:
- http://127.0.0.1:8000/ (ommaviy bosh sahifa)
- http://127.0.0.1:8000/classrooms/ (CRUD; kirish talab qilinadi)
- http://127.0.0.1:8000/admin/ (admin)

## PostgreSQL

`.env` faylida `DATABASE_URL` ni sozlang, masalan:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kindergarten_crm
```

So‘ng ishga tushiring:

```bash
python manage.py migrate
python manage.py runserver
```

## Avtorizatsiya

Ushbu loyiha Django’ning standart autentifikatsiyasidan foydalanadi:
- Kirish: `/accounts/login/`
- Chiqish: `/accounts/logout/`
- Parolni tiklash: `/accounts/password_reset/`

Parolni tiklash xabarlari Django’ning console email backend’i orqali terminal (konsol)ga chiqariladi.

## Eslatmalar

- Maxfiy ma’lumotlar repoga kiritilmagan. Hammasini `.env` / environment variables orqali sozlang.
- Static/media sozlamalari development uchun. Production’da static fayllarni web server orqali serve qiling.

## Davomat

- Davomat ro‘yxati: `/attendance/`
- Sanani tanlang va xohlasangiz guruh/holat bo‘yicha filter qiling.
- Agar tanlangan sanada davomat yozuvlari bo‘lmasa, ilova barcha **Faol** bolalar uchun avtomatik `Expected` (Kutilmoqda) yozuvlarini yaratadi.
- Qator tugmalari orqali tezda Keldi/Kechikdi/Kelmagan/Yarim kun holatini belgilang yoki **Tahrirlash** orqali kirish/chiqish vaqti, sabab va izohlarni kiriting.
- Guruhni ommaviy “Keldi” deb belgilash uchun avval guruh filterini tanlang, so‘ng **Bulk mark Present** tugmasidan foydalaning.

## To‘lov

### Oylik to‘lov (soddalashtirilgan)

- Oylik to‘lov sahifasi: `/billing/monthly/`
- Oyni tanlang (`YYYY-MM`) va xohlasangiz filter/qidiruvdan foydalaning.
- Davomat kabi, oy ochilganda barcha **Faol** bolalar uchun yozuvlar avtomatik yaratiladi.
- Avtomatik yaratilgan yozuv summasi bolaning biriktirilgan tarifi bo‘yicha olinadi (tarif bo‘lmasa `0`).
- **Mark Paid** / **Mark Unpaid** tugmalari orqali holatni o‘zgartiring; belgilash faqat `bola id + oy` orqali ishlaydi.

### Tariflar

- Tariflarni boshqarish: `/tariffs/` (yaratish/tahrirlash/o‘chirish)
- Bolaga tarif biriktirish: bola qo‘shish/tahrirlash formasi orqali.

Ilova atayin faqat soddalashtirilgan oylik to‘lov oqimidan foydalanadi (har bir bola + har bir oy uchun bitta yozuv).
