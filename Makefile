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

backend-fast:
	python scripts/run_test_gate.py fast

backend-integration:
	python scripts/run_test_gate.py integration

backend-full:
	python scripts/run_test_gate.py full

frontend-test:
	cd frontend && npm run typecheck && npm test -- --run

e2e-smoke:
	cd frontend && npm run e2e

e2e-full:
	cd frontend && npm run e2e:db

lint:
	cd backend && python -m compileall app

test-backup-restore:
	@test -n "$(SOURCE_DATABASE_URL)" || (echo "SOURCE_DATABASE_URL is required" && exit 1)
	@test -n "$(TARGET_DATABASE_URL)" || (echo "TARGET_DATABASE_URL is required" && exit 1)
	SOURCE_DATABASE_URL="$(SOURCE_DATABASE_URL)" TARGET_DATABASE_URL="$(TARGET_DATABASE_URL)" sh scripts/validate_test_backup_restore.sh

recovery:
	@test -n "$(RECOVERY_ADMIN_DATABASE_URL)" || (echo "RECOVERY_ADMIN_DATABASE_URL is required" && exit 1)
	docker build -f backend/Dockerfile.recovery -t astra-recovery-local .
	docker run --rm --network host -e RECOVERY_ADMIN_DATABASE_URL -e ASTRA_APPLICATION_COMMIT astra-recovery-local scripts/run_recovery_integration.py
