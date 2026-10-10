# StockFlow

Sistema de **inventario y logistica** construido con Django 5.2 + Django REST Framework, que
ademas sirve como **demostracion del uso de Pylint** en un proyecto real (UMG — Ingenieria en
Sistemas, curso *Calidad de Software*).

- Codigo con arquitectura por capas (vistas → services → modelos), principios SOLID y patrones de diseno.
- Pylint obligatorio: `.pylintrc` versionado, `make lint`, pre-commit, CI y un modulo web **/calidad/**
  que ejecuta Pylint y explica los mensajes en espanol.
- 200 tests (pytest) con cobertura ≥ 90 % y Pylint **10.00/10**.

Plan de implementacion: [`plans/plan-app-inventario.md`](plans/plan-app-inventario.md) ·
Avance: [`plans/PROGRESS.md`](plans/PROGRESS.md) · Teoria de Pylint: [`plans/Pylint.md`](plans/Pylint.md) ·
Arquitectura: [`docs/arquitectura.md`](docs/arquitectura.md)

## Tabla de contenidos

1. [Descripcion y arquitectura](#1-descripcion-y-arquitectura)
2. [Funcionalidades y roles](#2-funcionalidades-y-roles)
3. [Requisitos](#3-requisitos)
4. [Configuracion (.env)](#4-configuracion-env)
5. [Formas de ejecucion](#5-formas-de-ejecucion)
6. [Usuarios demo](#6-usuarios-demo)
7. [Pylint](#7-pylint)
8. [Tests y cobertura](#8-tests-y-cobertura)
9. [Debug](#9-debug)
10. [API REST](#10-api-rest)
11. [Arquitectura: capas, SOLID y patrones](#11-arquitectura-capas-solid-y-patrones)
12. [Estructura de carpetas y como agregar una app](#12-estructura-de-carpetas-y-como-agregar-una-app)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Descripcion y arquitectura

StockFlow cubre el ciclo completo de una bodega:

- **Catalogo**: productos con categorias, marcas, unidades y estrategia de rotacion (FIFO / FEFO), lotes y caducidad.
- **Almacenes** con ubicaciones tipificadas (recepcion, almacenamiento, despacho, cuarentena).
- **Inventario**: entradas, salidas, transferencias, ajustes, kardex valorizado, alertas (bajo minimo, por vencer, vencido) y conteos ciclicos con aprobacion.
- **Compras** (OC): confirmacion, recepcion parcial/total con lotes y **costo promedio ponderado**.
- **Ventas** (OV): confirmacion, **picking sugerido** (FEFO/FIFO) y despacho parcial/total.
- **Reportes**: dashboard con KPIs y graficos, exportacion CSV / Excel / PDF.
- **Auditoria**: bitacora de altas, cambios (con diff), bajas e inicios/cierres/fallos de sesion.
- **Calidad**: ejecuta Pylint sobre el proyecto, guarda corridas, analiza snippets y explica cada mensaje.

```mermaid
flowchart LR
    U[Navegador<br/>Templates + Bootstrap 5 + HTMX] --> V[Vistas web]
    C[Cliente API<br/>Token / Sesion] --> A[ViewSets DRF /api/v1/]
    V --> S[Services<br/>reglas de negocio]
    A --> S
    V --> Q[Selectors<br/>lecturas]
    A --> Q
    S --> M[(Modelos)] --> PG[(PostgreSQL)]
    Q --> M
    S -. eventos .-> O[Observers<br/>alertas / auditoria]
    S --> P[[Pylint<br/>subproceso]]
```

Detalle completo (capas, patrones, flujos de estado, permisos) en [`docs/arquitectura.md`](docs/arquitectura.md).
Diagramas UML generados con `pyreverse` en [`docs/uml/`](docs/uml/).

## 2. Funcionalidades y roles

| Modulo | URL | Que permite |
|--------|-----|-------------|
| Inicio | `/` | KPIs, acciones rapidas, movimientos recientes, stock bajo minimo |
| Catalogo | `/catalogo/` | Productos, categorias, marcas, unidades |
| Almacenes | `/almacenes/` | Almacenes y ubicaciones |
| Socios | `/socios/` | Proveedores y clientes |
| Inventario | `/inventario/` | Stock, movimientos, entrada/salida/transferencia/ajuste, lotes, alertas, kardex, conteos |
| Compras | `/compras/` | OC: lineas, confirmar, recibir (lote/caducidad), cancelar |
| Ventas | `/ventas/` | OV: lineas, confirmar, picking sugerido, despachar, cancelar |
| Reportes | `/reportes/` | Dashboard, grafico de movimientos, exportar valoracion CSV/XLSX/PDF |
| Auditoria | `/auditoria/` | Bitacora con diff de cambios y accesos |
| Calidad | `/calidad/` | Ejecutar Pylint, historial, detalle de mensajes, analizador de snippets, catalogo |
| Admin | `/admin/` | Django admin con todos los modelos |
| API | `/api/v1/`, `/api/docs/` | REST + Swagger |

**Matriz de roles** (generada desde `apps/accounts/roles.py`):

| Funcion | Administrador | Supervisor | Almacenista | Compras | Ventas | Consulta |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Catalogo (editar) | ✔ | ✔ | — | — | — | — |
| Almacenes (editar) | ✔ | ✔ | — | — | — | — |
| Proveedores | ✔ | ✔ | — | ✔ | — | ✔ |
| Clientes | ✔ | ✔ | — | — | ✔ | ✔ |
| Movimientos de stock | ✔ | ✔ | ✔ | — | — | — |
| Kardex | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Crear conteo | ✔ | ✔ | ✔ | — | — | — |
| Aprobar conteo | ✔ | ✔ | — | — | — | — |
| Crear OC | ✔ | — | — | ✔ | — | — |
| Confirmar OC | ✔ | ✔ | — | ✔ | — | — |
| Recibir OC | ✔ | ✔ | ✔ | — | — | — |
| Crear OV | ✔ | — | — | — | ✔ | — |
| Confirmar OV | ✔ | ✔ | — | — | ✔ | — |
| Despachar OV | ✔ | ✔ | ✔ | — | — | — |
| Reportes | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Auditoria | ✔ | ✔ | — | — | — | — |
| Ver calidad | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Ejecutar Pylint | ✔ | ✔ | — | — | — | — |
| Usuarios | ✔ | — | — | — | — | — |

El rol se asigna en **Usuarios** (o `seed_demo`); `assign_role` sincroniza el `Group` de permisos.
Los menus y botones se ocultan segun permisos y las acciones prohibidas devuelven **403**.

## 3. Requisitos

- Python **3.12+** (probado con 3.13 en Docker y 3.14 local) y [`uv`](https://docs.astral.sh/uv/) (recomendado) o `pip`.
- Acceso a una base **PostgreSQL** (la del proyecto es remota; ver `.env`).
- Opcional: Docker / Docker Compose, Graphviz (`dot`) para UML en PNG/SVG, `make`.

## 4. Configuracion (.env)

```bash
cp .env.example .env     # y edite los valores
```

| Variable | Ejemplo | Descripcion |
|----------|---------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | `dev`, `prod` o `test` |
| `DJANGO_SECRET_KEY` | *(generada)* | `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `True` | Solo en desarrollo |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Obligatorio en prod |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:8000` | Origenes para CSRF |
| `DATABASE_URL` | `postgres://USER:PASSWORD@HOST:PORT/DBNAME` | Conexion principal |
| `TEST_DATABASE_NAME` | `test_logistic` | BD de pruebas cuando se usa Postgres |
| `DB_CONN_MAX_AGE` | `60` | Conexiones persistentes (s) |
| `TIME_ZONE` / `LANGUAGE_CODE` | `America/Guatemala` / `es` | Localizacion |
| `PYLINT_TARGETS` | `apps,config` | Que analiza el modulo Calidad |
| `PYLINT_FAIL_UNDER` | `9.5` | Umbral de `run_pylint` |
| `PYLINT_TIMEOUT` | `180` | Segundos maximos por corrida |
| `PYLINT_SNIPPET_MAX_BYTES` | `20000` | Tamano maximo de snippet |
| `EXPIRY_ALERT_DAYS` | `30` | Dias para alertar lotes por vencer |
| `SEED_DEMO_PASSWORD` | `Cambia-en-produccion-1234` | Contrasena de los usuarios demo |
| `DJANGO_SECURE_SSL_REDIRECT` / `DJANGO_SECURE_COOKIES` / `DJANGO_SECURE_HSTS_SECONDS` | `1` / `1` / `31536000` | Endurecimiento prod (Compose los pone en `0` para probar en `http://localhost`) |
| `TEST_DATABASE_ENGINE` | `postgres` | Hace que `pytest` use `DATABASE_URL` en vez de SQLite |

> `.env` esta en `.gitignore`: nunca versione credenciales reales.
> Si un valor contiene `$`, escapelo como `$$` (Docker Compose interpreta `$NOMBRE` como variable).

## 5. Formas de ejecucion

### a) venv + pip paso a paso

```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
cp .env.example .env                # editar DATABASE_URL y DJANGO_SECRET_KEY
python manage.py migrate
python manage.py seed_demo          # datos demo (solo con DEBUG=True)
python manage.py runserver          # http://localhost:8000
```

### b) uv

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements/dev.txt
python manage.py migrate && python manage.py seed_demo && python manage.py runserver
```

### c) Makefile

```bash
make setup     # .venv + dependencias + .env + pre-commit install
make migrate
make seed
make run
```

Otros targets: `test`, `test-fast`, `cov`, `lint`, `lint-json`, `lint-report`, `uml`, `check`,
`docker-up`, `docker-debug`, `docker-down`, `superuser`.

### d) Windows (PowerShell)

```powershell
pwsh scripts/run.ps1 -Task setup
pwsh scripts/run.ps1 -Task migrate
pwsh scripts/run.ps1 -Task seed
pwsh scripts/run.ps1 -Task run
```

Acepta los mismos nombres de tarea que el Makefile.

### e) Docker

```bash
docker compose up --build          # http://localhost:8000 (gunicorn + WhiteNoise, settings prod)
```

La imagen es multi-stage (`python:3.13-slim`, usuario no root). El entrypoint aplica migraciones
(`DJANGO_MIGRATE=0` para omitirlas). **No hay servicio de BD**: usa `DATABASE_URL` del `.env`.

### f) Docker en modo debug

```bash
docker compose --profile debug up --build web-debug
```

Levanta `runserver` bajo `debugpy` escuchando en el puerto **5678**, con el codigo montado como
volumen y la debug toolbar habilitada. Ver [Debug](#9-debug) para adjuntar el IDE.

## 6. Usuarios demo

`python manage.py seed_demo` (idempotente; se niega a correr con `DEBUG=False` salvo `--force`)
crea estos usuarios, todos con la contrasena definida en `SEED_DEMO_PASSWORD`:

| Usuario | Rol |
|---------|-----|
| `admin` | Administrador (superusuario) |
| `supervisor` | Supervisor |
| `almacenista` | Almacenista |
| `compras` | Compras |
| `ventas` | Ventas |
| `consulta` | Consulta (solo lectura) |

Ademas carga 30 productos (4 con lote/caducidad FEFO), 2 almacenes, proveedores, clientes,
3 OC (recibida, parcial, borrador), 3 OV (despachada, confirmada, borrador), 2 transferencias,
1 ajuste, 1 conteo en progreso, productos bajo minimo y un lote por vencer (alertas activas).
`--with-lint` ejecuta ademas una primera corrida de Pylint.

> Solo para desarrollo. En DEBUG el login muestra la lista de usuarios demo.

## 7. Pylint

### Que es

Pylint es un analizador estatico para Python: sin ejecutar el codigo detecta errores probables,
malas practicas, violaciones de estilo (PEP 8) y *code smells*, y asigna una **nota de 0 a 10**.
Resumen teorico completo en [`plans/Pylint.md`](plans/Pylint.md).

| Letra | Categoria | Ejemplo |
|:-----:|-----------|---------|
| `C` | Convencion (estilo) | `C0103 invalid-name`, `C0114 missing-module-docstring` |
| `R` | Refactor (code smell) | `R0913 too-many-arguments`, `R1731 consider-using-max-builtin` |
| `W` | Warning (posible bug) | `W0611 unused-import`, `W0102 dangerous-default-value` |
| `E` | Error (bug probable) | `E1101 no-member`, `E0602 undefined-variable` |
| `F` | Fatal (no se pudo analizar) | `F0001`, errores de sintaxis |
| `I` | Informativo | `I0011 locally-disabled` |

La nota se calcula como `10 - ((5*E + W + R + C) / sentencias) * 10`. En StockFlow el minimo es
**9.5** (`fail-under`) y la meta, cumplida, es **10.00/10**.

### Comandos

```bash
pylint apps config tests                                # analisis con .pylintrc
pylint apps config --output-format=json2 > reports/pylint.json   # salida para herramientas
pylint apps --fail-under=9.5                            # exit != 0 si la nota es menor
pylint apps --disable=C0114,missing-function-docstring  # desactivar mensajes en una corrida
pylint --generate-rcfile > referencia.pylintrc          # rcfile por defecto, como referencia
pylint --help-msg=invalid-name                          # explicacion de un mensaje
python manage.py run_pylint --fail-under 9.5            # corrida guardada en BD (visible en /calidad/)
python manage.py generate_uml                           # pyreverse → docs/uml/*.mmd
```

Desactivar en linea solo con justificacion en la misma linea:

```python
except Exception as exc:  # pylint: disable=broad-exception-caught  # el runner puede fallar de muchas formas
```

### `.pylintrc` explicado

| Clave | Valor | Por que |
|-------|-------|---------|
| `load-plugins` | `pylint_django` | Entiende modelos, managers y `objects` de Django (evita falsos `no-member`) |
| `django-settings-module` | `config.settings.test` | Settings que usa el plugin para inspeccionar modelos |
| `ignore` | `migrations` | Codigo generado por Django |
| `ignore-paths` | `^apps/quality/snippets/.*$` | Snippets **intencionalmente malos** de la demo |
| `jobs` | `0` | Usa todos los nucleos |
| `py-version` | `3.14` | Version objetivo para las comprobaciones |
| `fail-under` | `9.5` | Nota minima: por debajo, exit code ≠ 0 (CI y pre-commit fallan) |
| `persistent` | `no` | No guarda estadisticas entre corridas |
| `disable` | `too-few-public-methods`, `wildcard-import`, `unused-wildcard-import`, `too-many-ancestors`, `redefined-outer-name`, `unused-argument`, `duplicate-code` | Ruido justificado en el archivo: `Meta`/DTOs/Protocols, `from .base import *` de settings, mixins de Django, fixtures de pytest, campos repetidos por diseno |
| `max-line-length` | `100` | Lineas legibles sin ser tan estrictos como 79 |
| `max-args` / `max-positional-arguments` | `6` | Mas parametros sugiere un DTO |
| `max-attributes` / `max-locals` / `max-returns` / `max-branches` | `10` / `15` / `6` / `12` | Limites de complejidad |
| `good-names` | `i,j,k,pk,id,qs,_,urlpatterns,app_name,register` | Nombres cortos idiomaticos aceptados |
| `output-format` / `reports` / `score` | `colorized` / `no` / `yes` | Salida legible con nota final |

### Como leer la salida

```
apps/x.py:12:0: C0103: Function name "Calcular" doesn't conform to snake_case naming style (invalid-name)
└─ archivo:linea:columna: CODIGO: mensaje (simbolo)
...
Your code has been rated at 9.83/10
```

### Modulo web `/calidad/`

- **Resumen**: nota de la ultima corrida, conteo por categoria y boton *Ejecutar Pylint ahora* (permiso `accounts.run_lint`).
- **Corridas**: historial con nota y C/R/W/E/F; el detalle lista cada mensaje con enlace al catalogo.
- **Analizar snippet**: pega codigo (no se ejecuta; limite de tamano y timeout) o carga una demo.
- **Catalogo**: mensajes frecuentes con explicacion en espanol y ejemplo malo/bueno.

### Demo antes / despues

En `/calidad/analizar/` cargue **Calculos (mala calidad)** y luego **Calculos (calidad corregida)**:

| Snippet | Nota | Mensajes |
|---------|-----:|----------|
| `calculos_malo.py` | ~6.5 | `invalid-name`, `unused-import`, `unused-variable`, `dangerous-default-value`, `broad-exception-caught`, `missing-function-docstring`, `consider-using-max-builtin` |
| `calculos_bueno.py` | 10.00 | — |

El test `@pytest.mark.slow` `test_real_pylint_on_demo_snippets` verifica esta demo con Pylint real.

### Pre-commit, CI y UML

- `pre-commit install` (lo hace `make setup`): `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`,
  `check-toml`, `check-added-large-files` y **pylint** sobre los archivos modificados (con el venv activo).
- CI (`.github/workflows/ci.yml`): Postgres 16 propio → `check` → `makemigrations --check` →
  `pylint apps config tests --fail-under=9.5` → `pytest --cov` (≥ 90 %) → artefactos `htmlcov/` y `reports/pylint.json`.
- UML: `make uml` genera diagramas Mermaid (`.mmd`, visibles en GitHub/VS Code). Con Graphviz:
  `python manage.py generate_uml --format png`.

## 8. Tests y cobertura

```bash
make test              # pytest completo (incluye el test slow con Pylint real)
make test-fast         # pytest -m "not slow"
make cov               # cobertura en terminal + htmlcov/index.html
```

- Por defecto los tests usan **SQLite en memoria** (`config/settings/test.py`) para no tocar la BD remota.
- Con `TEST_DATABASE_ENGINE=postgres` usan `DATABASE_URL` (asi corre la CI con `postgres:16`).
- Cobertura minima configurada: **90 %** (`pyproject.toml`); actual ≈ 94 %.
- Suites destacadas: `tests/test_flows.py` (flujos OC/OV/conteo por rol), `tests/test_api.py`,
  `tests/test_navigation.py` (todas las paginas con los 6 roles, sin 500), `tests/test_seed_demo.py`,
  `tests/test_migrations.py`.

## 9. Debug

**VS Code** (`.vscode/launch.json`): *Django: runserver*, *Pytest: archivo actual*, *Pytest: todo*,
*Pylint: proyecto* y *Docker: attach (5678)* (mapea `${workspaceFolder}` ↔ `/app`).

**PyCharm** (`.idea/runConfigurations/`): *Django runserver*, *Pytest*, *Pylint*. Para Docker use
*Run → Attach to Process* / *Python Debug Server* contra `localhost:5678` con el mismo path mapping.

**Docker**: `make docker-debug` y luego adjunte el depurador al puerto 5678 (el servidor arranca sin
esperar al cliente). Breakpoints en el codigo montado se respetan porque se usa `--noreload`.

**django-debug-toolbar**: activa en `config.settings.dev` para `INTERNAL_IPS` (en Docker se agrega
automaticamente el gateway). Los loggers `apps.*` emiten nivel DEBUG en desarrollo.

## 10. API REST

Base `/api/v1/` · Swagger `/api/docs/` · Esquema OpenAPI `/api/schema/`.

- Autenticacion: sesion o token (`POST /api/v1/auth/token/`).
- Permisos: modelo (`view/add/change`) + permisos por accion; `DELETE` = desactivacion logica.
- Paginacion 20; filtros `?campo=`, `?search=`, `?ordering=`.
- Errores de negocio → **400** `{"detail": "...", "code": "InsufficientStockError"}`.

| Recurso | Acciones extra |
|---------|----------------|
| `categories`, `brands`, `uoms`, `products`, `warehouses`, `locations`, `suppliers`, `customers` | CRUD |
| `lots`, `stock` | solo lectura |
| `movements` | `POST receive/`, `issue/`, `transfer/`, `adjust/`; `GET kardex/?product=` |
| `purchase-orders` | `POST {id}/lines/`, `{id}/confirm/`, `{id}/cancel/`, `{id}/receive/` |
| `sales-orders` | `POST {id}/lines/`, `{id}/confirm/`, `{id}/cancel/`, `{id}/ship/`; `GET {id}/suggest-picking/` |
| `cycle-counts` | `POST {id}/start/`, `{id}/record/`, `{id}/approve/`, `{id}/cancel/` |
| `lint-runs` | `POST run/` |
| `reports/kpis` | `GET` |

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/token/ \
  -d username=almacenista -d password="$SEED_DEMO_PASSWORD" | python -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -H "Authorization: Token $TOKEN" "localhost:8000/api/v1/products/?search=demo"

curl -H "Authorization: Token $TOKEN" -H "Content-Type: application/json" \
  -X POST localhost:8000/api/v1/movements/receive/ \
  -d '{"product": 2, "location": 2, "quantity": "5", "unit_cost": "3.50"}'

# Picking sugerido y despacho de una OV confirmada
curl -H "Authorization: Token $TOKEN" localhost:8000/api/v1/sales-orders/2/suggest-picking/
```

## 11. Arquitectura: capas, SOLID y patrones

Capas: **vistas/ViewSets** (entrada/salida) → **services** (reglas de negocio, transacciones) →
**modelos**; **selectors** para lecturas. El stock solo cambia via `InventoryService`.

| Patron | Archivo |
|--------|---------|
| Command | `apps/inventory/services/commands.py` |
| Facade | `apps/inventory/services/inventory_service.py` |
| Strategy (+ Factory) | `apps/inventory/services/strategies.py` (FIFO/FEFO), `apps/reports/exporters.py` (CSV/XLSX/PDF) |
| State | `apps/core/state.py` + transiciones en `purchasing/sales/inventory` services |
| Observer | `apps/inventory/events.py` + `signals.py`, `apps/audit/signals.py` |
| Registry | `apps/core/menu.py`, `apps/audit/registry.py` |
| Adapter | `apps/quality/runner.py` |
| Template Method | `apps/core/views.py` (`ServiceActionView`), `apps/inventory/views.py` (`_MovementCreateView`) |
| DTO | `ReceiptLineInput`, `ShipLineInput`, `KardexRow`, `TabularData`, `LintResult` |
| Inyeccion de dependencias | `PurchaseService(inventory=...)`, `LintService(runner=..., parser=...)` |

SOLID aplicado y diagramas de estado: [`docs/arquitectura.md`](docs/arquitectura.md).

## 12. Estructura de carpetas y como agregar una app

```
apps/
  core/          infraestructura: modelos abstractos, secuencias, state machine, menu, vistas base, seed_demo
  accounts/      usuarios, roles, setup_roles, assign_role, token API
  catalog/ warehouses/ partners/   maestros
  inventory/     commands, services, estrategias, conteos, alertas, kardex
  purchasing/ sales/               ordenes de compra y venta
  reports/ audit/ quality/         KPIs y exportes, bitacora, modulo Pylint
  <app>/api/     serializers, viewsets y rutas de /api/v1/
config/          settings (base, dev, prod, test), urls, api_urls
templates/ static/                 UI (Bootstrap 5 + HTMX)
tests/           pruebas transversales (flujos, API, navegacion, seed)
docs/            arquitectura y UML
scripts/         run.ps1, entrypoint.sh
plans/           plan, progreso y teoria de Pylint
```

Checklist para una app nueva:

1. `python manage.py startapp <nombre> apps/<nombre>` y `name = "apps.<nombre>"` en `apps.py`.
2. Crear `models.py`, `services.py`, `selectors.py`, `views.py`, `urls.py`, `api/`, `tests/`.
3. Agregar a `INSTALLED_APPS`, `config/urls.py` y `config/api_urls.py`.
4. `python manage.py makemigrations <nombre>` (`tests/test_migrations.py` falla si se olvida).
5. Registrar menu (`MenuRegistry`) y auditoria (`audit.registry.register`) en `ready()`.
6. Agregar permisos al rol en `accounts/roles.py` y correr `python manage.py setup_roles`.
7. `make check`.

## 13. Troubleshooting

| Sintoma | Causa | Solucion |
|---------|-------|----------|
| `permission denied to create database` al correr tests con Postgres | El usuario no tiene `CREATEDB` | Pida al DBA crear `test_logistic` con owner del usuario y ejecute `pytest --reuse-db`, o use SQLite (no defina `TEST_DATABASE_ENGINE`) |
| `relation "..." does not exist` | Migraciones sin aplicar | `python manage.py migrate` |
| `pip install` falla en Python 3.14 | Falta wheel de alguna dependencia | `uv venv --python 3.13 .venv` |
| `generate_uml --format png` falla | Falta Graphviz | `brew install graphviz` / `apt install graphviz`, o use el formato por defecto `mmd` |
| Puerto 8000 ocupado | Otro proceso | `lsof -i :8000` o `runserver 0.0.0.0:8001` |
| Pylint excede el tiempo | Corrida grande | Suba `PYLINT_TIMEOUT` |
| Snippet devuelve nota 0 / `django-settings-module-not-found` | Pylint sin `BASE_DIR` en `PYTHONPATH` | Ya resuelto en `SubprocessPylintRunner`; ejecute desde la raiz del repo |
| Secret key u otra variable "cortada" dentro de Docker | Compose interpreta `$` en `.env` | Escape `$` como `$$` o regenere el valor sin `$` |
| Login no persiste en `http://localhost` con settings prod | Cookies `Secure` sin HTTPS | `DJANGO_SECURE_COOKIES=0` y `DJANGO_SECURE_SSL_REDIRECT=0` (Compose ya lo hace) |
| `seed_demo` se niega a correr | `DEBUG=False` | Use `--force` solo si realmente lo necesita |
| `pre-commit` falla en pylint | Mensajes nuevos o venv no activo | Corrija el codigo o active `.venv` antes de commitear |

> Seguridad: la contrasena de la BD del proyecto se compartio en texto plano; **rotela** tras la
> entrega y use un usuario con privilegios minimos.
