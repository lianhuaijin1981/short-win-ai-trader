"""市场数据路由 — 市场概览、指数、涨停股、板块热力图

提供A股市场实时概览数据:
- /market/overview — 市场整体概览
- /market/indices — 三大指数详情
- /market/limit-up — 涨停股列表
- /market/heat-map — 板块热力图
"""

import asyncio
import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import IndexData, MarketOverview
from api.services.ifind_service import ifind_service

logger = get_logger("swat.router.market")
config = APIConfig()

router = APIRouter(prefix="/market", tags=["Market"])

# ── 辅助函数 ────────────────────────────────────────────


def _generate_mock_indices() -> List[IndexData]:
    """生成模拟指数数据（开发/测试环境）"""
    return [
        IndexData(
            name="上证指数",
            code="000001.SH",
            current=3052.37 + random.uniform(-20, 20),
            change=random.uniform(-15, 15),
            change_pct=random.uniform(-0.8, 0.8),
            volume=round(random.uniform(2500, 3500), 2),
            amount=round(random.uniform(2800, 3800), 2),
        ),
        IndexData(
            name="深证成指",
            code="399001.SZ",
            current=9788.42 + random.uniform(-50, 50),
            change=random.uniform(-40, 40),
            change_pct=random.uniform(-0.9, 0.9),
            volume=round(random.uniform(3000, 4500), 2),
            amount=round(random.uniform(3200, 4800), 2),
        ),
        IndexData(
            name="创业板指",
            code="399006.SZ",
            current=1897.63 + random.uniform(-15, 15),
            change=random.uniform(-12, 12),
            change_pct=random.uniform(-1.0, 1.0),
            volume=round(random.uniform(1200, 1800), 2),
            amount=round(random.uniform(1400, 2200), 2),
        ),
    ]


def _generate_mock_limit_up() -> List[Dict]:
    """生成模拟涨停股列表"""
    limit_up_stocks = [
        {"ticker": "600611.SH", "name": "大众交通", "boards": 5, "sector": "智慧交通", "amount": 12.5},
        {"ticker": "000793.SZ", "name": "华闻集团", "boards": 4, "sector": "文化传媒", "amount": 8.3},
        {"ticker": "603386.SH", "name": "骏亚科技", "boards": 3, "sector": "PCB", "amount": 6.7},
        {"ticker": "002232.SZ", "name": "启明信息", "boards": 3, "sector": "智能网联", "amount": 9.1},
        {"ticker": "600686.SH", "name": "金龙汽车", "boards": 3, "sector": "新能源汽车", "amount": 15.2},
        {"ticker": "603893.SH", "name": "瑞芯微", "boards": 2, "sector": "芯片设计", "amount": 22.8},
        {"ticker": "300308.SZ", "name": "中际旭创", "boards": 2, "sector": "光模块", "amount": 35.6},
        {"ticker": "002241.SZ", "name": "歌尔股份", "boards": 2, "sector": "消费电子", "amount": 18.4},
        {"ticker": "600520.SH", "name": "文一科技", "boards": 2, "sector": "先进封装", "amount": 7.9},
        {"ticker": "300502.SZ", "name": "新易盛", "boards": 2, "sector": "光通信", "amount": 28.3},
    ]
    for s in limit_up_stocks:
        s["price"] = round(random.uniform(8.0, 60.0), 2)
        s["change_pct"] = round(10.02 + random.uniform(-0.5, 0.5), 2)
        s["volume"] = round(random.uniform(50000, 500000))
        s["first_board_time"] = f"{random.randint(9, 10):02d}:{random.randint(25, 59):02d}"
    return limit_up_stocks


def _generate_mock_heat_map() -> List[Dict]:
    """生成模拟板块热力图数据"""
    sectors = [
        {"sector": "光模块/CPO", "temperature": 95, "change_pct": 5.82},
        {"sector": "消费电子", "temperature": 88, "change_pct": 4.35},
        {"sector": "智慧交通", "temperature": 92, "change_pct": 6.12},
        {"sector": "芯片设计", "temperature": 85, "change_pct": 3.78},
        {"sector": "新能源汽车", "temperature": 82, "change_pct": 3.25},
        {"sector": "文化传媒", "temperature": 78, "change_pct": 2.91},
        {"sector": "先进封装", "temperature": 80, "change_pct": 3.15},
        {"sector": "智能网联", "temperature": 76, "change_pct": 2.68},
        {"sector": "PCB", "temperature": 72, "change_pct": 2.34},
        {"sector": "光通信", "temperature": 74, "change_pct": 2.52},
        {"sector": "光伏储能", "temperature": 45, "change_pct": -1.25},
        {"sector": "医药生物", "temperature": 38, "change_pct": -2.10},
        {"sector": "房地产开发", "temperature": 32, "change_pct": -2.85},
        {"sector": "银行保险", "temperature": 28, "change_pct": -1.56},
        {"sector": "白酒消费", "temperature": 25, "change_pct": -3.20},
    ]
    for s in sectors:
        s["limit_up_count"] = random.randint(0, 8) if s["temperature"] > 60 else 0
        s["leading_stock"] = f"{random.randint(600000, 699999)}.SH" if random.random() > 0.5 else f"{random.randint(300000, 399999)}.SZ"
        s["net_inflow"] = round(random.uniform(-15, 30), 2)
    return sectors


