#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI entry point for the application
"""

import os
from app import create_app

# Get the application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()