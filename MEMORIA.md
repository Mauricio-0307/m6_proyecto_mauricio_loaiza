# Memoria del Proyecto: Pipeline CI/CD con Flask, PostgreSQL, Docker y Azure

---

## 1. Introducción

El presente documento recoge el proceso completo de diseño, desarrollo y despliegue de una aplicación backend contenerizada con integración y entrega continuas (CI/CD). El proyecto aborda un ejercicio práctico de DevOps que integra múltiples tecnologías: Python/Flask como framework web, PostgreSQL como base de datos relacional, Docker y Docker Compose para contenerización y orquestación local, Azure Container Registry (ACR) y Azure Container Apps para el despliegue en la nube, GitHub Actions como plataforma de CI/CD, y pytest como framework de pruebas automatizadas.

El enfoque del proyecto pone especial énfasis en dos aspectos que frecuentemente se descuidan en ejercicios académicos: la inclusión de **pruebas automatizadas reales** como parte obligatoria del pipeline de CI/CD, y una **documentación profunda** que refleje el análisis crítico del proceso, las incidencias encontradas y las lecciones aprendidas.

> **Sugerencia de captura:** Diagrama de arquitectura del proyecto (terminal o diagrama digital).

---

## 2. Objetivos

Los objetivos principales del proyecto son:

1. Diseñar y configurar un pipeline CI/CD para el despliegue automatizado de una aplicación en la nube.
2. Implementar una aplicación backend funcional con base de datos, contenida en Docker y gestionada con Docker Compose.
3. Integrar pruebas automatizadas (unitarias y de integración) en el pipeline, de modo que el despliegue solo se produzca si todos los tests pasan.
4. Desplegar la aplicación en Azure utilizando Azure Container Apps.
5. Aplicar buenas prácticas de configuración, seguridad y documentación.
6. Monitorizar y validar el correcto funcionamiento del despliegue.

---

## 3. Arquitectura de la solución

La arquitectura sigue un modelo de tres capas contenidas en Docker:

- **Capa de presentación/API**: aplicación Flask que expone tres endpoints REST (`/`, `/health`, `/db`).
- **Capa de datos**: base de datos PostgreSQL 15.
- **Capa de orquestación**: Docker Compose en local; Azure Container Apps en producción.

En el entorno local, Flask y PostgreSQL corren como contenedores Docker dentro de la misma red interna, comunicándose por el nombre del servicio (`db`). Docker Compose gestiona el orden de arranque mediante healthchecks, asegurando que Flask no intente conectar hasta que PostgreSQL esté listo.

En el entorno de producción (Azure), la aplicación se despliega como una Container App con ingress externo, conectada a una base de datos PostgreSQL gestionada (Azure Database for PostgreSQL). Las imágenes Docker se almacenan en Azure Container Registry (ACR).

El pipeline de CI/CD en GitHub Actions actúa como puente entre ambos entornos: cada push a la rama `main` dispara la ejecución de pruebas automatizadas con pytest y, solo si estas pasan, construye la imagen Docker, la sube a ACR y actualiza la Container App.

> **Sugerencia de captura:** Esquema de conexiones entre componentes locales y en Azure.

---

## 4. Desarrollo de la aplicación

La aplicación Flask implementa tres endpoints:

- **`GET /`**: devuelve información general del servicio en formato JSON (nombre, versión, descripción, fecha UTC y lista de endpoints disponibles).
- **`GET /health`**: endpoint de health check que confirma que la aplicación está activa. Devuelve `{"status": "ok"}`. Es fundamental para que los orquestadores (Docker, Azure) puedan verificar el estado del servicio.
- **`GET /db`**: prueba de conexión a PostgreSQL ejecutando `SELECT 1`. Devuelve status 200 si la conexión es exitosa o 500 con detalle del error si falla.

