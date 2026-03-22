# 🚀 MI-BACKEND-APP: Flask + PostreSQL + Docker + Azure

Un backend robusto diseñado para demostrar la implementación práctica de un flujo **CI/CD real**. Cuenta con una API REST en Python, base de datos relacional y despliegue automatizado en la nube.

🌍 **En producción:** [mi-backend-app.salmonbay-c911fa5d.swedencentral.azurecontainerapps.io](https://mi-backend-app.salmonbay-c911fa5d.swedencentral.azurecontainerapps.io/)

---

## 🛠 Stack Tecnológico

- **Backend**: Python 3.11, Flask, Gunicorn
- **Base de Datos**: PostgreSQL 15, psycopg2
- **Testing**: Pytest (Unitarios e Integración con `unittest.mock`)
- **DevOps**: Docker, Docker Compose, GitHub Actions
- **Cloud (Azure)**: Container Registry (ACR), Container Apps

## 🏗 Arquitectura

```text
┌───────────────── ENTORNO LOCAL ─────────────────┐
│ docker-compose.yml                              │
│ ┌────────────┐       ┌────────────┐             │
│ │ Flask:5000 │──────→│ PostgreSQL │             │
│ └────────────┘       └────────────┘             │
└─────────────────────────────────────────────────┘

┌───────────────── FLUJO CI/CD ───────────────────┐
│ GITHUB ACTIONS (al hacer push a main)           │
│  1. Test: Pytest (si falla, detiene el pipeline)│
│  2. Deploy: Build Docker ➔ ACR ➔ Container App  │
└─────────────────────────────────────────────────┘
```

## 🚀 Ejecución en Local

La forma más sencilla de levantar el proyecto en tu máquina es usando **Docker Compose**. Esto configurará de forma paralela la base de datos y la API sin instalar dependencias globales.

1. **Clonar el proyecto:**
   ```bash
   git clone https://github.com/Mauricio-0307/m6_proyecto_mauricio_loaiza.git
   cd m6_proyecto_mauricio_loaiza
   ```
2. **Configurar entorno:**
   (Opcional) Copia `.env.example` a `.env` si deseas modificar credenciales por defecto.
3. **Levantar contenedores:**
   ```bash
   docker compose up --build -d
   ```
4. **Verificar estado:**
   Visita `http://localhost:5000/health` en tu navegador.

## 🧪 Pruebas Automatizadas (CI)

El proyecto cuenta con una cobertura de tests obligatoria. El pipeline CI de GitHub Actions ejecuta **18 pruebas** (11 unitarias, 7 de integración) que validan:
- Respuesta correcta de endpoints base y 404.
- Conectividad a la Base de Datos (usando `mocks` para entornos sin DB real).
- Manejo seguro de recursos y conexiones limitadas.

```bash
# Para correr los tests manualmente:
pip install -r requirements.txt
pytest -v
```

## ☁️ Despliegue en Azure y Retos Abordados

El despliegue está configurado sobre **Azure Container Apps** en la región `swedencentral`. Durante la configuración surgieron retos propios de entornos empresariales y educativos restrictivos que obligaron a adaptar la solución:

1. **Gestión de timing (Race Conditions):** Flask intentaba conectarse antes de que PostgreSQL estuviera listo. Solucionado integrando *Healthchecks* nativos (`pg_isready`) en el `docker-compose.yml`.
2. **Restricciones de región por Azure Policy:** La suscripción *Azure for Students* impide despliegues en diversas regiones populares europeas. Mediante auditoría de permisos (`az policy assignment`), detectamos y migramos a `swedencentral`.
3. **Políticas de Identidad Estrictas:** Al carecer de permisos de Directorio Activo (`Azure AD`) para crear el *Service Principal* que requería GitHub Actions, el pipeline validaba con éxito la parte "CI" (pytest), implementando un despliegue manual complementario para cumplir con el ciclo de vida. Una valiosa lección sobre degradación elegante en restricciones cloud reales.

---
**Autor:** Mauricio Loaiza — Proyecto CI/CD Avanzado (UNIR)
