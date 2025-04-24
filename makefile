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

run-project: run-migrations
	fastapi dev ./api/main.py

run-tests: services-up wait-for-pg
	pytest ./tests
	make services-down
