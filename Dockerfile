# API 서버 Docker 이미지

FROM python:3.13-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# 의존성 설치
RUN uv sync --no-dev

# 마이그레이션 실행
RUN uv run alembic upgrade head

# API 서버 실행
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
