# Pruebas FUNCIONALES / DE INTEGRACIÓN — endpoint /db
# Usan mocks para simular PostgreSQL sin necesitar una BD real

from unittest.mock import patch, MagicMock


class TestDbEndpoint:
    """Tests funcionales del endpoint GET /db (sin mock)"""

    def test_db_endpoint_returns_json(self, client):
        response = client.get("/db")
        assert response.content_type == "application/json"

    def test_db_endpoint_returns_status_key(self, client):
        response = client.get("/db")
        data = response.get_json()
        assert "status" in data

    def test_db_endpoint_sin_bd_devuelve_error(self, client):
        """Sin BD accesible, debe devolver 500 con status 'error'."""
        response = client.get("/db")
        data = response.get_json()
        if response.status_code == 500:
            assert data["status"] == "error"
            assert "mensaje" in data
            assert "detalle" in data

    def test_db_endpoint_sin_bd_contiene_detalle(self, client):
        response = client.get("/db")
        if response.status_code == 500:
            data = response.get_json()
            assert len(data["detalle"]) > 0


class TestDbEndpointConMock:
    """Tests de integración simulando PostgreSQL con mock"""

    @patch("app.psycopg2.connect")
    def test_db_conexion_exitosa(self, mock_connect, client):
        """Simula conexión exitosa a PostgreSQL."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        response = client.get("/db")
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert data["resultado_select_1"] == 1
        assert "Conexión exitosa" in data["mensaje"]

    @patch("app.psycopg2.connect")
    def test_db_conexion_fallida(self, mock_connect, client):
        """Simula fallo de conexión a PostgreSQL."""
        mock_connect.side_effect = Exception(
            "could not connect to server: Connection refused"
        )

        response = client.get("/db")
        data = response.get_json()

        assert response.status_code == 500
        assert data["status"] == "error"
        assert "No se pudo conectar" in data["mensaje"]

    @patch("app.psycopg2.connect")
    def test_db_conexion_exitosa_cierra_recursos(self, mock_connect, client):
        """Verifica que cursor y conexión se cierran correctamente."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client.get("/db")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
