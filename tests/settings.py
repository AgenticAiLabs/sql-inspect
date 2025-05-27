SECRET_KEY = "secret_key"
ROOT_URLCONF = "demo_app.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "demo_app",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

USE_TZ = False

DEBUG = True
