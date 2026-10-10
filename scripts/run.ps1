# Equivalente Windows del Makefile. Uso:
#   pwsh scripts/run.ps1 -Task setup
#   pwsh scripts/run.ps1 -Task run
#   pwsh scripts/run.ps1 -Task test
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        'setup', 'migrate', 'seed', 'run', 'test', 'test-fast',
        'cov', 'lint', 'lint-json', 'lint-report', 'uml', 'check',
        'docker-up', 'docker-debug', 'docker-down', 'superuser'
    )]
    [string]$Task
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

$python = Join-Path '.venv' -ChildPath 'Scripts/python.exe'
if (-not (Test-Path $python)) { $python = 'python' }

switch ($Task) {
    'setup' {
        uv venv --python 3.14 --clear .venv
        $env:VIRTUAL_ENV = (Resolve-Path .venv).Path
        uv pip install -r requirements/dev.txt
        if (-not (Test-Path .env)) { Copy-Item .env.example .env }
        & $python -m pre_commit install
        & $python manage.py check
    }
    'migrate'   { & $python manage.py migrate }
    'seed'      { & $python manage.py seed_demo }
    'run'       { & $python manage.py runserver 0.0.0.0:8000 }
    'test'      { & $python -m pytest }
    'test-fast' { & $python -m pytest -m 'not slow' }
    'cov'       { & $python -m pytest --cov --cov-report=term-missing --cov-report=html }
    'lint'      { & $python -m pylint apps config tests }
    'lint-json' {
        New-Item -ItemType Directory -Force reports | Out-Null
        & $python -m pylint apps config --output-format=json2 | Out-File -Encoding utf8 reports/pylint.json
    }
    'lint-report' { & $python manage.py run_pylint }
    'check' {
        & $python manage.py check
        & $python manage.py makemigrations --check --dry-run
        & $python -m pylint apps config tests
        & $python -m pytest
    }
    'uml'          { & $python manage.py generate_uml }
    'docker-up'    { docker compose up --build }
    'docker-debug' { docker compose --profile debug up --build web-debug }
    'docker-down'  { docker compose --profile debug down }
    'superuser'    { & $python manage.py createsuperuser }
}
