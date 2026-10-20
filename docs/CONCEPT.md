# Concept & Outlook: from single script to a Docker microservices application

## 1. Where we are

The task solution is one container with one codebase: seed → convert → store, triggered by HTTP.
That is fine for a demo, but a single script with single execution does not scale, cannot be
retried, and mixes responsibilities. The code is already split into layers (routes / services /
models) so it can be pulled apart without a rewrite.

## 2. Target architecture

```
           ┌──────────┐      HTTP       ┌─────────────┐
 client ──▶│ API      │────────────────▶│ PostgreSQL  │
           │ gateway  │                 │ (per-service│
           └────┬─────┘                 │  schemas)   │
                │ publish job           └──────▲──────┘
                ▼                              │
           ┌──────────┐   consume   ┌──────────┴──────┐
           │ RabbitMQ │────────────▶│ converter worker│ (scales 1..N)
           │ / Redis  │             └─────────────────┘
           └──────────┘
                ▲
           ┌────┴──────┐
           │ generator │  (scheduled / on demand)
           └───────────┘
```

| Service | Responsibility | Scales by |
|---|---|---|
| `api` (FastAPI) | public REST API, validation, auth, reads results | replicas behind a reverse proxy (nginx / Traefik) |
| `generator` | produces source numbers (or ingests them from files/other systems) | rarely; scheduled job |
| `converter-worker` | takes a job from the queue, converts number → text, writes result | number of workers |
| `db` (Postgres) | persistent storage | managed DB / replicas later |
| `broker` (RabbitMQ or Redis) | decouples producers from workers, retries, dead-letter queue | managed broker |
| `scheduler` (optional) | triggers periodic runs (cron-like) | single instance |

Why a queue: instead of "run the script once", the API publishes "convert number X" messages.
Workers process them in parallel, failed messages are retried or moved to a dead-letter queue,
and nothing is lost if a worker restarts.

**Broker choice.** Start with **RabbitMQ**: acknowledgements, retries and dead-letter queues are
built in, which is exactly what the converter worker needs. Redis (Streams or a task library such as
RQ/Celery) is the lighter alternative if the setup should stay minimal; the `JobPublisher` /
`JobConsumer` wrappers (section 3) hide the broker, so switching later touches only those two classes.

### Example: target `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    environment: { POSTGRES_USER: app, POSTGRES_PASSWORD: app, POSTGRES_DB: numbers_db }
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U app"], interval: 3s, retries: 10 }

  broker:
    image: rabbitmq:3-management-alpine
    healthcheck: { test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"], interval: 5s, retries: 10 }

  api:                      # publishes jobs, serves results
    build: ./services/api
    ports: ["8000:8000"]
    depends_on: { db: { condition: service_healthy }, broker: { condition: service_healthy } }

  converter-worker:         # consumes jobs, writes table 2; scale with --scale converter-worker=N
    build: ./services/converter
    depends_on: { db: { condition: service_healthy }, broker: { condition: service_healthy } }

  generator:                # creates source numbers on a schedule / on demand
    build: ./services/generator
    depends_on: { broker: { condition: service_healthy } }

volumes:
  pgdata:
```

## 3. Code structure (per service)

```
services/<name>/
  app/
    api/            routers (HTTP only, no business logic)
    domain/         entities + pure logic (e.g. NumberToTextConverter)
    services/       use-cases (ConvertNumberUseCase, SeedNumbersUseCase)
    repositories/   DB access behind interfaces (NumberRepository, WordRepository)
    messaging/      publisher / consumer wrappers
    config.py       pydantic-settings
  tests/
  Dockerfile
```

Key classes:

- `NumberToTextConverter` (strategy interface) with `EnglishConverter`, `GermanConverter`, ...
  → new languages without touching the rest.
- `NumberRepository`, `WordRepository`: SQLAlchemy implementations, in-memory fakes for tests.
- `ConvertNumberUseCase`: orchestrates repository + converter, idempotent.
- `JobPublisher` / `JobConsumer`: the only code that knows about the broker.

Shared code (schemas, message contracts) goes into a small internal package, versioned
and installed into each service image.

## 4. Data & contracts

- Each service owns its tables (database-per-service as a goal; one Postgres instance with separate
  schemas is a pragmatic first step).
- Messages are versioned JSON, e.g. `{"version": 1, "number_id": 12, "value": 7}`.
- Migrations with Alembic instead of `create_all`.
- Idempotency key = `number_id` (already `UNIQUE` in table 2).

## 5. Cross-cutting concerns

- **Config & secrets:** environment variables, `.env` locally, Docker/K8s secrets in production.
- **Observability:** structured JSON logs, `/health` + `/ready` endpoints, Prometheus metrics, tracing (OpenTelemetry) with a correlation id passed through messages.
- **Resilience:** retries with backoff, dead-letter queue, timeouts, graceful shutdown of workers.
- **Security:** auth at the gateway (JWT/API keys), least-privilege DB users, non-root containers, dependency scanning.
- **Testing:** unit tests (domain, use-cases), integration tests with `docker compose` + testcontainers, contract tests for messages.

## 6. Delivery

- One repo (monorepo) with `services/*`, one `docker-compose.yml` for local dev, one for CI.
- CI pipeline: lint (ruff) → tests → build images → scan → push to registry.
- Deployment: Docker Compose on a single host first, then Kubernetes / ECS when scale requires it.

## 7. Migration roadmap

1. **Now:** single FastAPI container + Postgres (this solution).
2. Extract `converter` logic into a worker and put a broker in between; API only enqueues.
3. Add Alembic migrations, repository layer and use-case classes.
4. Add generator/scheduler service and observability.
5. Split data ownership per service, add gateway/auth, move to orchestration (K8s).

Each step keeps the system working, so there is no big-bang rewrite.
