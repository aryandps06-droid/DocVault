"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import shutil
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Copy SQLite database to writable /tmp directory if running on Vercel
if 'VERCEL' in os.environ:
    db_source = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    db_dest = '/tmp/db.sqlite3'
    if os.path.exists(db_source) and not os.path.exists(db_dest):
        shutil.copy2(db_source, db_dest)

application = get_wsgi_application()

# Vercel requires 'app' variable to be exposed
app = application