La configuración de la base de datos se gestiona exclusivamente mediante variables de entorno (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), cargadas con `python-dotenv` en local y directamente inyectadas por el orquestador en producción. Esta separación entre código y configuración sigue el principio de los Twelve-Factor Apps.

Las dependencias del proyecto se gestionan con `requirements.txt`, incluyendo Flask, psycopg2-binary (driver de PostgreSQL), python-dotenv, gunicorn (servidor WSGI de producción) y pytest.

> **Sugerencia de captura:** Respuesta JSON de cada endpoint en el navegador.

---

## 5. Contenerización

El proyecto utiliza Docker para empaquetar la aplicación con todas sus dependencias, garantizando que se ejecute de la misma manera en cualquier entorno.

El **Dockerfile** parte de la imagen `python:3.11-slim` (ligera, ~120 MB frente a ~900 MB de la imagen completa). La estrategia de capas está optimizada: primero se copia e instala `requirements.txt`, y después el código fuente. Así, las dependencias se cachean entre builds si no cambian, reduciendo significativamente los tiempos de construcción sucesivos. Como servidor WSGI se usa Gunicorn con 2 workers.

El **docker-compose.yml** define dos servicios: `db` (PostgreSQL 15 con healthcheck basado en `pg_isready`) y `web` (la aplicación Flask). La directiva `depends_on` con `condition: service_healthy` asegura que Flask no arranca hasta que PostgreSQL esté preparado para recibir conexiones. Un volumen nombrado (`pgdata`) persiste los datos de PostgreSQL entre reinicios.

Las variables de entorno se leen desde un archivo `.env` que nunca se sube al repositorio (incluido en `.gitignore`). Se proporciona `.env.example` como plantilla.

> **Sugerencia de captura:** Terminal mostrando `docker compose up --build` exitoso con ambos servicios funcionando.

---

## 6. Integración continua con pruebas automatizadas

Este apartado representa una de las mejoras más significativas respecto a una versión anterior del ejercicio, donde el pipeline carecía de cualquier tipo de validación de código.

### Importancia de las pruebas en CI/CD

Un pipeline que solo automatiza la construcción y subida de imágenes no implementa verdadera **integración continua**. La "I" de CI se refiere a la integración y validación automática de cada cambio. Sin pruebas, no existe esa validación, y cualquier error puede propagarse directamente a producción. Las pruebas actúan como una "puerta de calidad" (quality gate) que impide el paso de código defectuoso.

### Suite de pruebas

El proyecto incluye **18 pruebas** organizadas en dos categorías:

**Pruebas unitarias** (`test_app.py`, 11 tests): verifican los endpoints `/` y `/health` de forma aislada, sin dependencias externas. Validan códigos de respuesta HTTP, tipos de contenido, estructura del JSON y presencia de claves esperadas. También incluyen un test de ruta inexistente (404).

**Pruebas de integración** (`test_integration.py`, 7 tests): verifican el endpoint `/db` usando `unittest.mock` para simular la conexión a PostgreSQL. Se prueban tres escenarios:
- Conexión exitosa (mock devuelve resultado esperado → status 200)
- Conexión fallida (mock lanza excepción → status 500 con error descriptivo)
- Verificación de limpieza de recursos (cursor y conexión deben cerrarse)

El uso de mocks es esencial para que los tests de integración sean ejecutables en cualquier entorno (local sin BD, GitHub Actions runners) de forma rápida, repetible y determinista.

### Integración en el pipeline

El pipeline de GitHub Actions define el job `test` como prerequisito obligatorio del job `build-and-deploy` mediante la directiva `needs: test`. Si algún test falla, pytest devuelve un código de salida distinto de cero, GitHub Actions marca el job como fallido, y el job de despliegue **nunca se ejecuta**.

> **Sugerencia de captura:** Resultado de `pytest -v` en terminal mostrando 18/18 PASSED. Si es posible, también captura de GitHub Actions mostrando un pipeline exitoso con ambos jobs verdes.

---

## 7. Despliegue en Azure

