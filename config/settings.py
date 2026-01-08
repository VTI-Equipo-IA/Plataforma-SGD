# config/settings.py
import os

def load_config(app):
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PAGE_SIZE"] = int(os.environ.get("PAGE_SIZE", 25))

    # CORS/headers mínimos seguros (puedes ajustar CSP luego)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 20 * 1024 * 1024))  # 20MB
