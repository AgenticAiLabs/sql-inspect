SECRET_KEY="secret_key"
ROOT_URLCONF = ""

INSTALLED_APPS = [
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "demo_app"
]

MIDDLEWARE = [
  "django.middleware.common.CommonMiddleware",
  "sql-inspect.middleware.SQLInspectMiddleware"
]

DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.sqlite3"
  }
}

USE_TZ = False