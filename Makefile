dev:
	docker compose up --build

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.seed

schema-status:
	docker compose run --rm backend python -m app.cli schema-status

session-cleanup:
	docker compose run --rm backend python -m app.cli session-cleanup

test:
	cd backend && pytest
	cd frontend && npm run build

lint:
	cd backend && python -m compileall app

test-backup-restore:
	@test -n "$(SOURCE_DATABASE_URL)" || (echo "SOURCE_DATABASE_URL is required" && exit 1)
	@test -n "$(TARGET_DATABASE_URL)" || (echo "TARGET_DATABASE_URL is required" && exit 1)
	SOURCE_DATABASE_URL="$(SOURCE_DATABASE_URL)" TARGET_DATABASE_URL="$(TARGET_DATABASE_URL)" sh scripts/validate_test_backup_restore.sh
