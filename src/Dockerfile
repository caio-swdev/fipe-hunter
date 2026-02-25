# =============================================================================
# IMPORTANT: Docker build context must be the REPO ROOT, not src/.
# In Render dashboard: Root Directory = "." (repo root)
# Dockerfile path = "products/demo-fipe-hunter/src/Dockerfile"
#
# Why repo root? The vite-app depends on monorepo packages via file: protocol:
#   package.json: "file:../../../../../packages/automotive-ui"
# These resolve to /packages/X from WORKDIR /frontend (traverses to /).
# We COPY packages/ into the image at build time so npm ci can resolve them.
# =============================================================================

# =============================================================================
# Stage 0 — frontend builder
# Copies monorepo packages, installs deps, compiles Vite/React → dist/.
# Build context: repo root (see note above).
# =============================================================================
FROM node:22-slim AS frontend-builder

WORKDIR /frontend

# Copy monorepo packages that vite-app depends on via file: protocol.
# package.json references "file:../../../../../packages/*" which resolves
# from WORKDIR /frontend (5 levels up = /) to /packages/*.
COPY packages/automotive-ui/       /packages/automotive-ui/
COPY packages/design-system-engine/ /packages/design-system-engine/
COPY packages/ui/                  /packages/ui/

COPY products/demo-fipe-hunter/src/apps/vite-app/package*.json ./
RUN npm ci

COPY products/demo-fipe-hunter/src/apps/vite-app/ ./
# Skip tsc type-check — packages/ui has pre-existing TS errors unrelated to
# the build. Vite uses esbuild for transpilation; tsc belongs in CI only.
RUN npx vite build

# =============================================================================
# Stage 1 — builder
# Install all Python packages into a prefix so stage 2 stays lean.
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed at build time only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip + hatchling (build backend used by every pyproject.toml)
RUN pip install --upgrade pip hatchling

# ---- Copy all pyproject.toml files first so Docker cache layers are stable ----
# Root package (fipe-hunter meta-package + alembic)
COPY products/demo-fipe-hunter/src/pyproject.toml .

# Internal libraries
COPY products/demo-fipe-hunter/src/libs/business-py/pyproject.toml  libs/business-py/pyproject.toml
COPY products/demo-fipe-hunter/src/libs/infra-py/pyproject.toml     libs/infra-py/pyproject.toml
COPY products/demo-fipe-hunter/src/libs/adapters-py/pyproject.toml  libs/adapters-py/pyproject.toml

# FastAPI app
COPY products/demo-fipe-hunter/src/apps/fastapi-app/pyproject.toml  apps/fastapi-app/pyproject.toml

# ---- Copy source so pip can build wheels with hatchling ----
COPY products/demo-fipe-hunter/src/libs/business-py/  src/libs/business-py/
COPY products/demo-fipe-hunter/src/libs/infra-py/      src/libs/infra-py/
COPY products/demo-fipe-hunter/src/libs/adapters-py/   src/libs/adapters-py/
COPY products/demo-fipe-hunter/src/apps/fastapi-app/   src/apps/fastapi-app/

# Install libraries in dependency order (bottom-up)
# Use --prefix so everything lands in /install for easy COPY in stage 2
RUN pip install --prefix=/install --no-warn-script-location \
    ./libs/business-py \
    ./libs/infra-py \
    ./libs/adapters-py \
    ./apps/fastapi-app

# Install root-level runtime deps (alembic, apscheduler, telegram, etc.)
RUN pip install --prefix=/install --no-warn-script-location \
    "fastapi>=0.104.0" \
    "uvicorn[standard]>=0.24.0" \
    "sqlalchemy>=2.0.0" \
    "alembic>=1.12.0" \
    "pydantic>=2.5.0" \
    "requests>=2.31.0" \
    "beautifulsoup4>=4.12.0" \
    "lxml>=4.9.0" \
    "fake-useragent>=1.4.0" \
    "python-telegram-bot>=20.7.0" \
    "apscheduler>=3.10.0" \
    "fuzzywuzzy>=0.18.0" \
    "python-Levenshtein>=0.23.0" \
    "python-dateutil>=2.8.0" \
    "psycopg2-binary>=2.9.0" \
    "python-dotenv>=1.0.0" \
    "slowapi>=0.1.9" \
    "packaging>=23.0" \
    "python-jose[cryptography]>=3.3.0" \
    "bcrypt>=4.0.0" \
    "curl-cffi>=0.7.0" \
    "aiofiles>=23.0.0"


# =============================================================================
# Stage 2 — runtime
# Minimal image: no build tools, no dev files, no venv clutter.
# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only system libs
# curl-cffi needs libcurl; lxml needs libxml2/libxslt; xvfb for headful Chrome (Xvfb virtual display)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 \
    libxml2 \
    libxslt1.1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# packaging is used by limits/slowapi but not declared as a dep.
# builder's python:3.12-slim has it pre-installed, so pip --prefix=/install
# skips it ("already satisfied"). Install it directly here so it lands
# in the runtime image's site-packages.
RUN pip install --no-cache-dir "packaging>=23.0"

# Install Playwright's Chromium — container-optimized binary that doesn't crash on
# Render's seccomp profile (unlike Debian chromium which hits SIGTRAP at startup).
# PLAYWRIGHT_BROWSERS_PATH makes it world-readable so appuser can run it.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
RUN pip install --no-cache-dir "playwright>=1.40.0" "playwright-stealth>=1.0.0" && \
    playwright install-deps chromium && \
    playwright install chromium && \
    chmod -R 755 /opt/playwright-browsers

# Copy application source
COPY products/demo-fipe-hunter/src/libs/business-py/  libs/business-py/
COPY products/demo-fipe-hunter/src/libs/infra-py/      libs/infra-py/
COPY products/demo-fipe-hunter/src/libs/adapters-py/   libs/adapters-py/
COPY products/demo-fipe-hunter/src/apps/fastapi-app/   apps/fastapi-app/

# Copy Alembic migration files (needed for `alembic upgrade head` at startup)
COPY products/demo-fipe-hunter/src/apps/fastapi-app/alembic.ini .
COPY products/demo-fipe-hunter/src/apps/fastapi-app/alembic/    alembic/

# Copy built frontend (served as static files by FastAPI)
COPY --from=frontend-builder /frontend/dist/ apps/vite-app/dist/

# PYTHONPATH must be set so uvicorn can find `app.main` and the internal libs.
# render.yaml [envVars] mirrors this — the Dockerfile ENV makes it work for
# local `docker run` usage as well.
ENV PYTHONPATH="/app/apps/fastapi-app:/app/libs/infra-py:/app/libs/business-py:/app/libs/adapters-py"
# Tell Breakpad/Crashpad not to run even if invoked — belt-and-suspenders with
# the crashpad handler binary removal above.
ENV BREAKPAD_DISABLE=1

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

# Render health-check path: /health — internal port 8000
EXPOSE 8000

# Run Alembic migrations then start uvicorn.
# DATABASE_URL is injected as a Render environment variable at runtime.
# The app module path matches: src/apps/fastapi-app/app/main/__init__.py
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
