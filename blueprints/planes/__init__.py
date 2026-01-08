# blueprints/planes/__init__.py
from flask import Blueprint
bp = Blueprint("planes", __name__, url_prefix="/planes", template_folder="../../templates/planes")
from . import routes  # noqa
