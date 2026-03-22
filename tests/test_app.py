# Pruebas UNITARIAS — endpoints / y /health
# No requieren base de datos para ejecutarse


class TestIndex:
    """Tests para el endpoint raíz GET /"""

    def test_index_status_code(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_content_type(self, client):
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_index_contains_servicio(self, client):
        response = client.get("/")
        data = response.get_json()
        assert "servicio" in data
        assert data["servicio"] == "mi-backend-app"

    def test_index_contains_version(self, client):
        response = client.get("/")
        data = response.get_json()
        assert "version" in data

    def test_index_contains_endpoints(self, client):
        response = client.get("/")
        data = response.get_json()
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert "/" in endpoints
        assert "/health" in endpoints
        assert "/db" in endpoints

    def test_index_contains_fecha(self, client):
        response = client.get("/")
        data = response.get_json()
        assert "fecha_hora_utc" in data


class TestHealth:
    """Tests para el endpoint GET /health"""

    def test_health_status_code(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_ok(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_contains_servicio(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert "servicio" in data
        assert data["servicio"] == "mi-backend-app"

    def test_health_contains_mensaje(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert "mensaje" in data
        assert len(data["mensaje"]) > 0


class TestNotFound:
    """Tests para rutas inexistentes"""

    def test_ruta_inexistente(self, client):
        response = client.get("/ruta-que-no-existe")
        assert response.status_code == 404