El despliegue utiliza tres servicios de Azure:

- **Azure Container Registry (ACR)**: registro privado donde se almacenan las imágenes Docker. Se eligió el nivel Basic por ser suficiente para este caso de uso.
- **Azure Container Apps**: plataforma serverless que ejecuta los contenedores. No requiere gestionar máquinas virtuales ni clústeres de Kubernetes. Soporta escalado automático, ingress HTTP y certificados TLS.
- **Azure Database for PostgreSQL** (recomendado para producción): servicio gestionado que ofrece backups automáticos, alta disponibilidad y parches de seguridad. En local se usa PostgreSQL en contenedor por simplicidad.

La autenticación de GitHub Actions con Azure se realiza mediante un **Service Principal** con rol Contributor, cuyas credenciales se almacenan como secret de GitHub (`AZURE_CREDENTIALS`). Esta separación garantiza que las credenciales nunca aparecen en el código fuente.

Cada imagen se etiqueta con el SHA del commit (`github.sha`) además de `latest`, proporcionando trazabilidad completa: ante cualquier incidencia, es posible identificar exactamente qué código está desplegado.

> **Sugerencia de captura:** Portal de Azure mostrando la Container App con estado "Running" y la URL pública accesible.

---

## 8. Validación y monitorización

La validación del despliegue se realiza en varios niveles:

1. **Endpoint `/health`**: verificación básica de que la aplicación responde. Puede configurarse como health probe en Azure Container Apps.
2. **Endpoint `/db`**: verificación de conectividad con PostgreSQL.
3. **Logs de Azure**: consultables con `az containerapp logs show`.
4. **Pipeline de GitHub Actions**: proporciona trazabilidad de cada despliegue, incluyendo resultado de tests, logs de build y confirmación de actualización.

Para verificar que el pipeline funciona correctamente de extremo a extremo, basta realizar un cambio menor en el código, hacer push a `main` y observar la ejecución automática del workflow en GitHub Actions.

> **Sugerencia de captura:** Navegador mostrando la respuesta de `/health` desde la URL pública de Azure. Logs de la Container App en el portal de Azure.

---

## 9. Incidencias y soluciones

### Incidencia 1: Race condition entre Flask y PostgreSQL

Flask intentaba conectar a PostgreSQL antes de que la base de datos estuviera lista, generando errores `Connection refused`. Se resolvió implementando un healthcheck con `pg_isready` y usando `depends_on` con `condition: service_healthy` en Docker Compose.

### Incidencia 2: Importación de módulos en pytest

Al ejecutar pytest, el directorio de trabajo era `tests/`, lo que impedía encontrar `app.py`. Se resolvió añadiendo el directorio raíz a `sys.path` en `conftest.py`.

### Incidencia 3: Tests de base de datos en CI

Los tests del endpoint `/db` fallaban en GitHub Actions por ausencia de PostgreSQL. Se implementaron mocks con `unittest.mock.patch` para simular la conexión en cualquier entorno.

### Incidencia 4: Pipeline sin validación de calidad

En la versión anterior del ejercicio, el pipeline solo automatizaba build y push, sin ejecutar pruebas. Se reestructuró el pipeline en dos jobs con dependencia explícita (`needs: test`), convirtiendo pytest en requisito obligatorio para el despliegue.

### Incidencia 5: Conflicto de puertos locales

Si PostgreSQL ya estaba instalado en la máquina local, el puerto 5432 estaba ocupado. Se resolvió documentando la solución (detener el servicio local o cambiar el mapeo de puertos).

### Incidencia 6: Restricción de regiones en Azure for Students

Al crear el Azure Container Registry, el comando `az acr create --location westeurope` fallaba con el error `RequestDisallowedByAzure`. Tras investigar con `az policy assignment list`, se descubrió que la suscripción Azure for Students (UNIR) tiene una Azure Policy que restringe el despliegue a cinco regiones: `swedencentral`, `switzerlandnorth`, `polandcentral`, `italynorth` y `germanywestcentral`. Se recrearon todos los recursos en `swedencentral`, resolviendo el problema. Esta incidencia demuestra la importancia de verificar las políticas de gobernanza antes de planificar la infraestructura.

