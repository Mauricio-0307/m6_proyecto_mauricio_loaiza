# MI-BACKEND-APP — CI/CD con Flask, PostgreSQL, Docker y Azure

## Descripción del proyecto

Aplicación backend desarrollada con Python y Flask que implementa una API REST conectada a una base de datos PostgreSQL. El proyecto está contenerizado con Docker, orquestado con Docker Compose para entorno local, y desplegado en Azure Container Apps mediante un pipeline CI/CD en GitHub Actions.

El pipeline incluye **pruebas automatizadas con pytest** como paso obligatorio antes del despliegue: si los tests fallan, la imagen no se construye ni se despliega. Esto garantiza que solo código validado llega a producción.

## Arquitectura

```
┌─────────────────────────────────────────────────┐
│               ENTORNO LOCAL                     │
│                                                 │
│  docker-compose.yml                             │
│  ┌────────────┐       ┌────────────┐            │
│  │ Flask:5000 │──────→│ PostgreSQL │            │
│  └────────────┘       └────────────┘            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              GITHUB ACTIONS                     │
│                                                 │
│  push a main                                    │
│    ├── pytest (si falla → STOP)                 │
│    ├── docker build + push a ACR                │
│    └── az containerapp update                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                  AZURE                          │
│                                                 │
│  ┌─────┐    ┌────────────────┐    ┌──────────┐  │
│  │ ACR │───→│ Container Apps │───→│Azure DB  │  │
│  └─────┘    └────────────────┘    └──────────┘  │
│                    │                             │
│              URL pública                         │
└─────────────────────────────────────────────────┘
```

En local se usa PostgreSQL en contenedor. En producción se recomienda **Azure Database for PostgreSQL** (servicio gestionado) por sus ventajas: backups automáticos, alta disponibilidad, escalado y parches de seguridad.

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje de programación |
| Flask 3.1 | Framework web para la API REST |
| PostgreSQL 15 | Base de datos relacional |
| psycopg2 | Driver Python para PostgreSQL |
| Docker | Contenerización de la aplicación |
| Docker Compose | Orquestación local (Flask + PostgreSQL) |
| GitHub Actions | Pipeline CI/CD |
| Azure Container Registry | Registro privado de imágenes Docker |
| Azure Container Apps | Plataforma de despliegue serverless |
| pytest | Framework de pruebas automatizadas |

## Requisitos previos

- Python 3.11 o superior
- Docker Desktop
- Git
- Azure CLI
- Cuenta de GitHub
- Suscripción de Azure

## Instalación local

```bash
# Clonar el repositorio
git clone https://github.com/<tu-usuario>/<tu-repo>.git
cd <tu-repo>

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación (sin Docker, sin BD)
python app.py
```

La app arranca en `http://localhost:5000/`. Los endpoints `/` y `/health` funcionan sin PostgreSQL. El endpoint `/db` devolverá error 500 hasta que haya una BD disponible.

## Configuración del .env

Copiar la plantilla y ajustar los valores si es necesario:

```bash
copy .env.example .env     # Windows
cp .env.example .env       # Linux/Mac
```

Variables disponibles:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DB_HOST` | Host de PostgreSQL | `db` (nombre del servicio en Docker Compose) |
| `DB_PORT` | Puerto | `5432` |
| `DB_NAME` | Nombre de la base de datos | `mi_backend_db` |
| `DB_USER` | Usuario | `postgres` |
| `DB_PASSWORD` | Contraseña | `postgres` |

> **⚠️ El archivo `.env` contiene credenciales y está en `.gitignore`. NUNCA subirlo al repositorio.**

## Ejecución con Docker Compose

```bash
# Construir y levantar los contenedores
docker compose up --build

# Verificar los endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/db

# Detener los contenedores
docker compose down

