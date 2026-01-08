# app.py
import os
from flask import Flask, send_from_directory
from dotenv import load_dotenv
from config.settings import load_config
from extensions.db import db
from extensions.csrf import csrf

# Cargar variables de entorno desde .env
load_dotenv()

def create_app():
    app = Flask(__name__)
    load_config(app)

    # Extensiones
    db.init_app(app)
    csrf.init_app(app)

    # Blueprints
    from blueprints.planes import bp as planes_bp
    app.register_blueprint(planes_bp)

    from blueprints.prompts import prompts_bp
    app.register_blueprint(prompts_bp)

    from blueprints.manual import bp as manual_bp
    app.register_blueprint(manual_bp)

    # Compatibilidad: rutas antiguas que apuntaban al manual
    from flask import redirect, url_for

    @app.get("/manual")
    @app.get("/manual/")
    def manual_legacy_redirect():
        return redirect(url_for("manual.index"), code=301)

    @app.get("/editor-planes/manual")
    @app.get("/editor-planes/manual/")
    def manual_legacy_editor_planes_redirect():
        return redirect(url_for("manual.index"), code=301)

    # (Opcional) Configuración de IA si la expones
    try:
        from blueprints.config_bp import bp as config_bp
        app.register_blueprint(config_bp)
    except Exception:
        pass

    @app.route("/")
    def index():
        # Redirige a la página principal de planes
        return redirect(url_for("planes.index"))
    
    @app.route("/health")
    def health():
        return "OK"

    # Servir imágenes desde la carpeta 'img' en la raíz del proyecto
    @app.route("/img/<path:filename>")
    def img_file(filename: str):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        # La carpeta 'img' está al lado de app.py (raíz del proyecto)
        return send_from_directory(os.path.join(root_dir, "img"), filename)

    return app

if __name__ == "__main__":
    app = create_app()
    # No ejecutes en producción con debug=True
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