### Incidencia 7: Imposibilidad de crear Service Principal

Para que GitHub Actions pueda autenticarse contra Azure, se necesita un Service Principal (credenciales de aplicación). Al ejecutar `az ad sp create-for-rbac`, Azure devolvió `Insufficient privileges to complete the operation`. La suscripción educativa no otorga permisos de Azure Active Directory a los estudiantes. Como consecuencia, el job `build-and-deploy` del pipeline no puede ejecutarse de forma automatizada. Sin embargo, el job `test` (pytest) funciona correctamente, validando la parte de integración continua. El despliegue se realizó manualmente mediante `az acr login`, `docker push` y `az containerapp create`. Esta limitación es representativa de situaciones reales en entornos corporativos donde las políticas de seguridad restringen la creación de identidades.

---

## 10. Lecciones aprendidas

1. **La CI real incluye validación, no solo automatización.** Un pipeline sin tests es como una cadena de montaje sin control de calidad: produce rápido, pero sin garantías.

2. **Los mocks son una herramienta fundamental para CI.** Permiten verificar interacciones con servicios externos sin depender de su disponibilidad, haciendo los tests rápidos y deterministas.

3. **Los healthchecks eliminan errores de timing.** La dependencia entre servicios no es solo "arrancar en orden", sino "arrancar cuando el servicio esté listo". Docker Compose con healthchecks resuelve esto de forma elegante.

4. **La separación de configuración y código es una práctica de seguridad básica.** Variables de entorno, archivos `.env` excluidos de Git y GitHub Secrets garantizan que las credenciales nunca se exponen.

5. **La documentación de incidencias reales produce mejor documentación.** Documentar los problemas tal como ocurren genera material mucho más útil que un README genérico escrito post-facto.

6. **El versionado de imágenes con el SHA del commit aporta trazabilidad total.** Ante cualquier incidencia en producción, se puede saber exactamente qué código está desplegado y revertir de forma inmediata.

7. **Las suscripciones educativas tienen restricciones de gobernanza.** Las Azure Policies del tenant universitario limitan regiones y permisos. Esto obliga a investigar las restricciones antes de diseñar la infraestructura y a plantear alternativas cuando el flujo ideal no es viable. En entornos corporativos existen limitaciones similares, por lo que esta experiencia es directamente transferible al mundo profesional.

---

## 11. Conclusiones

El proyecto demuestra la implementación completa de un pipeline CI/CD real que va más allá de la simple automatización de subida de imágenes. La inclusión de pruebas automatizadas como paso obligatorio del pipeline garantiza que solo código validado llega a producción, lo cual es el principio fundamental de la integración continua.

Las tecnologías elegidas (Flask, PostgreSQL, Docker, Azure Container Apps, GitHub Actions, pytest) forman un stack coherente y representativo de las prácticas modernas de desarrollo y despliegue de software. Cada componente cumple un papel específico y bien definido en la cadena de desarrollo-prueba-despliegue.

Las incidencias encontradas durante el desarrollo, lejos de ser obstáculos, han sido oportunidades de aprendizaje que han enriquecido tanto la solución técnica como la comprensión de las buenas prácticas DevOps. La documentación detallada de estas incidencias y sus soluciones añade valor práctico al proyecto.

Como mejoras futuras se plantea la integración de análisis de cobertura de código, pruebas de carga, análisis de vulnerabilidades en las imágenes Docker y migraciones de base de datos con Alembic, todas ellas extensiones naturales del pipeline implementado.

> **Sugerencia de captura:** Vista general del repositorio en GitHub mostrando la estructura de archivos completa y los resultados del pipeline CI/CD.
