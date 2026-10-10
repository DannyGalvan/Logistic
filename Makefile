.PHONY: setup migrate seed run test test-fast cov lint lint-json lint-report uml check \
        docker-up docker-debug docker-down superuser

PYTHON ?= .venv/bin/python

setup:  ## Crea .venv, instala dependencias, copia .env y activa pre-commit
	uv venv --python 3.14 --clear .venv
	VIRTUAL_ENV=$$(pwd)/.venv uv pip install -r requirements/dev.txt
	test -f .env || cp .env.example .env
	$(PYTHON) -m pre_commit install
	$(PYTHON) manage.py check

migrate:
	$(PYTHON) manage.py migrate

seed:
	$(PYTHON) manage.py seed_demo

run:
	$(PYTHON) manage.py runserver 0.0.0.0:8000

test:
	$(PYTHON) -m pytest

test-fast:
	$(PYTHON) -m pytest -m "not slow"

cov:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=html

lint:
	$(PYTHON) -m pylint apps config tests

lint-json:
	mkdir -p reports
	-$(PYTHON) -m pylint apps config --output-format=json2 > reports/pylint.json

lint-report:
	$(PYTHON) manage.py run_pylint

uml:
	$(PYTHON) manage.py generate_uml

check:
	$(PYTHON) manage.py check
	$(PYTHON) manage.py makemigrations --check --dry-run
	$(PYTHON) -m pylint apps config tests
	$(PYTHON) -m pytest

docker-up:
	docker compose up --build

docker-debug:
	docker compose --profile debug up --build web-debug

docker-down:
	docker compose --profile debug down

superuser:
	$(PYTHON) manage.py createsuperuser
