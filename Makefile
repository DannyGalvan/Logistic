.PHONY: setup migrate seed run test test-fast cov lint lint-json lint-report check superuser

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

setup:
	uv venv --python 3.14 --clear .venv
	VIRTUAL_ENV=$$(pwd)/.venv uv pip install -r requirements/dev.txt
	test -f .env || cp .env.example .env
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
	$(PYTHON) -m pylint apps config --output-format=json2 > reports/pylint.json

lint-report:
	$(PYTHON) manage.py run_pylint

check:
	$(PYTHON) manage.py check
	$(PYTHON) manage.py makemigrations --check --dry-run
	$(PYTHON) -m pylint apps config tests
	$(PYTHON) -m pytest

superuser:
	$(PYTHON) manage.py createsuperuser