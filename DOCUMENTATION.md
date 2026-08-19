# upSerArch - Plan de Desarrollo

## Descripción del Proyecto

Aplicación web minimalista y robusta para homelab que permite subir archivos PDF y descargarlos mediante un código único. Construida con FastAPI, HTMX, Tailwind CSS y Docker. Orquestada con Traefik y expuesta vía túnel de Cloudflare.

### Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3.12 + FastAPI |
| Frontend | HTMX + Tailwind CSS (CDN) |
| Templates | Jinja2 |
| Base de datos | SQLite + SQLAlchemy async + aiosqlite |
| Auth | Cookie session con itsdangerous (`TimedSerializer`) |
| Contenedor | Docker multi-stage build |
| Proxy reverso | Traefik (labels en docker-compose) |
| Tunnel | Cloudflare Tunnel |

### Decisiones Técnicas

- **Base de datos**: SQLite embebida en el contenedor, ideal para homelab sin servicios adicionales.
- **Auth**: Login básico con cookie de sesión. Credenciales en `.env`. La descarga es pública (solo necesitas el código). Usa `TimedSerializer` de itsdangerous con `dumps`/`loads`.
- **Upload**: Si el código ya existe → sobrescribir archivo y actualizar metadata.
- **Admin**: Panel protegido con login para listar, buscar y eliminar archivos.
- **HTMX**: Fragmentos HTML parciales para interacciones dinámicas sin recarga completa.
- **TemplateResponse**: API de Starlette 1.6.0+ usa keyword arguments: `TemplateResponse(request, "template.html", {context})`.

---

## Estructura del Proyecto

```
upSerArch/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, dependencias globales
│   ├── config.py            # Settings desde .env (pydantic-settings)
│   ├── database.py          # SQLAlchemy async engine + session
│   ├── models.py            # ORM models (FileRecord)
│   ├── auth.py              # Login básico (cookie session con TimedSerializer)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py         # GET / (home), GET /admin, POST /login, GET /logout, DELETE /admin/{id}
│   │   ├── upload.py        # POST /upload
│   │   └── download.py      # GET /d/{codigo}, GET /search
│   └── templates/
│       ├── base.html        # Layout base (Tailwind CDN + HTMX)
│       ├── index.html       # Home: buscador + formulario upload
│       ├── admin.html       # Listado de archivos
│       ├── login.html       # Formulario de login
│       └── components/
│           ├── upload_result.html   # Fragmento HTMX: resultado subida
│           ├── search_result.html   # Fragmento HTMX: resultado búsqueda
│           └── login_result.html    # Fragmento HTMX: redirect tras login
├── uploads/                 # Volumen persistente para PDFs
├── data/                    # Directorio para SQLite
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_upload.py
│   ├── test_download.py
│   └── test_auth.py
├── .env.example
├── .env
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
├── DOCUMENTATION.md
└── README.md
```

---

## Errores Corregidos durante el Desarrollo

Durante la implementación se encontraron y corrigieron los siguientes problemas:

| # | Error | Causa | Solución |
|---|-------|-------|----------|
| 1 | `COPY ./templates: not found` | Dockerfile buscaba `./templates` pero los templates están en `./app/templates` | Eliminada la línea COPY separada, los templates se copian con `COPY ./app ./app` |
| 2 | `PermissionError: 'data'` | El directorio `data` se creaba relativo a `/code` (root), pero el user `app` no tiene permisos ahí | Agregado `DATA_DIR=/app/data` como ruta absoluta en config |
| 3 | `unable to open database file` | `DATABASE_URL` usaba ruta relativa `./data/upserarch.db` que se resolvía contra WORKDIR `/code` | Cambiado a ruta absoluta: `sqlite+aiosqlite:////app/data/upserarch.db` |
| 4 | `TypeError: unhashable type: 'dict'` | Starlette 1.6.0 cambió el signature de `TemplateResponse` a keyword arguments | Cambiado de `TemplateResponse("tpl.html", {dict})` a `TemplateResponse(request, "tpl.html", {context})` |
| 5 | `Credenciales incorrectas` (siempre) | Parámetros `username`/`password` en POST /login no estaban anotados con `Form(...)` | Agregado `Form("")` a los parámetros del endpoint |
| 6 | `AttributeError: 'URLSafeTimedSerializer' has no attribute 'sign'` | `URLSafeTimedSerializer` usa `dumps`/`loads`, no `sign`/`unsign` | Cambiado a `TimedSerializer` con `dumps`/`loads` |
| 7 | Puerto no accesible desde host | `docker-compose.yml` solo tenía `expose: 8000` sin `ports:` mapping | Agregado `ports: ["8000:8000"]` para desarrollo local |

