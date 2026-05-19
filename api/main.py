"""FastAPI 后端主入口 — 短线致胜 AI 交易智能体 API 服务"""

import asyncio
from contextlib import asynccontextmanager
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from api.routers import (
    market_router, news_router, sentiment_router,
    scoring_router, yingyou_router, tactics_router,
    intraday_router, diagnosis_router, stock_router,
    journal_router, strategy_router,
    # 用户账号体系路由
    auth_router, user_router, membership_router,
    order_router, admin_router,
)
from api.core.config import APIConfig
from api.core.logger import get_logger
from api.services.static_proxy import setup_static_files, router as static_router
from api.services.data_sync import data_sync_service
from api.services.websocket_manager import websocket_service

logger = get_logger("swat.api")
config = APIConfig()

# ── Lifespan ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("SWAT API Server starting...")
    logger.info(f"Version: 2.0.0 | Date: {datetime.now().isoformat()}")
    logger.info(f"iFind API: {'Enabled' if config.ifind_enabled else 'Disabled (using mock data)'}")
    logger.info("=" * 60)
    
    # 启动数据同步服务
    await data_sync_service.start()
    logger.info("Data sync service started")
    
    # 启动 WebSocket 服务
    await websocket_service.start()
    logger.info("WebSocket service started")
    
    yield
    
    # 停止服务
    await websocket_service.stop()
    await data_sync_service.stop()
    logger.info("SWAT API Server shutting down...")

# ── FastAPI App ─────────────────────────────────────────

app = FastAPI(
    title="短线致胜 AI 交易智能体 API",
    description="A股超短线AI决策系统 — 对接同花顺iFind数据",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局异常处理 ────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

# ── Health Check ────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "ifind_connected": config.ifind_enabled,
            "modules": {
            "m01_news": "active",
            "m02_sentiment": "active",
            "m03_intraday": "active",
            "m04_yingyou": "active",
            "m05_tactics": "active",
            "m06_scoring": "active",
            "m07_diagnosis": "active",
            "m08_journal": "active",
            "m09_user_system": "active",
            "m10_strategy": "active",
        },
    }

@app.get("/api", tags=["System"])
async def api_info():
    """API信息（原根路径，改为 /api 避免与SPA冲突）"""
    return {
        "name": "短线致胜 AI 交易智能体 API",
        "version": "2.0.0",
        "docs": "/docs",
            "endpoints": {
            "market": "/api/v1/market",
            "sentiment": "/api/v1/sentiment",
            "intraday": "/api/v1/intraday",
            "yingyou": "/api/v1/yingyou",
            "tactics": "/api/v1/tactics",
            "scoring": "/api/v1/scoring",
            "diagnosis": "/api/v1/diagnosis",
            "stock": "/api/v1/stock",
            "news": "/api/v1/news",
            "journal": "/api/v1/journal",
            "strategy": "/api/v1/strategy",
            "auth": "/api/v1/auth",
            "user": "/api/v1/user",
            "membership": "/api/v1/membership",
            "order": "/api/v1/order",
            "admin": "/api/v1/admin",
        },
    }

# ── 静态文件 & 前端页面 ─────────────────────────────────
setup_static_files(app)
app.include_router(static_router)

# ── 注册路由 ────────────────────────────────────────────

app.include_router(market_router, prefix="/api/v1", tags=["Market"])
app.include_router(sentiment_router, prefix="/api/v1", tags=["Sentiment"])
app.include_router(intraday_router, prefix="/api/v1", tags=["Intraday"])
app.include_router(yingyou_router, prefix="/api/v1", tags=["Yingyou"])
app.include_router(tactics_router, prefix="/api/v1", tags=["Tactics"])
app.include_router(scoring_router, prefix="/api/v1", tags=["Scoring"])
app.include_router(diagnosis_router, prefix="/api/v1", tags=["Diagnosis"])
app.include_router(stock_router, prefix="/api/v1", tags=["Stock"])
app.include_router(news_router, prefix="/api/v1", tags=["News"])
app.include_router(journal_router, prefix="/api/v1", tags=["TradeJournal"])
app.include_router(strategy_router, prefix="/api/v1", tags=["Strategy"])

# 用户账号体系路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(membership_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# ── WebSocket 端点 ──────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, channel: str = "all"):
    """WebSocket 实时数据推送端点
    
    支持的频道:
    - all: 所有数据
    - market: 市场数据
    - limit_up: 涨停板
    - sentiment: 情绪诊断
    - fund_flow: 资金流向
    """
    await websocket_service.handle_connection(websocket, channel)


@app.get("/ws/status", tags=["System"])
async def websocket_status():
    """WebSocket 连接状态"""
    return {
        "connections": websocket_service.manager.connection_count,
        "channels": {
            ch: len(subs) 
            for ch, subs in websocket_service.manager.channel_subscriptions.items()
        },
    }


# ── 数据同步控制端点 ─────────────────────────────────────

@app.post("/api/v1/sync/trigger", tags=["System"])
async def trigger_sync(data_type: str = "all"):
    """手动触发数据同步"""
    results = {}
    
    if data_type in ("all", "market"):
        results["market"] = await data_sync_service.sync_market_overview()
    
    if data_type in ("all", "limit_up"):
        results["limit_up"] = await data_sync_service.sync_limit_up_stocks()
    
    if data_type in ("all", "sentiment"):
        results["sentiment"] = await data_sync_service.sync_sentiment()
    
    if data_type in ("all", "fund_flow"):
        results["fund_flow"] = await data_sync_service.sync_fund_flow()
    
    return {
        "status": "synced",
        "types": list(results.keys()),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/sync/status", tags=["System"])
async def sync_status():
    """数据同步状态"""
    return {
        "running": data_sync_service._running,
        "ifind_available": data_sync_service._ifind_available,
        "intervals": data_sync_service.intervals,
        "cache_stats": {
            "memory_keys": len(data_sync_service.cache._memory_cache),
        },
    }


# ── 启动入口 ────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info",
    )
