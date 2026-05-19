"""AI交易策略路由 — 策略信号、市场分析、仓位建议

提供AI交易策略功能:
- GET /strategy/signals — 获取交易信号
- GET /strategy/summary — 获取策略摘要
- GET /strategy/context — 获取市场环境
- POST /strategy/analyze — 分析指定股票
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.services.strategy_engine import strategy_engine

logger = get_logger("swat.router.strategy")
config = APIConfig()

router = APIRouter(prefix="/strategy", tags=["Strategy"])


# ── 请求模型 ────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """股票分析请求"""
    tickers: List[str] = Field(..., description="股票代码列表", min_length=1, max_length=20)


# ── 路由 ────────────────────────────────────────────────


@router.get("/signals", response_model=Dict)
async def get_strategy_signals(
    limit: int = Query(10, ge=1, le=50, description="返回信号数量"),
    signal_type: Optional[str] = Query(None, description="信号类型过滤: buy/sell/hold/watch"),
):
    """获取交易信号

    返回AI策略引擎生成的交易信号列表，按置信度排序。
    """
    logger.info(f"GET /strategy/signals limit={limit} type={signal_type}")
    try:
        signals = await strategy_engine.generate_signals()
        
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        
        signals = signals[:limit]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "signals": [s.__dict__ for s in signals],
                "count": len(signals),
                "summary": {
                    "buy": len([s for s in signals if s.signal_type == "buy"]),
                    "sell": len([s for s in signals if s.signal_type == "sell"]),
                    "watch": len([s for s in signals if s.signal_type == "watch"]),
                    "hold": len([s for s in signals if s.signal_type == "hold"]),
                },
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Strategy signals failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略信号失败: {str(e)}")


@router.get("/summary", response_model=Dict)
async def get_strategy_summary():
    """获取策略摘要

    返回当前市场环境、信号统计、推荐策略和仓位建议。
    """
    logger.info("GET /strategy/summary")
    try:
        summary = await strategy_engine.get_strategy_summary()
        return {
            "code": 200,
            "message": "success",
            "data": summary,
        }
    except Exception as e:
        logger.error(f"Strategy summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略摘要失败: {str(e)}")


@router.get("/context", response_model=Dict)
async def get_market_context():
    """获取市场环境

    返回当前市场情绪、涨跌统计、热点板块等环境数据。
    """
    logger.info("GET /strategy/context")
    try:
        context = await strategy_engine.get_market_context()
        return {
            "code": 200,
            "message": "success",
            "data": {
                "date": context.date,
                "market_mood": context.market_mood,
                "sentiment_score": context.sentiment_score,
                "limit_up_count": context.limit_up_count,
                "limit_down_count": context.limit_down_count,
                "volume_billion": context.volume_billion,
                "hot_sectors": context.hot_sectors,
                "cold_sectors": context.cold_sectors,
                "mood_description": {
                    "strong": "强势市场，适合积极操作",
                    "neutral": "中性市场，精选个股",
                    "weak": "弱势市场，防守为主",
                    "chaos": "混沌市场，建议观望",
                }.get(context.market_mood, "未知"),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Market context failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场环境失败: {str(e)}")


@router.post("/analyze", response_model=Dict)
async def analyze_stocks(request: AnalyzeRequest):
    """分析指定股票

    对指定股票进行AI分析，生成交易信号。
    """
    logger.info(f"POST /strategy/analyze tickers={request.tickers}")
    try:
        signals = await strategy_engine.generate_signals(tickers=request.tickers)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "signals": [s.__dict__ for s in signals],
                "count": len(signals),
                "analyzed_tickers": request.tickers,
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Stock analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"股票分析失败: {str(e)}")