---

## Fases de Desarrollo

### Fase 0: `main` - Infraestructura base

Crear esqueleto del proyecto, Docker y configuración básica.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 1 | `chore(init): scaffold project structure and .gitignore` | Crear `.gitignore`, `.dockerignore`, carpetas base | `.gitignore`, `.dockerignore`, `app/__init__.py`, `app/routers/__init__.py`, `uploads/`, `data/`, `tests/__init__.py` |
| 2 | `chore(deps): add requirements.txt with base dependencies` | Dependencias del proyecto | `requirements.txt` |
| 3 | `feat(config): add pydantic-settings based config` | Configuración desde `.env` | `app/config.py`, `.env.example` |
| 4 | `feat(docker): add Dockerfile with multi-stage build` | Dockerfile optimizado | `Dockerfile` |
| 5 | `chore(docker): add docker-compose.yml with Traefik labels` | Orquestación con Traefik | `docker-compose.yml` |

### Fase 1: `feature/database-and-models` - Base de datos

Modelos ORM y conexión async a SQLite.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 6 | `feat(db): add async SQLite engine and session factory` | Engine async, session dependency | `app/database.py` |
| 7 | `feat(models): add FileRecord ORM model` | Modelo con campos: id, codigo, original_filename, upload_date, file_size | `app/models.py` |
| 8 | `feat(db): add table creation on startup via lifespan` | Crear tablas al iniciar la app | `app/main.py` |

### Fase 2: `feature/auth` - Autenticación básica

Login con cookie de sesión y protección de rutas.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 9 | `feat(auth): add basic cookie-based login system` | Verificación de credenciales con `TimedSerializer.dumps/loads`, creación de cookie | `app/auth.py` |
| 10 | `feat(auth): add login page template` | Template de login con HTMX | `app/templates/login.html` |
| 11 | `feat(auth): add login route and logout endpoint` | POST /login (con `Form(...)`), GET /logout, dependencia require_auth | `app/routers/pages.py` |

### Fase 3: `feature/upload` - Subida de archivos

Upload con código único y persistencia.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 12 | `feat(upload): add upload route with file and code validation` | POST /upload: recibir PDF, validar, guardar, registrar en DB. Sobrescribir si código existe | `app/routers/upload.py` |
| 13 | `feat(upload): add upload form component with HTMX` | Fragmento HTML con resultado de subida | `app/templates/components/upload_result.html` |
| 14 | `feat(pages): add home page with upload form and search bar` | GET /: index.html con formulario y buscador | `app/routers/pages.py`, `app/templates/index.html`, `app/templates/base.html` |

### Fase 4: `feature/download` - Descarga por código

Ruta limpia de descarga y búsqueda.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 15 | `feat(download): add download route serving PDF by code` | GET /d/{codigo}: FileResponse con Content-Disposition | `app/routers/download.py` |
| 16 | `feat(search): add HTMX-powered search with live results` | GET /search?q=...: fragmento HTML con resultado | `app/templates/components/search_result.html` |

### Fase 5: `feature/admin` - Panel de administración