# Detener y eliminar volúmenes (borra datos de BD)
docker compose down -v
```

## Ejecución de pruebas con pytest

```bash
# Ejecutar todos los tests
pytest -v --tb=short
```

El proyecto incluye **18 pruebas** organizadas en dos archivos:

| Archivo | Tipo | Tests | Requiere BD |
|---|---|---|---|
| `tests/test_app.py` | Unitarias | 11 | No |
| `tests/test_integration.py` | Integración | 7 | No (usa mocks) |

**Pruebas unitarias** — Validan endpoints `/`, `/health` y rutas 404 de forma aislada, sin dependencias externas.

**Pruebas de integración** — Validan el endpoint `/db` simulando la conexión a PostgreSQL con `unittest.mock`. Verifican tanto el caso exitoso como el fallido, y comprueban que los recursos (cursor y conexión) se cierran correctamente.

## Despliegue en Azure

### 1. Crear recursos

```bash
az login
az group create --name rg-mi-backend --location westeurope
az acr create --resource-group rg-mi-backend --name acrmibackenddemo --sku Basic --admin-enabled true
az containerapp env create --name cae-mi-backend --resource-group rg-mi-backend --location westeurope
```

### 2. Subida manual inicial

```bash
docker build -t mi-backend:v1 .
docker tag mi-backend:v1 acrmibackenddemo.azurecr.io/mi-backend:v1
az acr login --name acrmibackenddemo
docker push acrmibackenddemo.azurecr.io/mi-backend:v1
```

### 3. Crear Container App

```bash
az containerapp create \
  --name mi-backend-app \
  --resource-group rg-mi-backend \
  --environment cae-mi-backend \
  --image acrmibackenddemo.azurecr.io/mi-backend:v1 \
  --target-port 5000 \
  --ingress external \
  --registry-server acrmibackenddemo.azurecr.io \
  --registry-username acrmibackenddemo \
  --registry-password <CONTRASEÑA_ACR>
```

## Pipeline CI/CD

El workflow `.github/workflows/ci-cd.yml` se dispara con cada push a `main` y ejecuta:

1. **Job `test`**: instala Python, dependencias y ejecuta `pytest`
2. **Job `build-and-deploy`**: depende de `test` → solo se ejecuta si los tests pasan. Construye la imagen Docker, la sube a ACR y despliega en Azure Container Apps.

### Secrets de GitHub necesarios

| Secret | Descripción |
|---|---|
| `AZURE_CREDENTIALS` | JSON del Service Principal de Azure |

### Crear el Service Principal

```bash
az ad sp create-for-rbac \
  --name "github-actions-sp" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-mi-backend \
  --json-auth
```

Copiar el JSON resultante y guardarlo como secret `AZURE_CREDENTIALS` en GitHub (Settings → Secrets).

## Estructura del proyecto

```
Actividad 8/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   └── test_integration.py
├── .env                    ← NO se sube a Git
├── .env.example
├── .gitignore
├── app.py
├── docker-compose.yml
├── Dockerfile
├── MEMORIA.md
├── README.md
└── requirements.txt
```

## Incidencias encontradas

### 1. Error de conexión a PostgreSQL al arrancar Docker Compose

**Problema:** Flask arrancaba antes que PostgreSQL estuviera listo, provocando `Connection refused` en el endpoint `/db`.

**Causa:** Docker Compose levanta los contenedores en paralelo. Aunque `depends_on` garantiza el orden de inicio, no espera a que la BD esté lista para aceptar conexiones.

**Solución:** Se añadió un `healthcheck` con `pg_isready` en el servicio `db` y se usó `depends_on: db: condition: service_healthy` en el servicio `web`. Así Flask no arranca hasta que PostgreSQL realmente acepta conexiones.

### 2. Tests fallando por importación de `app.py`

**Problema:** Al ejecutar `pytest`, aparecía `ModuleNotFoundError: No module named 'app'` porque pytest no encontraba el módulo raíz.

**Causa:** Cuando pytest se ejecuta, el directorio `tests/` es el contexto, y `app.py` está un nivel arriba.

**Solución:** En `conftest.py` se inserta el directorio padre en `sys.path`:
```python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

### 3. Tests de `/db` fallando sin PostgreSQL

**Problema:** Los tests de integración del endpoint `/db` fallaban en CI (GitHub Actions) porque no hay PostgreSQL disponible.

**Causa:** El endpoint intenta conectar a una BD real, que no existe en el runner de GitHub Actions.

**Solución:** Se implementaron dos estrategias complementarias:
- Tests con `unittest.mock` que simulan la conexión a PostgreSQL (éxito y fallo)
- Tests funcionales que verifican el manejo de error cuando no hay BD (`status_code == 500 → verificar formato de error`)

### 4. Pipeline CI/CD sin validación de código

