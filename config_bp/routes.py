# blueprints/config_bp/routes.py
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from .forms import ConfigForm
from models.app_config import AppConfig
from extensions.db import db
from config.security import encrypt_value, decrypt_value, mask_secret, SecurityConfigError
from services.external_ai_bridge import generate_plan, AIError

def _env_defaults():
    """Lee defaults desde ENV para precargar el formulario si BD está vacía."""
    cfg = current_app.config
    return {
        "provider":     (cfg.get("AI_PROVIDER") or "openai"),
        "model":        (cfg.get("AI_MODEL") or "gpt-4o-mini"),
        "temperature":  cfg.get("AI_TEMPERATURE", 0.7),
        "max_tokens":   cfg.get("AI_MAX_TOKENS", 400),
        "top_p":        cfg.get("AI_TOP_P", 1.0),
        "streaming":    cfg.get("AI_STREAMING", False),
        "retry_max_attempts": cfg.get("AI_RETRY_MAX_ATTEMPTS", 3),
        "retry_backoff_seconds": cfg.get("AI_RETRY_BACKOFF_SECONDS", 2),
    }

def _to_form_initial(app_cfg: AppConfig):
    envd = _env_defaults()
    return {
        "provider": app_cfg.provider or envd["provider"],
        "model": app_cfg.model or envd["model"],
        "temperature": app_cfg.temperature if app_cfg.temperature is not None else envd["temperature"],
        "max_tokens": app_cfg.max_tokens if app_cfg.max_tokens is not None else envd["max_tokens"],
        "top_p": app_cfg.top_p if app_cfg.top_p is not None else envd["top_p"],
        "streaming": bool(app_cfg.streaming) if app_cfg.streaming is not None else bool(envd["streaming"]),
        "retry_max_attempts": app_cfg.retry_max_attempts if app_cfg.retry_max_attempts is not None else envd["retry_max_attempts"],
        "retry_backoff_seconds": app_cfg.retry_backoff_seconds if app_cfg.retry_backoff_seconds is not None else envd["retry_backoff_seconds"],
        # api_key no se rellena por seguridad; se muestra máscara aparte
    }

def _config_as_dict(app_cfg: AppConfig, plain_api_key: str | None):
    """Construye el dict de config para pasar a tu puente IA."""
    return {
        "provider": app_cfg.provider,
        "model": app_cfg.model,
        "api_key": plain_api_key,  # cuidado: no loguear
        "temperature": app_cfg.temperature,
        "max_tokens": app_cfg.max_tokens,
        "top_p": app_cfg.top_p,
        "streaming": bool(app_cfg.streaming) if app_cfg.streaming is not None else False,
        "retry_max_attempts": app_cfg.retry_max_attempts or 0,
        "retry_backoff_seconds": app_cfg.retry_backoff_seconds or 0,
    }

@bp.route("/", methods=["GET", "POST"])
def index():
    app_cfg = AppConfig.get_singleton()

    # Carga inicial del formulario
    form = ConfigForm(data=_to_form_initial(app_cfg))

    # Mostrar máscara si hay key guardada
    masked_key = None
    try:
        plain = decrypt_value(app_cfg.api_key_cipher) if app_cfg.api_key_cipher else None
        masked_key = mask_secret(plain) if plain else ""
    except SecurityConfigError:
        # Clave corrupta o sin FERNET_SECRET
        masked_key = "(clave cifrada ilegible; revisa FERNET_SECRET)"

    # Guardar
    if form.validate_on_submit() and form.submit_save.data:
        app_cfg.provider = form.provider.data
        app_cfg.model = form.model.data.strip()
        app_cfg.temperature = float(form.temperature.data) if form.temperature.data is not None else None
        app_cfg.max_tokens = int(form.max_tokens.data) if form.max_tokens.data is not None else None
        app_cfg.top_p = float(form.top_p.data) if form.top_p.data is not None else None
        app_cfg.streaming = bool(form.streaming.data)
        app_cfg.retry_max_attempts = int(form.retry_max_attempts.data) if form.retry_max_attempts.data is not None else None
        app_cfg.retry_backoff_seconds = float(form.retry_backoff_seconds.data) if form.retry_backoff_seconds.data is not None else None

        # API key: solo se reemplaza si el campo viene con valor
        if form.api_key.data:
            try:
                app_cfg.api_key_cipher = encrypt_value(form.api_key.data.strip())
            except SecurityConfigError as e:
                flash(str(e), "danger")
                return render_template("config/index.html", form=form, masked_key=masked_key)

        try:
            db.session.commit()
            flash("Configuración guardada.", "success")
        except Exception:
            db.session.rollback()
            flash("Error al guardar la configuración.", "danger")

        return redirect(url_for("config_bp.index"))

    # Probar llamada
    if form.validate_on_submit() and form.submit_test.data:
        # Construye config con la clave desencriptada (si existe)
        try:
            plain_key = decrypt_value(app_cfg.api_key_cipher) if app_cfg.api_key_cipher else None
        except SecurityConfigError as e:
            flash(f"Error de cifrado: {e}", "danger")
            return render_template("config/index.html", form=form, masked_key=masked_key)

        test_config = _config_as_dict(app_cfg, plain_key)

        # Fila/entrada mínima para probar tu servicio (no sensible)
        dummy_row = {
            "Brecha": "Prueba de conexión",
            "Dimension": "Config",
            "Subdimension": "Test",
        }
        try:
            # No guardamos nada; solo medimos éxito/latencia simple
            import time
            t0 = time.perf_counter()
            _ = generate_plan("gobernanza-datos", dummy_row, target="diego", config=test_config)
            dt = (time.perf_counter() - t0) * 1000
            flash(f"Prueba exitosa. Latencia ~{dt:.0f} ms.", "success")
        except AIError as e:
            flash(f"Prueba fallida: {e}", "danger")
        except Exception:
            flash("Prueba fallida: error inesperado en el puente IA.", "danger")

        return render_template("config/index.html", form=form, masked_key=masked_key)

    # GET o validación fallida
    if request.method == "POST" and not form.validate():
        flash("Revisa los campos del formulario.", "danger")

    return render_template("config/index.html", form=form, masked_key=masked_key)