Listado, gestión y eliminación de archivos.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 17 | `feat(admin): add admin page with file listing` | GET /admin: tabla con archivos (protegido con require_auth) | `app/templates/admin.html` |
| 18 | `feat(admin): add delete endpoint for files` | DELETE /admin/{id}: eliminar archivo y registro | `app/routers/pages.py` |

### Fase 6: `feature/tests` - Tests

Cobertura de pruebas de integración.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 19 | `test(add): configure pytest and test fixtures` | conftest.py con AsyncClient, DB de prueba | `tests/conftest.py` |
| 20 | `test(upload): add upload integration tests` | Subida exitosa, código duplicado, archivo no PDF | `tests/test_upload.py` |
| 21 | `test(download): add download integration tests` | Descarga exitosa, código inexistente | `tests/test_download.py` |
| 22 | `test(auth): add auth flow tests` | Login/logout, acceso denegado | `tests/test_auth.py` |

### Fase 7: `feature/production` - Configuración production

Optimizaciones y documentación para despliegue.

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 23 | `chore(docker): add docker-compose.prod.yml for production` | Config production con Traefik + Cloudflare | `docker-compose.prod.yml` |
| 24 | `docs(readme): add comprehensive README with setup and usage` | Instrucciones completas | `README.md` |

### Fase 8: `feature/commits-doc` - Documentación de plan

| # | Commit | Descripción | Archivos |
|---|--------|-------------|----------|
| 25 | `docs(plan): add DOCUMENTATION.md with development plan` | Este documento | `DOCUMENTATION.md` |

---

## Flujo de Integración (Ramas)

### Modelo de trabajo

El proyecto se desarrolla con un flujo de **feature branches** que se integran a `main` mediante **squash merge**. Cada fase corresponde a una rama independiente.

### Dependencias entre ramas

```
main (base limpia)
│
├── feature/database-and-models  (sin dependencias)
│   → Crea: database.py, models.py, main.py (lifespan)
│
├── feature/auth                 (depende de: database-and-models)
│   → Crea: auth.py, login.html, login_result.html
│   → Modifica: pages.py (agrega rutas login/logout)
│
├── feature/upload               (depende de: auth, database-and-models)
│   → Crea: upload.py, upload_result.html
│   → Modifica: pages.py (agrega ruta home)
│
├── feature/download             (depende de: upload)
│   → Crea: download.py, search_result.html
│   → Modifica: index.html (agrega barra de búsqueda)
│
├── feature/admin                (depende de: auth, download)
│   → Crea: admin.html
│   → Modifica: pages.py (agrega DELETE /admin/{id})
│
├── feature/tests                (depende de: todas las anteriores)
│   → Crea: conftest.py, test_upload.py, test_download.py, test_auth.py
│
├── feature/production           (sin dependencias de código)
│   → Crea: docker-compose.prod.yml, README.md
│
└── feature/commits-doc          (sin dependencias de código)
    → Crea: DOCUMENTATION.md
```

### Orden de integración recomendado

```
1. feature/database-and-models  → squash merge a main
2. feature/auth                 → squash merge a main
3. feature/upload               → squash merge a main
4. feature/download             → squash merge a main
5. feature/admin                → squash merge a main
6. feature/tests                → squash merge a main
7. feature/production           → squash merge a main (puede ir en paralelo)
8. feature/commits-doc          → squash merge a main (puede ir en paralelo)
```

### Reglas de merge

1. **Siempre squash merge** para mantener el historial de `main` limpio:
   ```bash
   git checkout main
   git merge --squash feature/nombre-fase
   git commit -m "feat(descripción corta del merge)"
   ```

2. **Antes de merge**, la feature branch debe:
   - Pasar todos los tests: `docker compose exec web pytest`
   - No tener errores de lint/format

3. **`main` siempre debe estar deployable** - nunca hacer direct commit a main sin pasar por feature branch.

