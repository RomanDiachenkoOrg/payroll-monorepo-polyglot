.PHONY: up down reset logs ps test test-api test-reports test-notifier test-web lint

up:
	docker compose up --build -d
	@echo "Web: http://localhost:8080  API docs: http://localhost:8000/api/docs  Reports: http://localhost:8081/reports/health"

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build -d

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test: test-api test-reports test-notifier test-web

test-api:
	cd services/api && python -m pytest

test-reports:
	cd services/reports && go test ./...

test-notifier:
	cd services/notifier && npm test

test-web:
	cd web && npm test
