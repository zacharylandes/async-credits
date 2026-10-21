# Async Credit Processing Service

Python 3.12 service that accepts credit requests asynchronously: FastAPI validates and registers a credit, Celery publishes work over RabbitMQ, and a worker applies the amount to a MongoDB user balance.

## Prerequisites

- Docker and Docker Compose

## Run

```bash
make up
```

API listens on `http://localhost:8000`. Interactive OpenAPI docs: `http://localhost:8000/docs`.

## Example

```bash
curl -sS -X POST http://localhost:8000/credits \
  -H 'content-type: application/json' \
  -d '{"user_id":"alice","amount":"10.00"}'

curl -sS http://localhost:8000/credits/<task_id>
```

Peek at stored documents:

```bash
docker compose exec mongo mongosh --eval 'db.getSiblingDB("credits").credits.find().toArray()'
docker compose exec mongo mongosh --eval 'db.getSiblingDB("credits").users.find().toArray()'
```

## Tests

With the stack up:

```bash
make test
```

## Design

See [docs/design.md](docs/design.md) (and `docs/design.pdf`) for architecture, claim/idempotency, and failure semantics.

## Not included

- Outbox / client idempotency keys
- Celery result backend (status lives in MongoDB)
- Auth, rate limiting, multi-region deployment
