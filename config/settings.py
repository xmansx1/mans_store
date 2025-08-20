from pathlib import Path
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من .env (محلياً)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------- أمان/بيئة -----------------
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# ----------------- اللغة والمنطقة -----------------
LANGUAGE_CODE = "ar"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Riyadh")
USE_I18N = True
USE_TZ = True

# ----------------- التطبيقات -----------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # تطبيقات المشروع
    "products",

    # Cloudinary للتخزين السحابي
    "cloudinary",
    "cloudinary_storage",
]

# ----------------- Middleware -----------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # لخدمة الملفات الثابتة بالإنتاج
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ----------------- قاعدة البيانات -----------------
# SQLite للتطوير (يمكن استبدالها بـ PostgreSQL لاحقاً)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ----------------- الملفات الثابتة -----------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"          # للإنتاج
STATICFILES_DIRS = [BASE_DIR / "static"]        # أثناء التطوير

STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},  # رفع media إلى Cloudinary
}

# ----------------- Cloudinary -----------------
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")

# ----------------- إعدادات تيليجرام للتنبيهات -----------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true" and bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# ----------------- LOGGING -----------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "products": {"handlers": ["console"], "level": "INFO", "propagate": True},
    },
}

# ----------------- إعدادات أمن إضافية (للإنتاج) -----------------
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
