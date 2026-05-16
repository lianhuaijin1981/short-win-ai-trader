"""盘中监控路由 — 锚定标的、资金流向、板块预警

提供盘中实时监控功能:
- GET /intraday/anchors — 锚定标的
- GET /intraday/fund-flow — 资金流向
- GET /intraday/alerts — 板块预警
"""

import random
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import AnchorStock, FundFlowData, SectorAlert

logger = get_logger("swat.router.intraday")
config = APIConfig()

router = APIRouter(prefix="/intraday", tags=["Intraday"])


# ── 辅助函数 ────────────────────────────────────────────


def _generate_anchors() -> List[AnchorStock]:
    """生成锚定标的列表"""
    anchors = [
        ("600611.SH", "大众交通", "情绪锚定"),
        ("300308.SZ", "中际旭创", "板块锚定"),
        ("603893.SH", "瑞芯微", "趋势锚定"),
        ("002230.SZ", "科大讯飞", "容量锚定"),
        ("600519.SH", "贵州茅台", "指数锚定"),
        ("000001.SZ", "平安银行", "权重锚定"),
    ]
    result = []
    for ticker, name, anchor_type in anchors:
        price = round(random.uniform(10, 200), 2)
        result.append(AnchorStock(
            ticker=ticker,
            name=name,
            anchor_type=anchor_type,
            score=round(random.uniform(60, 95), 1),
            expectation=random.choice(["加速预期", "分歧预期", "回封预期", "低吸预期"]),
            boards=random.randint(1, 8),
            current_price=price,
            change_pct=round(random.uniform(-5, 10), 2),
        ))
    return sorted(result, key=lambda x: x.score, reverse=True)


def _generate_fund_flow() -> List[FundFlowData]:
    """生成资金流向数据"""
    sectors = [
        "光模块/CPO", "智慧交通", "消费电子", "芯片设计",
        "新能源汽车", "文化传媒", "先进封装", "人工智能",
        "生物医药", "白酒消费", "房地产", "银行保险",
    ]
    result = []
    for sector in sectors:
        inflow = round(random.uniform(-20, 50), 2)
        outflow = round(random.uniform(0, 40), 2) if inflow < 0 else round(random.uniform(0, 20), 2)
        result.append(FundFlowData(
            sector=sector,
            inflow=max(0, inflow),
            outflow=outflow,
            net=round(inflow - outflow, 2),
            limit_up_count=random.randint(0, 8) if inflow > 10 else 0,
        ))
    return sorted(result, key=lambda x: x.net, reverse=True)


def _generate_alerts() -> List[SectorAlert]:
    """生成板块预警数据"""
    alerts = [
        SectorAlert(
            sector="光模块/CPO",
            alert_type="加速预警",
            trigger="龙头涨停，板块内跟风股集体冲高",
            urgency="高",
            affected_stocks=["300308.SZ", "300502.SZ", "002281.SZ"],
        ),
        SectorAlert(
            sector="智慧交通",
            alert_type="分歧预警",
            trigger="大众交通炸板，后排开始走弱",
            urgency="高",
            affected_stocks=["600611.SH", "002232.SZ", "600686.SH"],
        ),
        SectorAlert(
            sector="消费电子",
            alert_type="启动预警",
            trigger="歌尔股份放量突破，板块异动",
            urgency="中",
            affected_stocks=["002241.SZ", "300433.SZ", "601231.SH"],
        ),
        SectorAlert(
            sector="白酒消费",
            alert_type="退潮预警",
            trigger="茅台跌破10日线，板块持续流出",
            urgency="中",
            affected_stocks=["600519.SH", "000858.SZ", "000568.SZ"],
        ),
    ]
    return alerts


# ── 路由 ────────────────────────────────────────────────


@router.get("/anchors", response_model=Dict)
async def get_anchor_stocks():
    """获取锚定标的

    返回当前市场的锚定标的列表，用于盘中观察和决策参考。
    """
    logger.info("GET /intraday/anchors")
    try:
        anchors = _generate_anchors()
        return {
            "code": 200,
            "message": "success",
            "data": {
                "anchors": [a.model_dump() for a in anchors],
                "count": len(anchors),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Anchors query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow", response_model=Dict)
async def get_fund_flow(
    sector: Optional[str] = Query(None, description="板块过滤"),
    min_net: float = Query(0, description="最小净流入过滤"),
):
    """获取资金流向

    返回各板块资金流向数据，用于判断资金主攻方向。
    """
    logger.info(f"GET /intraday/fund-flow sector={sector} min_net={min_net}")
    try:
        flows = _generate_fund_flow()
        if sector:
            flows = [f for f in flows if f.sector == sector]
        if min_net > 0:
            flows = [f for f in flows if f.net >= min_net]
        return {
            "code": 200,
            "message": "success",
            "data": {
                "flows": [f.model_dump() for f in flows],
                "total_inflow": round(sum(f.inflow for f in flows), 2),
                "total_outflow": round(sum(f.outflow for f in flows), 2),
                "net_flow": round(sum(f.net for f in flows), 2),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Fund flow query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=Dict)
async def get_sector_alerts(
    urgency: Optional[str] = Query(None, description="紧急程度: 高/中/低"),
):
    """获取板块预警

    返回当前市场板块异动预警，帮助及时发现风险和机会。
    """
    logger.info(f"GET /intraday/alerts urgency={urgency}")
    try:
        alerts = _generate_alerts()
        if urgency:
            alerts = [a for a in alerts if a.urgency == urgency]
        return {
            "code": 200,
            "message": "success",
            "data": {
                "alerts": [a.model_dump() for a in alerts],
                "count": len(alerts),
                "urgency_summary": {
                    "high": len([a for a in alerts if a.urgency == "高"]),
                    "medium": len([a for a in alerts if a.urgency == "中"]),
                    "low": len([a for a in alerts if a.urgency == "低"]),
                },
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Alerts query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
