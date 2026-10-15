# One image, two roles (web + worker), selected by the command in docker-compose.yml.
# Rails equivalent: your app Dockerfile; same image runs `puma` and `sidekiq`.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so Docker caches this layer
# (Rails equivalent: COPY Gemfile* then `bundle install`).
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000

# Default command = web server. Gunicorn is the WSGI server (Puma's role).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]
