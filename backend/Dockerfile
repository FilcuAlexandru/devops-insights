FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local
COPY alembic.ini ./
COPY migrations ./migrations

# OpenShift starts containers with a random UID that always belongs to group 0,
# so everything the application touches must be group-writable.
RUN useradd --uid 1001 --gid 0 --no-create-home --shell /usr/sbin/nologin appuser \
    && chgrp -R 0 /app \
    && chmod -R g=u /app

USER 1001

EXPOSE 8000

CMD ["uvicorn", "devops_insights.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
