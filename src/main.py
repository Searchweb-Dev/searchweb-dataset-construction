"""FastAPI 메인 앱."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import folders, saved_links, tags, links
from src.db.models.base import Base
from src.db.session import engine

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SearchWeb API", version="0.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(folders.router)
app.include_router(saved_links.router)
app.include_router(tags.router)
app.include_router(links.router)


@app.get("/health")
def health_check():
    """헬스 체크."""
    return {"status": "ok"}
