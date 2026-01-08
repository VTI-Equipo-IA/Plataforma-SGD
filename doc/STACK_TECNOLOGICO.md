# 🛠️ Stack Tecnológico - Editor de Planes PTD

## 📋 Documento para Instalación en Servidor

Este documento detalla todas las tecnologías, dependencias y requisitos necesarios para instalar y ejecutar la plataforma **Editor de Planes PTD** en un servidor de producción.

---

## 📑 Tabla de Contenidos

1. [Requisitos del Sistema](#-requisitos-del-sistema)
2. [Software Base Requerido](#-software-base-requerido)
3. [Dependencias de Python](#-dependencias-de-python)
4. [Base de Datos PostgreSQL](#-base-de-datos-postgresql)
5. [Servicios Externos y APIs](#-servicios-externos-y-apis)
6. [Servidor Web y Deployment](#-servidor-web-y-deployment)
7. [Herramientas de Desarrollo (Opcional)](#-herramientas-de-desarrollo-opcional)
8. [Configuración del Sistema Operativo](#-configuración-del-sistema-operativo)
9. [Checklist de Instalación](#-checklist-de-instalación)
10. [Requisitos de Hardware](#-requisitos-de-hardware)

---

## 💻 Requisitos del Sistema

### Sistema Operativo Compatible

La plataforma es compatible con:

- ✅ **Linux** (Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+)
- ✅ **Windows Server** 2019+
- ✅ **macOS** 11+ (Big Sur o superior)

**Recomendado para producción:** Ubuntu Server 22.04 LTS o superior

---

## 📦 Software Base Requerido

### 1. Python

**Versión mínima:** Python 3.10  
**Versión recomendada:** Python 3.11+

#### Instalación en Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo apt install python3-pip
```

#### Instalación en CentOS/RHEL:
```bash
sudo dnf install python3.11 python3.11-devel
sudo dnf install python3-pip
```

#### Instalación en Windows Server:
- Descargar desde: https://www.python.org/downloads/
- Instalar con opción "Add Python to PATH"

#### Verificar instalación:
```bash
python3 --version  # Debe mostrar 3.10+
pip3 --version
```

---

### 2. PostgreSQL

**Versión mínima:** PostgreSQL 13  
**Versión recomendada:** PostgreSQL 15+

#### Instalación en Ubuntu/Debian:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Instalación en CentOS/RHEL:
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Instalación en Windows Server:
- Descargar desde: https://www.postgresql.org/download/windows/
- Instalar con Stack Builder (incluye pgAdmin)

#### Verificar instalación:
```bash
psql --version  # Debe mostrar 13+
```

#### Configuración inicial:
```bash
# Acceder como usuario postgres
sudo -u postgres psql

# Dentro de psql:
CREATE USER ptd_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE ptd_database OWNER ptd_user;
GRANT ALL PRIVILEGES ON DATABASE ptd_database TO ptd_user;
\q
```

---

### 3. Git (Opcional pero recomendado)

```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo dnf install git

# Verificar
git --version
```

---

## 🐍 Dependencias de Python

### Instalación de Dependencias

Todas las dependencias están listadas en `requirements.txt`. Para instalarlas:

```bash
# Crear entorno virtual
python3 -m venv editor
source editor/bin/activate  # Linux/macOS
# o
.\editor\Scripts\Activate.ps1  # Windows

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

---

### Dependencias Principales (Core)

#### Framework Web

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **Flask** | 3.0.3 | Framework web principal |
| **Flask-WTF** | 1.2.1 | Formularios y validación |
| **Flask-SQLAlchemy** | 3.1.1 | ORM para base de datos |
| **Flask-CSRF** | 0.9.2 | Protección contra CSRF |
| **WTForms** | 3.1.2 | Validación de formularios |

#### Base de Datos

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **psycopg2-binary** | 2.9.10 | Adaptador PostgreSQL para Python |
| **SQLAlchemy** | 2.0.43 | ORM y abstracción de BD |

#### Procesamiento de Datos

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **pandas** | 2.3.2 | Análisis y manipulación de datos |
| **numpy** | 2.3.2 | Operaciones numéricas |
| **openpyxl** | 3.1.5 | Lectura/escritura de archivos Excel |

#### Seguridad

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **cryptography** | 43.0.1 | Cifrado Fernet para API keys |
| **python-dotenv** | 1.1.1 | Gestión de variables de entorno |

---

### Dependencias de Inteligencia Artificial

#### LangChain y OpenAI

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **langchain** | 0.3.27 | Framework para aplicaciones LLM |
| **langchain-community** | 0.3.27 | Integraciones comunitarias |
| **langchain-core** | 0.3.74 | Núcleo de LangChain |
| **langchain-openai** | 0.3.30 | Integración con OpenAI |
| **langchain-text-splitters** | 0.3.9 | División de textos |
| **langsmith** | 0.4.14 | Monitoreo de LangChain |
| **openai** | 1.100.2 | Cliente oficial de OpenAI |
| **tiktoken** | 0.11.0 | Tokenización para modelos OpenAI |

#### Búsqueda Vectorial

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **faiss-cpu** | 1.12.0 | Búsqueda de similitud vectorial |

#### Procesamiento de Documentos

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **pypdf** | 6.0.0 | Lectura de archivos PDF |
| **python-docx** | 1.2.0 | Lectura de documentos Word |
| **lxml** | 6.0.0 | Procesamiento XML/HTML |

---

### Dependencias de Validación y Serialización

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **pydantic** | 2.11.7 | Validación de datos |
| **pydantic-settings** | 2.10.1 | Gestión de configuración |
| **pydantic_core** | 2.33.2 | Núcleo de Pydantic |
| **annotated-types** | 0.7.0 | Tipos anotados |
| **dataclasses-json** | 0.6.7 | Serialización de dataclasses |
| **marshmallow** | 3.26.1 | Validación y serialización |
| **orjson** | 3.11.2 | JSON rápido |

---

### Dependencias HTTP y Networking

#### HTTP Síncrono

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **requests** | 2.32.5 | Cliente HTTP |
| **urllib3** | 2.5.0 | Pool de conexiones HTTP |
| **certifi** | 2025.8.3 | Certificados SSL |
| **charset-normalizer** | 3.4.3 | Detección de charset |
| **idna** | 3.10 | Soporte para dominios internacionales |
| **requests-toolbelt** | 1.0.0 | Utilidades para requests |

#### HTTP Asíncrono

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **aiohttp** | 3.12.15 | Cliente/servidor HTTP asíncrono |
| **aiohappyeyeballs** | 2.6.1 | Resolución DNS rápida |
| **aiosignal** | 1.4.0 | Manejo de señales async |
| **frozenlist** | 1.7.0 | Lista inmutable para asyncio |
| **multidict** | 6.6.4 | Diccionarios multi-valor |
| **yarl** | 1.20.1 | URLs para asyncio |
| **propcache** | 0.3.2 | Cache de propiedades |

#### HTTP Core

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **httpx** | 0.28.1 | Cliente HTTP moderno |
| **httpcore** | 1.0.9 | Núcleo HTTP |
| **httpx-sse** | 0.4.1 | Server-Sent Events |
| **h11** | 0.16.0 | Protocolo HTTP/1.1 |
| **anyio** | 4.10.0 | Biblioteca async unificada |
| **sniffio** | 1.3.1 | Detección de backend async |

---

### Dependencias de Utilidades

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **python-dateutil** | 2.9.0.post0 | Parsing de fechas |
| **pytz** | 2025.2 | Zonas horarias |
| **tzdata** | 2025.2 | Base de datos de zonas horarias |
| **typing_extensions** | 4.14.1 | Extensiones de tipado |
| **typing-inspect** | 0.9.0 | Inspección de tipos |
| **typing-inspection** | 0.4.1 | Inspección de anotaciones |
| **mypy_extensions** | 1.1.0 | Extensiones para MyPy |
| **attrs** | 25.3.0 | Clases sin boilerplate |
| **six** | 1.17.0 | Compatibilidad Python 2/3 |
| **colorama** | 0.4.6 | Colores en terminal |
| **distro** | 1.9.0 | Información de distribución Linux |
| **greenlet** | 3.2.4 | Concurrencia lightweight |
| **tenacity** | 9.1.2 | Reintentos con backoff |
| **tqdm** | 4.67.1 | Barras de progreso |
| **packaging** | 25.0 | Parsing de versiones |
| **et_xmlfile** | 2.0.0 | Lectura de XML (openpyxl) |

---

### Dependencias de Procesamiento de Texto

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **regex** | 2025.7.34 | Expresiones regulares avanzadas |
| **PyYAML** | 6.0.2 | Parsing de archivos YAML |
| **jsonpatch** | 1.33 | Parches JSON (RFC 6902) |
| **jsonpointer** | 3.0.0 | JSON Pointer (RFC 6901) |

---

### Dependencias de Compresión

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **zstandard** | 0.24.0 | Compresión Zstandard |
| **jiter** | 0.10.0 | Iterador JSON rápido |

---

### Dependencias del Sistema Comité (Opcional)

Si se usa el sistema de comité de agentes especializado:

```bash
cd comite
pip install -r requirements.txt
```

**Dependencias adicionales del Comité:**

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| **langchain** | >=0.2.10 | Framework LLM |
| **langchain-openai** | >=0.1.14 | OpenAI con LangChain |
| **langchain-community** | >=0.2.9 | Integraciones |
| **pandas** | >=2.0.3 | Análisis de datos |
| **openai** | >=1.40.0 | Cliente OpenAI |
| **faiss-cpu** | >=1.8.0 | Búsqueda vectorial |
| **PyPDF2** | >=3.0.1 | Procesamiento PDF |
| **tiktoken** | >=0.7.0 | Tokenización |
| **python-docx** | - | Documentos Word |
| **openpyxl** | - | Archivos Excel |
| **langchain-text-splitters** | - | División de textos |

---

## 🗄️ Base de Datos PostgreSQL

### Configuración del Esquema

La aplicación requiere una base de datos PostgreSQL con tipos ENUM personalizados y una tabla principal.

#### Tipos ENUM Requeridos

```sql
CREATE TYPE tipo_nivel_madurez AS ENUM ('Insuficiente', 'Basico', 'Medio');
CREATE TYPE tipo_autor AS ENUM ('Comite', 'Agente Maestro');
CREATE TYPE tipo_actividad_hito AS ENUM ('Actividad', 'Hito');
```

#### Tabla Principal: ptd_planes

```sql
CREATE TABLE ptd_planes (
    id SERIAL PRIMARY KEY,
    "Dimension" TEXT NOT NULL,
    "Subdimension" TEXT,
    "Instrumento" TEXT,
    "Nivel_de_madurez" tipo_nivel_madurez,
    "Hito" TEXT,
    "Actividad" TEXT,
    "Autor" tipo_autor,
    "Tipo" tipo_actividad_hito,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dimension ON ptd_planes("Dimension");
CREATE INDEX idx_subdimension ON ptd_planes("Subdimension");
CREATE INDEX idx_autor ON ptd_planes("Autor");
```

#### Tabla de Prompts: ptd_prompts

```sql
CREATE TABLE ptd_prompts (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    version_label VARCHAR(255),
    fuente VARCHAR(255) DEFAULT 'Editor Web',
    notas TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompts_fecha ON ptd_prompts(fecha_creacion DESC);

-- Trigger para auto-actualización de timestamp
CREATE OR REPLACE FUNCTION update_prompts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_prompts_timestamp
BEFORE UPDATE ON ptd_prompts
FOR EACH ROW
EXECUTE FUNCTION update_prompts_timestamp();
```

**Propósito de ptd_prompts:**
- Versionado del SuperPrompt del Agente Maestro
- Historial completo de cambios con notas
- Restauración a versiones anteriores
- Integración automática con scripts de generación
- Gestión desde interfaz web en `/prompts/`

#### Script de Creación Automatizado

```bash
# Desde el directorio del proyecto
cd db
python ejecutar_scripts_sql.py
```

O manualmente:
```bash
psql -h localhost -U ptd_user -d ptd_database -f db/crear_tabla_ptd.sql
```

---

### Configuración de Acceso Remoto (Producción)

#### 1. Editar `postgresql.conf`:
```bash
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Cambiar:
```
listen_addresses = '*'  # Escuchar en todas las interfaces
```

#### 2. Editar `pg_hba.conf`:
```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Agregar:
```
# IPv4 local connections:
host    ptd_database    ptd_user    0.0.0.0/0    scram-sha-256
```

#### 3. Reiniciar PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## 🔑 Servicios Externos y APIs

### OpenAI API (Requerido para IA)

**Propósito:** Regeneración de planes con GPT-4

#### Requisitos:
- Cuenta en OpenAI: https://platform.openai.com/
- API Key con acceso a GPT-4o o GPT-4
- Créditos suficientes ($5+ recomendado para pruebas)

#### Configuración:
```bash
# En el archivo .env
OPENAI_API_KEY=sk-tu-api-key-aqui
AI_PROVIDER=openai
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000
```

#### Modelos Soportados:
- `gpt-4o` (recomendado, más rápido)
- `gpt-4` (más preciso pero más lento)
- `gpt-4-turbo`

---

## 🚀 Servidor Web y Deployment

### Opción 1: Gunicorn (Recomendado para Producción)

**Gunicorn** es un servidor WSGI HTTP para Python.

#### Instalación:
```bash
pip install gunicorn
```

#### Ejecutar:
```bash
# Modo básico
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Modo con logs
gunicorn -w 4 -b 0.0.0.0:5000 app:app \
  --access-logfile /var/log/gunicorn/access.log \
  --error-logfile /var/log/gunicorn/error.log \
  --log-level info
```

#### Configuración recomendada:
- **Workers (-w):** 2-4 × número de CPUs
- **Timeout:** 300s (para procesos IA largos)
- **Keep-alive:** 5s

#### Crear archivo `gunicorn.conf.py`:
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 300
keepalive = 5
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
```

Ejecutar con:
```bash
gunicorn -c gunicorn.conf.py app:app
```

---

### Opción 2: uWSGI

#### Instalación:
```bash
pip install uwsgi
```

#### Ejecutar:
```bash
uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4 --threads 2
```

---

### Opción 3: Flask Development Server (Solo Desarrollo)

⚠️ **NO usar en producción**

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

O con `python`:
```bash
python app.py
```

---

### Nginx como Proxy Inverso (Recomendado)

#### Instalación:
```bash
sudo apt install nginx
```

#### Configuración `/etc/nginx/sites-available/editor-planes`:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout largo para regeneración IA
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }

    location /static {
        alias /ruta/a/editor-planes/static;
        expires 30d;
    }

    location /img {
        alias /ruta/a/editor-planes/img;
        expires 30d;
    }
}
```

#### Activar sitio:
```bash
sudo ln -s /etc/nginx/sites-available/editor-planes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### SSL/TLS con Let's Encrypt (Opcional pero recomendado)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

### Systemd Service (Autoarranque)

#### Crear `/etc/systemd/system/editor-planes.service`:
```ini
[Unit]
Description=Editor de Planes PTD
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/ruta/a/editor-planes
Environment="PATH=/ruta/a/editor-planes/editor/bin"
ExecStart=/ruta/a/editor-planes/editor/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Activar servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl start editor-planes
sudo systemctl enable editor-planes
sudo systemctl status editor-planes
```

---

## 🔧 Herramientas de Desarrollo (Opcional)

### Para Desarrollo Local

| Herramienta | Propósito |
|-------------|-----------|
| **VS Code** | IDE principal |
| **pgAdmin 4** | Administración de PostgreSQL |
| **Postman** | Pruebas de API |
| **Git** | Control de versiones |

### Extensiones de VS Code Recomendadas

- Python (Microsoft)
- Pylance (Microsoft)
- SQLTools (PostgreSQL)
- GitLens
- Prettier

---

## ⚙️ Configuración del Sistema Operativo

### Variables de Entorno (.env)

Crear archivo `.env` en la raíz del proyecto:

```bash
# ========================================
# FLASK CONFIGURATION
# ========================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=genera_una_clave_super_segura_de_32_caracteres_o_mas

# ========================================
# DATABASE CONFIGURATION
# ========================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ptd_database
POSTGRES_USER=ptd_user
POSTGRES_PASSWORD=tu_password_seguro

# O usa la URI completa:
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://ptd_user:tu_password@localhost:5432/ptd_database

# ========================================
# SECURITY
# ========================================
# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_SECRET=tu_clave_fernet_base64

# ========================================
# OPENAI API
# ========================================
OPENAI_API_KEY=sk-tu-api-key-de-openai
AI_PROVIDER=openai
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000

# ========================================
# APPLICATION SETTINGS
# ========================================
MAX_CONTENT_LENGTH=20971520  # 20 MB
PAGE_SIZE=25

# ========================================
# COMITÉ (Opcional)
# ========================================
GOB_DB_ROUNDS=3
```

#### Generar SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Generar FERNET_SECRET:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### Permisos de Archivos

```bash
# Propietario del proyecto
sudo chown -R www-data:www-data /ruta/a/editor-planes

# Permisos de archivos
chmod 644 /ruta/a/editor-planes/.env
chmod 755 /ruta/a/editor-planes

# Logs
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
```

---

### Firewall (UFW en Ubuntu)

```bash
# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Permitir PostgreSQL (solo si acceso remoto)
sudo ufw allow 5432/tcp

# Activar firewall
sudo ufw enable
sudo ufw status
```

---

## ✅ Checklist de Instalación

Use este checklist para verificar que todo esté instalado correctamente:

### Software Base
- [ ] Python 3.10+ instalado y en PATH
- [ ] pip actualizado (`pip install --upgrade pip`)
- [ ] PostgreSQL 13+ instalado y corriendo
- [ ] Git instalado (opcional)

### Base de Datos
- [ ] Usuario PostgreSQL creado (`ptd_user`)
- [ ] Base de datos creada (`ptd_database`)
- [ ] Permisos otorgados al usuario
- [ ] Tabla `ptd_planes` creada con tipos ENUM
- [ ] Índices creados
- [ ] Conexión remota configurada (si aplica)

### Dependencias Python
- [ ] Entorno virtual creado (`python3 -m venv editor`)
- [ ] Entorno virtual activado
- [ ] `requirements.txt` instalado sin errores
- [ ] `comite/requirements.txt` instalado (si se usa Comité)

### Configuración
- [ ] Archivo `.env` creado con todas las variables
- [ ] `SECRET_KEY` generada y configurada
- [ ] `FERNET_SECRET` generada y configurada
- [ ] `SQLALCHEMY_DATABASE_URI` correcta
- [ ] `OPENAI_API_KEY` configurada (si se usa IA)

### Servidor Web
- [ ] Gunicorn instalado
- [ ] Archivo `gunicorn.conf.py` creado
- [ ] Nginx instalado (si se usa como proxy)
- [ ] Configuración de Nginx creada
- [ ] Servicio systemd creado (si aplica)
- [ ] SSL/TLS configurado (si aplica)

### Pruebas
- [ ] Aplicación arranca sin errores
- [ ] Se puede acceder a `http://localhost:5000`
- [ ] Conexión a base de datos funciona
- [ ] Importación de Excel funciona
- [ ] Regeneración con IA funciona (si configurada)
- [ ] No hay errores en logs

---

## 💾 Requisitos de Hardware

### Mínimo (Desarrollo/Pruebas)

- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disco:** 20 GB SSD
- **Red:** 10 Mbps

### Recomendado (Producción - Bajo tráfico)

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 50 GB SSD
- **Red:** 100 Mbps

### Ideal (Producción - Alto tráfico)

- **CPU:** 8+ cores
- **RAM:** 16+ GB
- **Disco:** 100 GB SSD (NVMe)
- **Red:** 1 Gbps

---

## 🌐 Puertos Utilizados

| Puerto | Servicio | Propósito |
|--------|----------|-----------|
| **5000** | Flask/Gunicorn | Aplicación web |
| **5432** | PostgreSQL | Base de datos |
| **80** | Nginx | HTTP (sin SSL) |
| **443** | Nginx | HTTPS (con SSL) |

---

## 📊 Estimación de Recursos

### Espacio en Disco

- **Código fuente:** ~50 MB
- **Dependencias Python:** ~500 MB
- **PostgreSQL:** ~200 MB (base)
- **Logs:** 1-10 GB/mes (según uso)
- **Total recomendado:** 20-50 GB

### Memoria RAM

- **Flask + Gunicorn (4 workers):** ~500 MB
- **PostgreSQL:** ~256 MB (mínimo)
- **Procesos IA (LangChain + OpenAI):** ~1-2 GB durante regeneración
- **Sistema operativo:** ~1 GB
- **Total recomendado:** 4-8 GB

### CPU

- **Operaciones normales:** 1-2 cores suficientes
- **Regeneración con IA:** Uso intensivo temporal (2-4 cores)
- **Total recomendado:** 2-4 cores

---

## 🔒 Consideraciones de Seguridad

### Checklist de Seguridad

- [ ] **Cambiar todas las contraseñas por defecto**
- [ ] **Usar HTTPS en producción**
- [ ] **Configurar firewall (UFW/firewalld)**
- [ ] **Restringir acceso SSH (solo clave pública)**
- [ ] **Actualizar sistema operativo regularmente**
- [ ] **Mantener PostgreSQL actualizado**
- [ ] **No exponer .env en Git (usar .gitignore)**
- [ ] **Validar permisos de archivos (644 para .env)**
- [ ] **Configurar backups automáticos de BD**
- [ ] **Limitar intentos de login**
- [ ] **Usar passwords fuertes (20+ caracteres)**
- [ ] **Rotar API keys periódicamente**

---

## 📝 Notas Importantes

### ⚠️ No incluir en producción:

- `FLASK_DEBUG=True` (solo desarrollo)
- Servidor Flask nativo (`flask run`)
- Contraseñas en código fuente
- API keys en Git
- Acceso SSH con password

### ✅ Obligatorio en producción:

- Gunicorn o uWSGI
- Nginx como proxy inverso
- SSL/TLS (HTTPS)
- Firewall configurado
- Backups automáticos
- Monitoreo de logs
- Rotación de logs

---

## 🆘 Soporte y Troubleshooting

### Problemas Comunes

#### 1. Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar puerto
sudo netstat -plnt | grep 5432

# Probar conexión
psql -h localhost -U ptd_user -d ptd_database
```

#### 2. Dependencias Python no se instalan
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar con caché limpia
pip install --no-cache-dir -r requirements.txt

# Instalar dependencias de sistema (Ubuntu)
sudo apt install python3-dev libpq-dev
```

#### 3. Gunicorn no arranca
```bash
# Ver logs
journalctl -u editor-planes -n 50

# Verificar permisos
ls -la /ruta/a/editor-planes

# Probar manualmente
/ruta/a/editor-planes/editor/bin/gunicorn -b 0.0.0.0:5000 app:app
```

#### 4. Error de API OpenAI
```bash
# Verificar API key
echo $OPENAI_API_KEY

# Probar conexión
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## 📚 Documentación Adicional

- **Manual de Usuario:** Ver `MANUAL_USUARIO.md`
- **README Técnico:** Ver `README.md`
- **Historial de Desarrollo:** Ver `HISTORIAL_DESARROLLO.md`
- **Changelog:** Ver `CHANGELOG.md`
- **Integración Comité:** Ver `INTEGRATION_COMITE.md`

---

**Última actualización:** 17 de Noviembre de 2025  
**Versión del Stack:** 2.0  
**Mantenido por:** VTI - Equipo IA, Universidad de Chile
