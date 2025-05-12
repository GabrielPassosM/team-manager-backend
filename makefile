SHELL := /bin/bash

current_dir = $(shell pwd)

services-up:
	docker compose -f infra/compose.yaml up -d

services-down:
	docker compose -f infra/compose.yaml down

services-stop:
	docker compose -f infra/compose.yaml stop

services-logs:
	docker compose -f infra/compose.yaml logs -f

wait-for-pg:
	python3 infra/scripts/wait_for_pg.py

run-migrations: services-up wait-for-pg
	alembic -c infra/alembic.ini upgrade head

populate-dev-db:
	python -m infra.scripts.populate_dev_db

run-project: run-migrations populate-dev-db
	fastapi dev ./api/main.py

run-tests:
	pytest ./tests

reset-docker:
	docker rm -v -f postgres-dev
	docker compose -f infra/compose.yaml up
