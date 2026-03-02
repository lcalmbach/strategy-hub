import os
from importlib.util import find_spec
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def dedupe_list(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def sqlite_database_config() -> dict:
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }


def database_config_from_env() -> dict:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return sqlite_database_config()

    parsed = urlparse(database_url)
    scheme = parsed.scheme

    if scheme in {"postgres", "postgresql", "pgsql"}:
        query = parse_qs(parsed.query)
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "600")),
            "OPTIONS": {
                key: values[-1]
                for key, values in query.items()
                if values
            },
        }

    if scheme == "sqlite":
        sqlite_path = parsed.path or "/db.sqlite3"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }

    raise ValueError(f"Unsupported DATABASE_URL scheme: {scheme}")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "testserver"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

heroku_app_name = os.getenv("HEROKU_APP_NAME")
if heroku_app_name:
    heroku_host = f"{heroku_app_name}.herokuapp.com"
    ALLOWED_HOSTS = dedupe_list([*ALLOWED_HOSTS, heroku_host])
    CSRF_TRUSTED_ORIGINS = dedupe_list([*CSRF_TRUSTED_ORIGINS, f"https://{heroku_host}"])

if not DEBUG and SECRET_KEY == "django-insecure-change-me":
    raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")

if not DEBUG and "DATABASE_URL" not in os.environ:
    raise RuntimeError("DATABASE_URL must be set when DJANGO_DEBUG is false.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "iommi",
    "core",
    "people",
    "strategies",
    "controlling",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "iommi.main_menu.main_menu_middleware",
    "iommi.middleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if find_spec("whitenoise") is not None:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.active_strategy",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": database_config_from_env(),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "de-ch"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "").strip()
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "").strip()
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "").strip()
AWS_MEDIA_LOCATION = os.getenv("AWS_MEDIA_LOCATION", "").strip("/")
AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", False)

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

if AWS_STORAGE_BUCKET_NAME:
    media_domain = AWS_S3_CUSTOM_DOMAIN or (
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
        if AWS_S3_REGION_NAME
        else f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    )
    media_path = f"/{AWS_MEDIA_LOCATION}/" if AWS_MEDIA_LOCATION else "/"
    MEDIA_URL = f"https://{media_domain}{media_path}"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

if AWS_STORAGE_BUCKET_NAME and find_spec("storages") is not None:
    s3_options = {
        "bucket_name": AWS_STORAGE_BUCKET_NAME,
        "querystring_auth": AWS_QUERYSTRING_AUTH,
    }
    if AWS_S3_REGION_NAME:
        s3_options["region_name"] = AWS_S3_REGION_NAME
    if AWS_MEDIA_LOCATION:
        s3_options["location"] = AWS_MEDIA_LOCATION
    if AWS_S3_CUSTOM_DOMAIN:
        s3_options["custom_domain"] = AWS_S3_CUSTOM_DOMAIN

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": s3_options,
    }

if find_spec("whitenoise") is not None:
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
IOMMI_DEFAULT_STYLE = "bootstrap5"
IOMMI_MAIN_MENU = "config.menu.main_menu"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