**Problema (versión anterior):** El pipeline solo hacía build y push, sin ejecutar ningún tipo de prueba. Código con errores podía llegar a producción.

**Solución:** Se separó el pipeline en dos jobs: `test` (pytest) y `build-and-deploy` con `needs: test`. Si cualquier test falla, el pipeline se detiene y no se despliega.

### 5. Conflicto de puerto 5432

**Problema:** Si PostgreSQL está instalado localmente, el puerto 5432 ya está ocupado y Docker Compose falla al mapear el puerto.

**Solución:** Detener el servicio local (`net stop postgresql-x64-15`) o cambiar el puerto mapeado en `docker-compose.yml` a `"5433:5432"`.

## Soluciones aplicadas

| Problema | Solución | Patrón DevOps |
|---|---|---|
| Flask arranca antes que PostgreSQL | Healthcheck + `condition: service_healthy` | Dependency management |
| Tests fallan sin BD real | Mocks con `unittest.mock` | Test isolation |
| Código sin validar llega a producción | Job `test` con `needs` en el pipeline | Shift-left testing |
| Credenciales en el código | Variables de entorno + `.env` + GitHub Secrets | Secret management |
| Imágenes sin trazabilidad | Tag con `github.sha` además de `latest` | Immutable artifacts |

## Lecciones aprendidas

### 1. La integración continua real requiere pruebas
Un pipeline que solo automatiza la subida de imágenes no es CI — es solo CD (Continuous Delivery). La **"I" de CI** significa que cada cambio se **integra y valida** automáticamente. Sin tests, no hay validación, y cualquier error puede propagarse a producción sin ser detectado. Añadir pytest como puerta de acceso al despliegue transforma el pipeline de "automatización de tareas" en "garantía de calidad".

### 2. Los mocks son imprescindibles para CI
En un pipeline de CI no siempre hay servicios externos disponibles (bases de datos, APIs). Los mocks permiten simular esas dependencias de forma controlada, haciendo que los tests sean rápidos, repetibles y ejecutables en cualquier entorno. Sin mocks, los tests de integración serían frágiles y difíciles de mantener en CI.

### 3. El healthcheck de Docker Compose evita errores de timing
La diferencia entre `depends_on` simple y `depends_on` con `condition: service_healthy` es crítica. Sin healthcheck, la app puede arrancar cuando PostgreSQL todavía está inicializando, causando errores intermitentes difíciles de depurar.

### 4. Separar jobs en el pipeline mejora la visibilidad
Tener `test` y `build-and-deploy` como jobs separados (en vez de steps en un solo job) hace que el pipeline sea:
- Más legible (ves de un vistazo si el fallo fue en tests o en deploy)
- Más eficiente (los jobs pueden correr en paralelo si no hay dependencias)
- Más seguro (la dependencia `needs` es explícita)

### 5. La seguridad se diseña, no se añade después
Usar variables de entorno, `.gitignore` y GitHub Secrets desde el principio es mucho más fácil que refactorizar un proyecto que tiene contraseñas hardcodeadas. El enfoque "security by design" es una buena práctica fundamental en DevOps.

### 6. La documentación profunda es una inversión
Documenter incidencias y lecciones aprendidas durante el desarrollo (no después) produce documentación mucho más útil y realista. Los READMEs genéricos no ayudan a resolver problemas reales.

## Mejoras futuras

- **Cobertura de código**: integrar `pytest-cov` y establecer un umbral mínimo de cobertura (ej. 80%)
- **Tests de carga**: usar `locust` o `k6` para validar rendimiento bajo carga
- **Linting automático**: añadir `flake8` o `ruff` al pipeline para validar calidad de código
- **Multi-stage Docker build**: separar imagen de build y de producción para reducir tamaño
- **Base de datos gestionada**: migrar a Azure Database for PostgreSQL en producción
- **HTTPS**: configurar certificado TLS en Azure Container Apps
- **Monitorización**: integrar Azure Monitor y alertas para detectar anomalías en tiempo real
- **Migraciones de BD**: usar `Alembic` o `Flask-Migrate` para gestionar cambios de esquema
- **Análisis de vulnerabilidades**: añadir `trivy` o `Snyk` al pipeline para escanear la imagen Docker

## Autor

Nombre del alumno / datos del estudiante según corresponda.
