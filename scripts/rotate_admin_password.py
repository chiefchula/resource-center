"""
Rotate the admin user's password.

Usage:
    cd ~/rescue-center
    source venv/bin/activate   (or ~/.virtualenvs/venv/bin/activate)
    set -a; source .env; set +a
    python scripts/rotate_admin_password.py
"""
import os
import sys
from getpass import getpass

# Make the project root importable so `from run import app` works
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from run import app
from app import db
from app.models import User