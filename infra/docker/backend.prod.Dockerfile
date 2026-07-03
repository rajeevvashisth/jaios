# Production image: no editable install, no dev/test/lint extras, runs as
# a non-root user with a fixed worker count instead of --reload. The local
# dev Dockerfile (backend.Dockerfile) stays separate and unchanged — this
# one is what ECS/Cloud Run/etc. actually pull.

FROM python:3.12-slim AS builder

WORKDIR /build
COPY backend/ ./
RUN pip install --no-cache-dir --user .

FROM python:3.12-slim AS runtime

# git is kept for the Developer/DevOps agents' GitTool; there is no docker/gh
# CLI in this image — DockerTool/GitHubTool are unavailable in this
# deployment target unless the image is extended to add them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser backend/ ./

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
