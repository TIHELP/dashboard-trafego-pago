"""Entrypoint WSGI usado pela Vercel (runtime @vercel/python detecta a variável `app`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_app import app  # noqa: E402
