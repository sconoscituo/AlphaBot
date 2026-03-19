"""
백테스팅 라우터
백테스트 실행, 결과 조회, 전략 저장/조회 엔드포인트
"""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.user import User
from app.models.strategy import Strategy
from app.models.backtest import BacktestResult
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResultResponse,
    BacktestListResponse,
    StrategyCreate,
    StrategyResponse,
)
from app.utils.auth import get_current_active_user
from app.services.data_loader import load_ohlcv, validate_date_range
from app.services.backtester import run_backtest
from app.services.strategies.ma_cross import MACrossStrategy
from app.services.strategies.rsi import RSIStrategy
from app.services.strategies.ai_strategy import generate_ai_strategy

router = APIRouter()


async def _execute_backtest(
    req: BacktestRequest,
    user: User,
) -> dict:
    """
    내부 백테스트 실행 헬퍼
    1) 날짜 범위 검증
    2) 주가 데이터 로드
    3) 전략 시그널 생성
    4) 백테스트 실행
    5) 결과 반환
    """
    # 날짜 범위 검증 (플랜에 따라 조정)
    try:
        start_date, end_date = validate_date_range(
            req.start_date, req.end_date, user.is_premium
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 주가 데이터 로드
    try:
        df = await load_ohlcv(req.ticker, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"주가 데이터 로드 실패: {e}")

    params = req.params or {}
    strategy_type = req.strategy.lower()
    ai_reason = None

    # 전략별 시그널 생성
    if strategy_type == "ma_cross":
        try:
            strategy = MACrossStrategy(params)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        df_signals = strategy.generate_signals(df)
        used_params = strategy.get_params()

    elif strategy_type == "rsi":
        try:
            strategy = RSIStrategy(params)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        df_signals = strategy.generate_signals(df)
        used_params = strategy.get_params()

    elif strategy_type == "ai_generated":
        # 프리미엄 사용자만 AI 전략 사용 가능
        if not user.is_premium:
            raise HTTPException(
                status_code=403,
                detail="AI 전략은 프리미엄 구독 사용자만 이용 가능합니다.",
            )
        ai_result = await generate_ai_strategy(req.ticker, df, start_date, end_date)
        strategy_type_ai = ai_result.get("strategy_type", "ma_cross")
        ai_params = ai_result.get("params", {})
        ai_reason = ai_result.get("reason", "")

        # AI가 추천한 전략으로 실행
        if strategy_type_ai == "rsi":
            strategy_obj = RSIStrategy(ai_params)
        else:
            strategy_obj = MACrossStrategy(ai_params)

        df_signals = strategy_obj.generate_signals(df)
        used_params = ai_params
        used_params["ai_recommended_type"] = strategy_type_ai

    else:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 전략입니다. (ma_cross / rsi / ai_generated)",
        )

    # 시그널이 너무 적으면 백테스트 불가
    if len(df_signals) < 10:
        raise HTTPException(
            status_code=400,
            detail="데이터가 부족합니다. 더 긴 기간을 선택하거나 파라미터를 조정하세요.",
        )

    # 백테스트 실행
    result = run_backtest(df_signals)

    return {
        "result": result,
        "used_params": used_params,
        "start_date": start_date,
        "end_date": end_date,
        "strategy_type": strategy_type,
        "ai_reason": ai_reason,
    }


@router.post("/run", response_model=BacktestResultResponse, status_code=201)
async def run_backtest_endpoint(
    req: BacktestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    백테스팅 실행 및 결과 저장
    - 전략 유형: ma_cross / rsi / ai_generated
    - 무료: 최근 3년, 프리미엄: 최근 10년
    """
    bt = await _execute_backtest(req, current_user)
    result = bt["result"]

    # 전략 저장 요청이 있을 때
    strategy_id = None
    if req.save_strategy and req.strategy_name:
        strat = Strategy(
            user_id=current_user.id,
            name=req.strategy_name,
            strategy_type=bt["strategy_type"],
            params_json=json.dumps(bt["used_params"], ensure_ascii=False),
            description=bt.get("ai_reason"),
        )
        db.add(strat)
        await db.flush()
        strategy_id = strat.id

    # 결과 DB 저장
    from datetime import date
    backtest_record = BacktestResult(
        user_id=current_user.id,
        strategy_id=strategy_id,
        ticker=req.ticker,
        strategy_type=bt["strategy_type"],
        start_date=date.fromisoformat(bt["start_date"]),
        end_date=date.fromisoformat(bt["end_date"]),
        total_return=result["total_return"],
        annual_return=result["annual_return"],
        mdd=result["mdd"],
        sharpe=result["sharpe"],
        total_trades=result["total_trades"],
        win_rate=result["win_rate"],
        trades_json=json.dumps(result["trades"], ensure_ascii=False),
        params_json=json.dumps(bt["used_params"], ensure_ascii=False),
    )
    db.add(backtest_record)
    await db.flush()
    await db.refresh(backtest_record)
    return backtest_record


@router.get("/results", response_model=BacktestListResponse)
async def list_results(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    ticker: str = Query(None, description="티커 필터"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """내 백테스팅 결과 목록 조회 (최신순)"""
    query = (
        select(BacktestResult)
        .where(BacktestResult.user_id == current_user.id)
        .order_by(desc(BacktestResult.created_at))
    )
    if ticker:
        query = query.where(BacktestResult.ticker == ticker.upper())

    # 전체 개수
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # 페이지네이션
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return BacktestListResponse(total=total, items=list(items))


@router.get("/results/{result_id}", response_model=BacktestResultResponse)
async def get_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """특정 백테스팅 결과 상세 조회"""
    result = await db.execute(
        select(BacktestResult).where(
            BacktestResult.id == result_id,
            BacktestResult.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="백테스팅 결과를 찾을 수 없습니다.")
    return record


@router.post("/strategies", response_model=StrategyResponse, status_code=201)
async def save_strategy(
    strategy_in: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """전략 저장"""
    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_in.name,
        strategy_type=strategy_in.strategy_type,
        params_json=strategy_in.params_json,
        description=strategy_in.description,
    )
    db.add(strategy)
    await db.flush()
    await db.refresh(strategy)
    return strategy


@router.get("/strategies", response_model=List[StrategyResponse])
async def list_strategies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """내 저장된 전략 목록 조회"""
    result = await db.execute(
        select(Strategy)
        .where(Strategy.user_id == current_user.id)
        .order_by(desc(Strategy.created_at))
    )
    return result.scalars().all()


@router.delete("/strategies/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """전략 삭제"""
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id,
        )
    )
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다.")
    await db.delete(strategy)
