# -*- coding: utf-8 -*-
"""
Blueprint الطلاب
"""

from flask import Blueprint

bp = Blueprint('student', __name__)

from app.student import routes