def _generate_market_overview(indices: List[IndexData]) -> MarketOverview:
    """生成市场概览"""
    limit_up = random.randint(40, 120)
    limit_down = random.randint(3, 20)
    total = 5330
    up = random.randint(1800, 3500)
    down = total - up
    return MarketOverview(
        date=date.today().isoformat(),
        indices=indices,
        limit_up_count=limit_up,
        limit_down_count=limit_down,
        total_stocks=total,
        up_count=up,
        down_count=down,
        volume=round(sum(i.volume for i in indices), 2),
    )


# ── 路由 ────────────────────────────────────────────────


@router.get("/overview", response_model=Dict)
async def get_market_overview():
    """获取市场概览

    返回当日市场整体数据，包括三大指数、涨跌统计、涨停跌停数量等。
    """
    logger.info("GET /market/overview")

    try:
        if config.ifind_enabled:
            indices = await ifind_service.get_market_indices()
            if indices:
                indices_data = [IndexData(**idx) for idx in indices]
            else:
                indices_data = _generate_mock_indices()
        else:
            indices_data = _generate_mock_indices()

        overview = _generate_market_overview(indices_data)
        return {
            "code": 200,
            "message": "success",
            "data": overview.model_dump(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Market overview failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.get("/indices", response_model=Dict)
async def get_market_indices(
    refresh: bool = Query(False, description="强制刷新缓存"),
):
    """获取三大指数实时数据

    返回上证指数、深证成指、创业板指的实时行情。
    """
    logger.info(f"GET /market/indices (refresh={refresh})")

    try:
        if config.ifind_enabled and not refresh:
            indices = await ifind_service.get_market_indices()
            if indices:
                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "indices": indices,
                        "timestamp": datetime.now().isoformat(),
                        "source": "ifind",
                    },
                }

        indices_data = _generate_mock_indices()
        return {
            "code": 200,
            "message": "success",
            "data": {
                "indices": [idx.model_dump() for idx in indices_data],
                "timestamp": datetime.now().isoformat(),
                "source": "mock",
            },
        }
    except Exception as e:
        logger.error(f"Indices query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取指数数据失败: {str(e)}")


@router.get("/limit-up", response_model=Dict)
async def get_limit_up_stocks(
    date_str: Optional[str] = Query(None, description="查询日期 (YYYY-MM-DD)，默认今日"),
    sort_by: str = Query("boards", description="排序字段: boards/amount/change_pct"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
):
    """获取涨停股列表

    返回当日涨停股票列表，可按涨停连板数、成交额排序。
    """
    query_date = date_str or date.today().isoformat()
    logger.info(f"GET /market/limit-up date={query_date} sort={sort_by} limit={limit}")

    try:
        stocks = _generate_mock_limit_up()

        # 排序
        reverse = True
        if sort_by == "boards":
            stocks.sort(key=lambda x: x["boards"], reverse=reverse)
        elif sort_by == "amount":
            stocks.sort(key=lambda x: x["amount"], reverse=reverse)
        elif sort_by == "change_pct":
            stocks.sort(key=lambda x: x["change_pct"], reverse=reverse)

        stocks = stocks[:limit]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "date": query_date,
                "total_limit_up": len(stocks),
                "stocks": stocks,
                "summary": {
                    "max_boards": max(s["boards"] for s in stocks) if stocks else 0,
                    "avg_boards": round(sum(s["boards"] for s in stocks) / len(stocks), 1) if stocks else 0,
                    "total_amount": round(sum(s["amount"] for s in stocks), 2),
                },
            },
        }
    except Exception as e:
        logger.error(f"Limit-up query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取涨停股列表失败: {str(e)}")


@router.get("/heat-map", response_model=Dict)
async def get_sector_heat_map(
    sort_by: str = Query("temperature", description="排序: temperature/change_pct/net_inflow"),
    min_temperature: int = Query(0, ge=0, le=100, description="最低温度过滤"),
):
    """获取板块热力图

    返回各板块温度、涨跌幅、资金流向等数据，用于判断市场热点。
    """
    logger.info(f"GET /market/heat-map sort={sort_by} min_temp={min_temperature}")

    try:
        sectors = _generate_mock_heat_map()

        # 过滤
        if min_temperature > 0:
            sectors = [s for s in sectors if s["temperature"] >= min_temperature]

        # 排序
        reverse = True
        if sort_by == "temperature":
            sectors.sort(key=lambda x: x["temperature"], reverse=reverse)
        elif sort_by == "change_pct":
            sectors.sort(key=lambda x: x["change_pct"], reverse=reverse)
        elif sort_by == "net_inflow":
            sectors.sort(key=lambda x: x["net_inflow"], reverse=reverse)

        # 统计
        hot_sectors = [s for s in sectors if s["temperature"] >= 70]
        cold_sectors = [s for s in sectors if s["temperature"] <= 40]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "sectors": sectors,
                "hot_count": len(hot_sectors),
                "cold_count": len(cold_sectors),
                "avg_temperature": round(sum(s["temperature"] for s in sectors) / len(sectors), 1) if sectors else 0,
                "top_hot": hot_sectors[:5] if hot_sectors else [],
                "top_cold": cold_sectors[:5] if cold_sectors else [],
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Heat map query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块热力图失败: {str(e)}")
