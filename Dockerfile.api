# API 서버 Docker 이미지

FROM python:3.13-slim

WORKDIR /app

# 프로젝트 파일 복사
COPY requirements.txt ./
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# API 서버 실행 (마이그레이션은 컨테이너 시작 시 실행)
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
