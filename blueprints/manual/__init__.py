from flask import Blueprint

bp = Blueprint("manual", __name__, url_prefix="/manual")

from . import routes  # noqa: E402,F401
