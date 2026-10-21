.PHONY: up test down

up:
	docker compose up -d --build

test:
	docker compose run --rm -e MONGO_DB=credits_test api pytest

down:
	docker compose down -v
