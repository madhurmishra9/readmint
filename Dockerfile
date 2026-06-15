# ---------- frontend build ----------
FROM node:20-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build   # emits /build/dist

# ---------- backend runtime ----------
FROM python:3.12-slim AS runtime

# WeasyPrint native deps (PDF export). Drop this block to slim the image if PDF
# export is not needed — the endpoint degrades to 501 without them.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
        libffi8 shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app/backend

# Honour corporate pip mirror / TLS during build.
COPY backend/pip.conf /etc/pip.conf
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY cli/ /app/cli/
COPY --from=frontend /build/dist /app/frontend/dist

# Non-root.
RUN useradd -m -u 10001 readmint && chown -R readmint:readmint /app
USER readmint

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:8080/healthz').status_code==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
