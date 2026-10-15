# Pizza Orders API

A small containerised Flask service for pizza shops: shops, menu items, orders, and a background job that confirms each order. It's a practice project, written to show how I structure a Python backend coming from ten years of professional Ruby on Rails.

**Stack:** Python 3.12 · Flask 3 · SQLAlchemy 2.0 (Flask-SQLAlchemy) · Alembic (Flask-Migrate) · PostgreSQL 16 · Redis + RQ (background jobs) · pydantic v2 (validation) · gunicorn · pytest · Docker Compose

## What it demonstrates

- Application factory with per-environment config, blueprints, and centralised error handlers
- A service layer (`app/services/`) that keeps business rules out of the route functions and testable without HTTP
- SQLAlchemy 2.0 style models and queries (`Mapped`, `select()`), with Alembic migrations
- Request validation at the edge with pydantic, returning structured 422 responses
- Background processing with RQ and Redis: jobs are enqueued after commit, run in their own app context, and are idempotent
- Tests with pytest, fixtures, an in-memory database and fake Redis
- A Docker Compose setup with separate web, worker, database and Redis containers
- A `flask shell` context that pre-imports `db`, the models, `select` and `func`

## Run it

```bash
cp .env.example .env
docker compose up --build
docker compose exec web flask --app wsgi db upgrade      # run migrations
curl localhost:8000/health

# Create a shop, add menu items, place an order
curl -X POST localhost:8000/shops -H 'Content-Type: application/json' \
  -d '{"name":"Tony'\''s Slice","city":"Belfast"}'
curl -X POST localhost:8000/shops/1/menu -H 'Content-Type: application/json' \
  -d '{"name":"Margherita","price_pence":1000}'
curl -X POST localhost:8000/shops/1/orders -H 'Content-Type: application/json' \
  -d '{"customer_email":"sam@example.com","items":[{"menu_item_id":1,"quantity":2}]}'
curl localhost:8000/orders/1        # status flips pending -> confirmed once the worker runs
```

Run the tests (SQLite in memory + fake Redis):

```bash
docker compose run --rm web pytest
```

Open a console with the app and models loaded:

```bash
docker compose exec web flask --app wsgi shell
```

## Layout

```
wsgi.py                  entry point gunicorn imports
app/__init__.py          create_app(): config, extensions, blueprints, error handlers
app/config.py            per-environment config classes, selected by APP_ENV
app/extensions.py        db and migrate objects
app/models.py            SQLAlchemy models
app/schemas.py           pydantic request validation
app/routes/*.py          blueprints: HTTP in, HTTP out
app/services/*.py        business logic (order creation, pricing, enqueueing)
app/jobs.py, queue.py    background jobs on RQ
migrations/              Alembic migrations
tests/                   pytest
Dockerfile               one image, run as web or worker
docker-compose.yml       web, worker, db, redis
```

## Request flow

`POST /shops/1/orders` goes through gunicorn to `wsgi:app`. Flask matches the blueprint route, and the route validates the body with `OrderCreate.model_validate(...)` (422 on bad input). It then calls the order service, which loads the menu items in one query, snapshots prices, computes the total and commits. After the commit it enqueues `send_order_confirmation` in Redis. A separate worker process picks the job up, opens its own app context, loads the order and marks it `confirmed`. The route returns 201.

## Coming from Rails: how it maps

| Rails | Flask / Python |
|---|---|
| `Gemfile` / `bundle install` | `requirements.txt` / `pip install -r` |
| `rails s` / Puma | `flask run` (dev) / gunicorn (prod), WSGI instead of Rack |
| `config.ru` | `wsgi.py` |
| `config/environments/*.rb`, `database.yml`, ENV | `app/config.py` classes + env vars (`APP_ENV`, `DATABASE_URL`) |
| `config/routes.rb` | blueprints registered in `create_app()` |
| Controller action | route function (`@bp.post(...)`) |
| Service object | module in `app/services/` |
| `params.require().permit()` | pydantic model: `OrderCreate.model_validate(...)` |
| ActiveRecord model | SQLAlchemy model (`Mapped[...]` columns) |
| `rails g migration` / `db:migrate` | `flask db migrate` / `flask db upgrade` |
| `rescue_from` | `@app.errorhandler(...)` |
| Sidekiq / ActiveJob | RQ (`queue.enqueue(fn, arg)`); Celery is the larger alternative |
| `rails console` | `flask --app wsgi shell` |
| RSpec / FactoryBot | pytest / fixtures (`tests/conftest.py`) |
| RuboCop | ruff (not configured here) |

### Differences worth knowing

1. **Nothing autoloads.** Routes, models and extensions must be imported and registered. Forget `from . import models` and Alembic sees no tables.
2. **App context is explicit.** A Flask worker has no app until you create one, which is why `app/jobs.py` opens one.
3. **The session is explicit.** You call `db.session.add(...)` and `db.session.commit()` yourself. There's no autosave.
4. **Validation lives outside the model.** Pydantic validates input at the edge, and models are mainly column definitions.
5. **Relationships lazy-load by default.** It's easy to introduce N+1 queries, so use `selectinload` / `joinedload` (Rails `includes`) where needed.
6. **Migrations are generated from model diffs and need review** before applying.

## Design choices and what I'd add next

- Status is a string column rather than a database enum, to keep migrations simple.
- Money is stored as integer pence to avoid rounding errors.
- Tests use SQLite in memory for speed. A real project should also run them against Postgres in CI, since SQLite hides some differences.
- Not included yet: authentication, pagination, rate limiting, structured logging, and a CI pipeline with ruff and mypy. These are the next things I would add.
