FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    PORT=10000 \
    PYTHONPATH=/app/backend
WORKDIR /app

COPY backend/requirements-lock.txt backend/requirements-deploy.txt ./backend/
RUN pip install -r backend/requirements-deploy.txt
COPY ml/ ./ml/
# Training happens once during the build; startup only loads the saved model.
RUN python -m ml.src.download && python -m ml.src.train && rm -rf ml/data
COPY backend/ ./backend/
COPY knowledge_base/ ./knowledge_base/
COPY --from=frontend /build/dist ./frontend/dist

RUN useradd --create-home --uid 10001 factorymind \
    && mkdir -p /app/backend/instance \
    && chown factorymind:factorymind /app/backend/instance
USER factorymind
EXPOSE 10000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 180 --access-logfile - --error-logfile - 'app:create_app()'"]
