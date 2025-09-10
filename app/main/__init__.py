# -*- coding: utf-8 -*-
"""
Blueprint الرئيسي
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes
