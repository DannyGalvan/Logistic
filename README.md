# StockFlow

> Sistema de inventario y logistica para PyME, con modulo web de calidad Pylint integrado.
> Proyecto academico: UMG - Ingenieria en Sistemas, curso Calidad de Software.

[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/release/python-3140/)
[![Django](https://img.shields.io/badge/django-5.2-success.svg)](https://docs.djangoproject.com/en/5.2/)
[![DRF](https://img.shields.io/badge/DRF-3.18-red.svg)](https://www.django-rest-framework.org/)
[![Pylint](https://img.shields.io/badge/pylint-4.1-yellowgreen.svg)](https://pylint.pycqa.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen.svg)](#tests-y-cobertura)
[![Coverage](https://img.shields.io/badge/coverage-Pending-orange.svg)](#tests-y-cobertura)

---

## Tabla de contenidos

1. [Descripcion general](#descripcion-general)
2. [Estado del proyecto](#estado-del-proyecto)
3. [Stack tecnologico](#stack-tecnologico)
4. [Requisitos previos](#requisitos-previos)
5. [Configuracion del entorno (.env)](#configuracion-del-entorno-env)
6. [Formas de ejecucion](#formas-de-ejecucion)
7. [Estructura del repositorio](#estructura-del-repositorio)
8. [Pylint: que es y como se usa](#pylint-que-es-y-como-se-usa)
9. [Tests y cobertura](#tests-y-cobertura)
10. [Debug](#debug)
11. [API REST](#api-rest)
12. [Arquitectura y patrones](#arquitectura-y-patrones)
13. [Como agregar una app nueva](#como-agregar-una-app-nueva)
14. [Troubleshooting](#troubleshooting)
15. [Licencia](#licencia)

---

## Descripcion general

StockFlow es un sistema de inventario y logistica para pequenas y medianas empresas, construido con Django 5.2 y Django REST Framework. La aplicacion cubre el ciclo completo:

- Catalogo de productos con categorias, marcas, unidades de medida y estrategias de rotacion (FIFO / FEFO).
- Almacenes con ubicaciones fisicas tipificadas (recepcion, almacenamiento, picking, despacho, cuarentena).
- Gestion de stock con lotes, fechas de caducidad, alertas (bajo minimo, proximo a vencer, vencido) y conteos ciclicos con aprobacion.
- Compras (OC) con confirmacion, recepcion parcial y total, y calculo de costo promedio ponderado.
- Ventas (OV) con confirmacion, picking sugerido por estrategia y despacho parcial o total.
- Kardex (historial valorizado), valoracion de inventario y movimientos por dia.
- Auditoria inmutable de cambios y autenticaciones.
- Exportadores CSV / Excel / PDF para todos los reportes.
- API REST documentada con OpenAPI/Swagger.
- Modulo web "Calidad" que ejecuta Pylint sobre el codigo del proyecto y permite analizar snippets didacticos.

La pieza central de la demostracion academica es la app `quality`: ejecuta Pylint contra `apps/` y `config/`, persiste las corridas, expone un catalogo en espanol de los mensajes mas frecuentes (tomado de `Pylint.md`) y permite comparar corridas para ver mejoras o regresiones.

## Estado del proyecto

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 1 | Esqueleto: configuracion, `core`, plantillas, base de tests | Completado |
| 2 | `accounts`: usuarios, roles, login, fixtures por rol | Pendiente |
| 3 | Maestros: `catalog`, `warehouses`, `partners` | Pendiente |
| 4 | `inventory`: stock, lotes, conteos, alertas | Pendiente |
| 5 | `purchasing`, `sales` | Pendiente |
| 6 | `reports`, `audit` | Pendiente |
| 7 | `quality`: modulo Pylint completo | Pendiente |
| 8 | UX final, seed demo, documentacion API | Pendiente |
| 9 | Endurecimiento: cobertura 90 %, Pylint 10/10 | Pendiente |
| 10 | DevOps: Docker, CI, IDE | Pendiente |

El plan completo esta en [`plans/plan-app-inventario.md`](plans/plan-app-inventario.md). La referencia teorica de Pylint esta en [`Pylint.md`](Pylint.md).

## Stack tecnologico

| Componente | Version | Proposito |
|------------|---------|-----------|
| Python | 3.14 | Lenguaje base |
| Django | 5.2 | Framework web |
| Django REST Framework | 3.18 | API REST |
| drf-spectacular | 0.28 | OpenAPI/Swagger |
| django-environ | 0.12 | Carga de `.env` |
| psycopg[binary] | 3.3 | Driver PostgreSQL |
| django-htmx | 1.23 | Interacciones HTMX |
| django-filter | 25.1 | Filtrado de querysets |
| django-crispy-forms | 2.4 | Formularios |
| openpyxl | 3.1 | Exportador XLSX |
| reportlab | 4.4 | Exportador PDF |
| whitenoise | 6.9 | Archivos estaticos |
| Pylint | 4.1 | Linter (version base, >=10.00/10 mantenido) |
| pylint-django | 2.6 | Plugin Pylint para Django |
| pytest | 9.1 | Framework de tests |
| pytest-django | 4.14 | Integracion pytest + Django |
| factory-boy | 3.3 | Fixtures de modelos |

## Requisitos previos

Antes de clonar el repositorio, asegurese de tener:

| Herramienta | Version minima | macOS | Linux | Windows |
|-------------|----------------|-------|-------|---------|
| Python | 3.14 | `brew install python@3.14` | `apt install python3.14` (o build desde fuente) | Instalador desde python.org |
| uv | 0.12+ | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `winget install astral-sh.uv` |
| Git | 2.40+ | `brew install git` | `apt install git` | `winget install git.git` |
| PostgreSQL (servidor academico) | 13+ | Acceso por red al server configurado | Acceso por red al server configurado | Acceso por red al server configurado |
| make | cualquier | `xcode-select --install` | `apt install build-essential` | `winget install gnuwin32-make` |
| Graphviz (opcional, para UML) | 2.50+ | `brew install graphviz` | `apt install graphviz` | `winget install graphviz` |
| Docker (opcional) | 24+ | Docker Desktop | docker-ce | Docker Desktop |

> Si su sistema no tiene Python 3.14 con wheels disponibles para todos los paquetes, cree el venv con 3.13: `uv venv --python 3.13 .venv`. Toda la configuracion es compatible hacia abajo.

> La cadena de conexion a PostgreSQL se lee exclusivamente desde la variable `DATABASE_URL` definida en `.env`. El repositorio no contiene credenciales; cada despliegue debe generar sus propias.

## Configuracion del entorno (.env)

Copie la plantilla incluida:

```bash
cp .env.example .env
```

Edite `.env` con sus valores. Las claves disponibles son:

| Variable | Obligatorio | Default | Descripcion |
|----------|-------------|---------|-------------|
| `DJANGO_SETTINGS_MODULE` | No | `config.settings.dev` | Modulo de configuracion activo |
| `DJANGO_SECRET_KEY` | Si | (none) | Clave secreta de Django (use `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`) |
| `DJANGO_DEBUG` | No | `False` | Habilita modo debug |
| `DJANGO_ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Hosts permitidos separados por coma |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | No | (vacio) | Origenes CSRF confiables |
| `DATABASE_URL` | Si | (plantilla) | Cadena `postgres://USER:PASS@HOST:PORT/DB` |
| `TEST_DATABASE_NAME` | No | `test_logistic` | Nombre de la BD que pytest crea/usa |
| `DB_CONN_MAX_AGE` | No | `60` | Tiempo de vida de conexiones (s) |
| `TIME_ZONE` | No | `America/Guatemala` | Zona horaria |
| `LANGUAGE_CODE` | No | `es` | Idioma de la UI |
| `PYLINT_TARGETS` | No | `apps,config` | Targets para Pylint |
| `PYLINT_FAIL_UNDER` | No | `9.5` | Nota minima aceptable |
| `PYLINT_TIMEOUT` | No | `180` | Timeout para Pylint (s) |
| `PYLINT_SNIPPET_MAX_BYTES` | No | `20000` | Tamanio maximo de snippet a analizar |
| `EXPIRY_ALERT_DAYS` | No | `30` | Dias para alerta de proximo a vencer |

## Formas de ejecucion

El proyecto ofrece seis formas de ejecutar la aplicacion. Elija la que mejor se adapte a su entorno.

### a) `uv` + Make (recomendado, multiplataforma)

```bash
# 1. Crear venv y verificar configuracion
make setup

# 2. Aplicar migraciones
make migrate

# 3. (Pendiente Fase 8) Cargar datos demo
make seed

# 4. Lanzar servidor de desarrollo
make run
```

Aplicacion disponible en <http://localhost:8000>.

### b) `uv` + comandos directos

```bash
uv venv --python 3.14 --clear .venv
VIRTUAL_ENV=$(pwd)/.venv uv pip install -r requirements/dev.txt
test -f .env || cp .env.example .env
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

### c) `venv` + pip tradicional

```bash
python3.14 -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate            # Windows (PowerShell)
pip install -r requirements/dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### d) Windows PowerShell (`run.ps1`)

En Windows use el script `scripts/run.ps1`:

```powershell
pwsh scripts/run.ps1 -Task setup
pwsh scripts/run.ps1 -Task migrate
pwsh scripts/run.ps1 -Task run
```

Tareas disponibles: `setup`, `migrate`, `seed`, `run`, `test`, `test-fast`, `cov`, `lint`, `lint-json`, `lint-report`, `check`, `superuser`.

### e) Docker

```bash
docker compose up --build
```

La imagen usa `python:3.13-slim`, instala `requirements/prod.txt` y ejecuta `gunicorn`. Ajuste `DJANGO_SETTINGS_MODULE` a `config.settings.prod` en `.env` antes de levantar.

### f) Docker con perfil debug (para VS Code / PyCharm)

```bash
docker compose --profile debug up
```

Levanta `web-debug` con `debugpy` escuchando en `0.0.0.0:5678`. Conectese desde su IDE para depurar.

## Estructura del repositorio

```
.
|-- manage.py                          # Entrada CLI de Django
|-- pyproject.toml                     # Dependencias + pytest + coverage + pylint
|-- requirements/{base,dev,prod}.txt   # Pinning por entorno
|-- .pylintrc                          # Configuracion de Pylint (nota >= 9.5)
|-- .editorconfig                      # Estilo de codigo
|-- .pre-commit-config.yaml            # Hooks de pre-commit (incluye pylint)
|-- Makefile                           # Atajos multiplataforma
|-- scripts/run.ps1                    # Equivalente Windows del Makefile
|-- config/                            # Paquete de configuracion
|   |-- settings/{base,dev,prod,test}  # Configuracion dividida por entorno
|   |-- urls.py                        # Enrutador raiz
|   |-- api_urls.py                    # Enrutador de API REST
|   |-- wsgi.py  asgi.py
|-- apps/                              # Aplicaciones Django
|   |-- core/                          # Modelos abstractos, menu, estado, mixins
|   |-- accounts/                      # Usuarios, roles (stub Fase 1)
|   |-- catalog/ warehouses/ partners/ # Maestros (stubs)
|   |-- purchasing/ sales/              # Operaciones (stubs)
|   |-- inventory/                     # Nucleo (stub)
|   |-- reports/ audit/                # Reportes y bitacora (stubs)
|   |-- quality/                       # Modulo Pylint (stub)
|-- templates/                         # Plantillas Django (base, partials, errores)
|-- static/                            # CSS, JS, imagenes
|-- tests/                             # Tests cross-app + conftest
|-- docs/                              # Documentacion tecnica y UML (Fase 10)
|-- plans/                             # Plan maestro
|-- Pylint.md                          # Referencia teorica Pylint
```

## Pylint: que es y como se usa

### Que es Pylint

Pylint es un analizador estatico de codigo Python que verifica:

- Errores de sintaxis y excepciones no manejadas.
- Errores logicos (variables no definidas, import sin usar).
- Convenciones de estilo (PEP 8, naming conventions).
- Refactorizaciones sugeridas (code smells, duplicacion, complejidad).
- Advertencias especificas de frameworks (via plugins como `pylint-django`).

Pylint asigna una **nota de 0 a 10** que resume la calidad del codigo. Categorias:

| Letra | Significado |
|-------|-------------|
| `C` | Convention (estilo) |
| `R` | Refactor (code smell) |
| `W` | Warning (posible bug) |
| `E` | Error (probable bug) |
| `F` | Fatal (error de sintaxis o import) |
| `I` | Informational (sugerencia) |

En StockFlow la nota minima es **9.5** y la meta es **10.00/10**.

### Comandos basicos

```bash
# Analisis rapido con la configuracion del proyecto
make lint

# Salida JSON para integracion con otras herramientas
make lint-json

# Corrida persistida en BD (visible en /calidad/ cuando este implementado)
make lint-report

# Generar un archivo .pylintrc por defecto (referencia)
.venv/bin/python -m pylint --generate-rcfile

# Desactivar un mensaje especifico en linea (comentado con motivo)
.venv/bin/python -m pylint apps config tests --disable=W0611
```

### Configuracion del proyecto

StockFlow mantiene la configuracion en `.pylintrc`. Mensajes desactivados y motivo:

| Mensaje | Motivo |
|---------|--------|
| `too-few-public-methods` | Clases `Meta` de Django, DTOs y Protocols tienen pocos metodos por diseno. |
| `wildcard-import`, `unused-wildcard-import` | Patron canonico de Django para modulos `settings/*` (importan todo de `base` y sobreescriben). |
| `too-many-ancestors` | `BaseListView` apila cinco mixins de Django por diseno; forzar a reducir la jerarquia anade complejidad sin valor. |

Ademas, el archivo `apps/core/models.py:KardexRow` desactiva inline `too-many-instance-attributes`, `too-many-arguments` y `too-many-positional-arguments` con comentario explicito: agrupa los ocho campos contables del Kardex y agruparlos en otro DTO restaria claridad.

### Como se lee la nota

- **10.00/10** Codigo limpio, sin advertencias.
- **9.00 a 9.99** Calidad alta, solo advertencias de estilo o diseno discutibles.
- **7.00 a 8.99** Aceptable para refactor; requiere tareas.
- **< 7.00** Requiere intervencion antes de produccion.

Para superar el umbral:

1. Revise la salida: cada mensaje incluye `archivo:linea: columna: CODIGO: descripcion (simbolo)`.
2. Corrija el codigo en lugar de desactivar el mensaje.
3. Solo si la desactivacion es legitima, agreguela a `.pylintrc` o inline con comentario que justifique.

### Modulo web `/calidad/`

Disponible en la Fase 7. Permitira:

- Ejecutar Pylint sobre el codigo del proyecto y guardar la corrida en BD.
- Ver historial, comparar dos ejecuciones y ver la evolucion de la nota.
- Analizar snippets didacticos que demuestran errores comunes.
- Consultar un catalogo en espanol con explicacion y ejemplos bueno/malo por mensaje.
- Mostrar la configuracion `.pylintrc` linea por linea.

## Tests y cobertura

```bash
# Suite completa
make test

# Suite sin tests marcados como slow
make test-fast

# Cobertura con reporte terminal + html
make cov
```

- Configuracion en `pyproject.toml` bajo `[tool.pytest.ini_options]` y `[tool.coverage.*]`.
- Umbral de cobertura: **90 %** (`fail_under = 90`).
- Tests usan **SQLite** en memoria (ver `config/settings/test.py`) para no tocar el PostgreSQL remoto.
- `tests/conftest.py` expone fixtures compartidas (en expansion conforme se agreguen apps).

Estado actual:

| Metrica | Valor |
|---------|-------|
| Tests | 17 pasando |
| Cobertura | Pendiente (solo nucleo en Fase 1) |

## Debug

### VS Code

Archivo `.vscode/launch.json` (se agrega en Fase 10). Configuraciones:

- "Django: runserver" - inicia el servidor con `debugpy`.
- "Pytest: archivo actual" / "Pytest: todo".
- "Pylint: proyecto".

### PyCharm

En Fase 10 se incluyen configuraciones en `.idea/runConfigurations/`. Mientras tanto, use la configuracion "Django Server" estandar apuntando a `manage.py`.

### Docker

Use el perfil debug:

```bash
docker compose --profile debug up
```

Adjunte al puerto `5678` desde VS Code o PyCharm (`Run > Attach to Docker Container`).

### django-debug-toolbar

Instalado en `config/settings/dev.py` para entornos de desarrollo. Aparece como un panel lateral en `/admin/` y otras vistas.

## API REST

Disponible en `/api/v1/` (Fase 1 expone solo `/api/schema/` y `/api/docs/`):

- Autenticacion: Session y Token (`rest_framework.authtoken`).
- Permisos: `IsAuthenticated` + `DjangoModelPermissions`.
- Paginacion: 20 elementos por pagina.
- Filtros: `django-filter`, `SearchFilter`, `OrderingFilter`.
- Documentacion: OpenAPI 3 en `/api/schema/` y Swagger UI en `/api/docs/`.

## Arquitectura y patrones

| Capa | Patron | Archivo de referencia |
|------|--------|-----------------------|
| Configuracion | Split settings | `config/settings/{base,dev,prod,test}.py` |
| Estado | State (maquina generica) | `apps/core/state.py` |
| Errores | Domain errors | `apps/core/exceptions.py` |
| Menu | Registry + Singleton | `apps/core/menu.py` |
| Middleware | Contexto (ContextVar) | `apps/core/middleware.py` |
| Vistas | Template Method (mixins) | `apps/core/views.py` |
| DTO | Dataclass inmutable | `apps/core/models.py:KardexRow` |

Las apps de dominio (Fases 2+) usan adicionalmente:

- **Command** para movimientos de stock.
- **Facade** en `InventoryService` que orquesta Commands.
- **Observer** para senales de cambio.
- **Strategy + Registry** para asignacion de stock (FIFO / FEFO).
- **Adapter** para el runner de Pylint.
- **Strategy + Factory** para exportadores CSV / XLSX / PDF.

## Como agregar una app nueva

1. Cree el paquete en `apps/<nombre>/` siguiendo el patron de la seccion "Estructura".
3. Agregue `apps.<nombre>` a `INSTALLED_APPS` en `config/settings/base.py`.
4. Incluya `path("", include("apps.<nombre>.urls"))` en `config/urls.py`.
5. Registre items del menu en `apps.<nombre>.apps.<Nombre>Config.ready()` usando `MenuRegistry.register(...)`.
6. Agregue el modelo a `apps.audit.registry.register(...)` para auditoria (cuando exista).
7. Cree tests en `apps/<nombre>/tests/`.
8. Ejecute `make check` antes de commitear.

## Troubleshooting

| Sintoma | Causa | Solucion |
|---------|------|----------|
| `pylint` reporta `database "logistic" does not exist` | La BD remota no esta creada o el usuario no tiene `CREATEDB`. | Cree `logistic` con `CREATE DATABASE logistic;` desde un usuario con permiso, o use el `.env` con una BD propia. |
| `pytest` falla con `permission denied to create database` | El usuario de BD no tiene `CREATEDB`. | StockFlow usa SQLite en memoria para tests, asi que este error solo aparece si cambio la configuracion. Revise `config/settings/test.py`. |
| `pip install` falla en Python 3.14 por falta de wheels | Algunos no tienen wheel para 3.14 todavia. | Cree el venv con 3.13: `uv venv --python 3.13 .venv`. |
| `pyreverse` no genera PNG | Falta Graphviz. | Instale con `brew install graphviz` / `apt install graphviz`. Use `-o puml` o `-o mmd` como alternativa. |
| Puerto 8000 ocupado | Otro proceso usa el puerto. | `lsof -i :8000` para identificar y detenerlo, o use otro puerto: `python manage.py runserver 0.0.0.0:8001`. |
| `pylint` excede el tiempo | El codigo es muy grande o hay ciclos. | Suba `PYLINT_TIMEOUT` en `.env`. |
| `pre-commit` falla por pylint | El hook encontro nuevos mensajes. | Corrija el codigo. Si la regla debe estar desactivada, agreguela a `.pylintrc` con motivo. |

---

## Licencia

MIT - consulte el archivo [LICENSE](LICENSE) si esta disponible en su distribucion. En el repositorio academico la licencia es "Uso academico - UMG".