4. Si hay conflictos durante el merge squash:
   ```bash
   git checkout main
   git merge --squash feature/nombre-fase
   # Si hay conflictos, resolverlos manualmente
   git add .
   git commit -m "feat: merge feature/nombre-fase"
   ```

### Flujo paso a paso para crear e integrar una feature branch

```bash
# 1. Crear rama desde main actualizado
git checkout main
git pull
git checkout -b feature/database-and-models

# 2. Desarrollar (uno o varios commits)
git add .
git commit -m "feat(db): add async SQLite engine"

# 3. Cuando la feature está lista, merge a main
git checkout main
git merge --squash feature/database-and-models
git commit -m "feat(db): add database layer with async SQLite"

# 4. Eliminar rama feature (opcional)
git branch -d feature/database-and-models

# 5. Repetir para la siguiente feature
git checkout -b feature/auth
```

---

## Comandos Útiles

```bash
# Desarrollo local con Docker
docker compose up --build

# Ejecutar tests
docker compose exec web pytest

# Ver logs
docker compose logs -f web

# Crear nueva rama
git checkout -b feature/nombre-fase main

# Squash merge
git checkout main && git merge --squash feature/nombre-fase && git commit -m "feat: descripción"

# Ver historial de main (solo commits squash)
git log --oneline main
```

---

## Variables de Entorno (.env)

```env
# Seguridad
SECRET_KEY=CHANGE_ME_TO_A_RANDOM_STRING
ADMIN_USER=admin
ADMIN_PASS=changeme123

# Base de datos (ruta absoluta para Docker)
DATABASE_URL=sqlite+aiosqlite:////app/data/upserarch.db

# Upload
UPLOAD_DIR=/app/uploads
DATA_DIR=/app/data
MAX_FILE_SIZE=52428800  # 50MB en bytes
ALLOWED_EXTENSIONS=pdf

# Servidor
HOST=0.0.0.0
PORT=8000
```

---

## Despliegue con Traefik + Cloudflare

### docker-compose.yml (labels Traefik)

```yaml
services:
  web:
    build: .
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"  # Solo para desarrollo local
    volumes:
      - uploads_data:/app/uploads
      - db_data:/app/data
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.upserarch.rule=Host(`${DOMAIN:-localhost}`)"
      - "traefik.http.routers.upserarch.entrypoints=websecure"
      - "traefik.http.services.upserarch.loadbalancer.server.port=8000"
    expose:
      - "8000"
```

### Cloudflare Tunnel

```bash
# Instalar cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Crear tunnel
cloudflared tunnel create upserarch
cloudflared tunnel route dns upserarch upserarch.tudominio.com
cloudflared tunnel run --url http://localhost:8000 upserarch
```

---

## Resumen de Commits (25 total)

```
 1. chore(init): scaffold project structure and .gitignore
 2. chore(deps): add requirements.txt with base dependencies
 3. feat(config): add pydantic-settings based config
 4. feat(docker): add Dockerfile with multi-stage build
 5. chore(docker): add docker-compose.yml with Traefik labels
 6. feat(db): add async SQLite engine and session factory
 7. feat(models): add FileRecord ORM model
 8. feat(db): add table creation on startup via lifespan
 9. feat(auth): add basic cookie-based login system
10. feat(auth): add login page template
11. feat(auth): add login route and logout endpoint
12. feat(upload): add upload route with file and code validation
13. feat(upload): add upload form component with HTMX
14. feat(pages): add home page with upload form and search bar
15. feat(download): add download route serving PDF by code
16. feat(search): add HTMX-powered search with live results
17. feat(admin): add admin page with file listing
18. feat(admin): add delete endpoint for files
19. test(add): configure pytest and test fixtures
20. test(upload): add upload integration tests
21. test(download): add download integration tests
22. test(auth): add auth flow tests
23. chore(docker): add docker-compose.prod.yml for production
24. docs(readme): add comprehensive README with setup and usage
25. docs(plan): add DOCUMENTATION.md with development plan
```
