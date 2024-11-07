# Builder stage
FROM python:3.11-slim-buster AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry

RUN groupadd -g 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos '' appuser

USER appuser

WORKDIR /home/appuser/app

COPY --chown=appuser:appgroup pyproject.toml poetry.lock ./
COPY --chown=appuser:appgroup {{ project-identifier }} ./{{ project-identifier }}

RUN touch README.md
RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

# Runner stage
FROM python:3.11-slim-buster AS runner


RUN groupadd -g 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos '' appuser

USER appuser

WORKDIR /home/appuser/app

# Copy only necessary files
COPY --from=builder --chown=appuser:appgroup /home/appuser/app/.venv ./.venv
COPY --from=builder --chown=appuser:appgroup /home/appuser/app/{{ project-identifier }} ./{{ project-identifier }}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/home/appuser/app/.venv \
    PATH="/home/appuser/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    LISTEN_PORT=8000

EXPOSE 8000

WORKDIR /home/appuser/app/{{ project-identifier }}

RUN chmod +x ./run.sh

CMD ["./run.sh"]