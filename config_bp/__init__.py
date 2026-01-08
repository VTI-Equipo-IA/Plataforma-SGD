# models/app_config.py
from datetime import datetime
from extensions.db import db

class AppConfig(db.Model):
    __tablename__ = "app_config"

    id = db.Column(db.Integer, primary_key=True)  # singleton (id=1)
    provider = db.Column(db.String(64), nullable=True)
    model = db.Column(db.String(128), nullable=True)
    api_key_cipher = db.Column(db.Text, nullable=True)

    temperature = db.Column(db.Float, nullable=True)
    max_tokens = db.Column(db.Integer, nullable=True)
    top_p = db.Column(db.Float, nullable=True)
    streaming = db.Column(db.Boolean, nullable=True)

    retry_max_attempts = db.Column(db.Integer, nullable=True)
    retry_backoff_seconds = db.Column(db.Float, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_singleton():
        inst = AppConfig.query.get(1)
        if not inst:
            inst = AppConfig(id=1)
            db.session.add(inst)
            # No commit automático aquí; el caller decide
        return inst
