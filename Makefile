.PHONY: up down run migrate lint test

up:
	docker compose up -d postgres redis minio

down:
	docker compose down

run:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "$(name)"

lint:
	ruff check . && mypy app

test:
	pytest -v --cov=app --cov-report=term-missing

worker:
	celery -A app.workers.celery_app worker --loglevel=info
