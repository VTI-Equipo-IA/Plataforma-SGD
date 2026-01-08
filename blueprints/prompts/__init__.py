# -*- coding: utf-8 -*-
"""
Blueprint para gestión de prompts del Agente Maestro
"""
from flask import Blueprint

prompts_bp = Blueprint(
    'prompts',
    __name__,
    url_prefix='/prompts',
    template_folder='../../templates/prompts'
)

from . import routes
