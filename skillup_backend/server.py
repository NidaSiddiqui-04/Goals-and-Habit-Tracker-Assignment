# serve.py
import os
from waitress import serve
from skillup_backend.wsgi import application  # Adjust the import based on your project

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillup_backend.settings")

serve(application, host="localhost", port=8000)
