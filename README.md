# upSerArch

Aplicación web minimalista para homelab que permite subir archivos PDF y descargarlos mediante un código único.

## Stack Tecnológico

- **Backend**: Python 3.12 + FastAPI
- **Frontend**: HTMX + Tailwind CSS (CDN)
- **Templates**: Jinja2
- **Base de datos**: SQLite + SQLAlchemy async
- **Auth**: Cookie session
- **Contenedor**: Docker multi-stage build
- **Proxy**: Traefik

## Características

- Subir archivos PDF con código único
- Descargar archivos con código limpio (`/d/{codigo}`)
- Búsqueda en tiempo real con HTMX
- Panel de administración protegido
- Sobrescritura de archivos si el código ya existe
- Diseño responsive con Tailwind CSS

## Instalación Local

### Prerrequisitos

- Docker y Docker Compose

### Pasos

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/upSerArch.git
cd upSerArch
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus valores
```

3. Iniciar la aplicación:
```bash
docker compose up --build
```

4. Acceder a la aplicación:
- Inicio: http://localhost:8000
- Admin: http://localhost:8000/admin
- Login: http://localhost:8000/login

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Clave para firmar cookies | `CHANGE_ME_TO_A_RANDOM_STRING` |
| `ADMIN_USER` | Usuario admin | `admin` |
| `ADMIN_PASS` | Contraseña admin | `changeme123` |
| `DATABASE_URL` | URL de SQLite | `sqlite+aiosqlite:///./data/upserarch.db` |
| `UPLOAD_DIR` | Directorio de uploads | `/app/uploads` |
| `MAX_FILE_SIZE` | Tamaño máximo en bytes | `52428800` (50MB) |

## Despliegue con Traefik + Cloudflare

### 1. Configurar Cloudflare Tunnel

```bash
# Instalar cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Crear tunnel
cloudflared tunnel create upserarch
cloudflared tunnel route dns upserarch upserarch.tudominio.com
```

### 2. Configurar .env para production

```env
DOMAIN=upserarch.tudominio.com
SECRET_KEY=tu-clave-secreta-muy-larga
ADMIN_USER=admin
ADMIN_PASS=tu-contraseña-segura
```

### 3. Desplegar

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 4. Iniciar Cloudflare Tunnel

```bash
cloudflared tunnel run --url http://localhost:8000 upserarch
```

## Estructura del Proyecto

```
upSerArch/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy async
│   ├── models.py            # ORM models
│   ├── auth.py              # Autenticación
│   ├── routers/
│   │   ├── pages.py         # Rutas de páginas
│   │   ├── upload.py        # Upload de archivos
│   │   └── download.py      # Descarga y búsqueda
│   └── templates/
│       ├── base.html        # Layout base
│       ├── index.html       # Página principal
│       ├── admin.html       # Panel admin
│       ├── login.html       # Login
│       └── components/      # Fragmentos HTMX
├── tests/                   # Tests
├── uploads/                 # PDFs subidos
├── data/                    # Base de datos SQLite
├── Dockerfile
├── docker-compose.yml
└── docker-compose.prod.yml
```

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Página principal | No |
| GET | `/login` | Página de login | No |
| POST | `/login` | Autenticar usuario | No |
| GET | `/logout` | Cerrar sesión | No |
| GET | `/admin` | Panel de administración | Sí |
| POST | `/upload` | Subir archivo PDF | Sí |
| GET | `/d/{codigo}` | Descargar archivo por código | No |
| GET | `/search?q=` | Buscar archivo por código | No |
| DELETE | `/admin/{id}` | Eliminar archivo | Sí |
| GET | `/health` | Health check | No |

## Desarrollo

### Ejecutar tests

```bash
docker compose exec web pytest
```

### Ver logs

```bash
docker compose logs -f web
```

### Acceder al contenedor

```bash
docker compose exec web bash
```

## Licencia

MIT
