"""
AlphaBot FastAPI 메인 애플리케이션
앱 초기화, 라우터 등록
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import backtest, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 라이프사이클 핸들러
    - 시작: DB 테이블 초기화
    """
    await init_db()
    print("AlphaBot 서버 시작 - DB 초기화 완료")
    yield
    print("AlphaBot 서버 종료")


# FastAPI 앱 인스턴스
app = FastAPI(
    title="AlphaBot API",
    description="주식 전략 백테스팅 + AI 시뮬레이터 - 수익률/MDD/샤프지수 분석",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])


@app.get("/", tags=["health"])
async def root():
    """헬스체크 엔드포인트"""
    return {"service": "AlphaBot", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok"}
