import os
from datetime import datetime, timezone

from flask import Flask, jsonify
from dotenv import load_dotenv
import psycopg2

# Cargar variables de entorno desde .env (en local)
load_dotenv()

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mi_backend_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

app = Flask(__name__)


@app.route("/")
def index():
    """Endpoint principal — información general de la API."""
    return jsonify({
        "servicio": "mi-backend-app",
        "version": "1.0.0",
        "descripcion": "API Flask con PostgreSQL, Docker y CI/CD en Azure",
        "fecha_hora_utc": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "/": "Información general",
            "/health": "Estado de salud del servicio",
            "/db": "Prueba de conexión a la base de datos"
        }
    })


@app.route("/health")
def health():
    """Endpoint de salud — confirma que la app está activa."""
    return jsonify({
        "status": "ok",
        "servicio": "mi-backend-app",
        "mensaje": "La aplicación está funcionando correctamente"
    })


@app.route("/db")
def db_check():
    """Endpoint de prueba de conexión a PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        resultado = cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({
            "status": "ok",
            "base_de_datos": DB_NAME,
            "host": DB_HOST,
            "resultado_select_1": resultado[0],
            "mensaje": "Conexión exitosa a PostgreSQL"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": "No se pudo conectar a PostgreSQL",
            "detalle": str(e)
        }), 500


# Arranque del servidor de desarrollo
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
