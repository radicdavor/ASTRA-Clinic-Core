dev:
	docker compose up --build

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.seed

test:
	cd backend && pytest
	cd frontend && npm run build

lint:
	cd backend && python -m compileall app
