# Fixtures compartidas para todos los tests

import sys
import os
import pytest

# Añadir directorio raíz al path para importar app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app


@pytest.fixture
def app():
    """Instancia de Flask en modo testing."""
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba para simular peticiones."""
    return app.test_client()
