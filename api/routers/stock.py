"""个股路由 — 个股详情、K线、基本面、股东、公告

提供个股全维度数据查询:
- GET /stock/{ticker} — 个股全维度详情
- GET /stock/{ticker}/prices — K线数据
- GET /stock/{ticker}/fundamentals — 基本面
- GET /stock/{ticker}/holders — 股东信息
- GET /stock/{ticker}/announcements — 公告
"""

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import (
    ComprehensiveScore, DimensionScore, StockDetailResponse,
    TradePlanResponse, YingYouMatch, TacticMatch,
)
from api.services.ifind_service import ifind_service

logger = get_logger("swat.router.stock")
config = APIConfig()

router = APIRouter(prefix="/stock", tags=["Stock"])

# ── 模拟数据生成 ────────────────────────────────────────


def _generate_mock_kline(days: int = 60) -> List[Dict]:
    """生成模拟K线数据"""
    klines = []
    base_price = random.uniform(30, 150)
    current_price = base_price

    for i in range(days):
        d = date.today() - timedelta(days=days - i)
        if d.weekday() >= 5:
            continue

        change_pct = random.uniform(-0.06, 0.06)
        open_p = round(current_price * (1 + random.uniform(-0.02, 0.02)), 2)
        close_p = round(current_price * (1 + change_pct), 2)
        high_p = round(max(open_p, close_p) * (1 + random.uniform(0, 0.03)), 2)
        low_p = round(min(open_p, close_p) * (1 - random.uniform(0, 0.03)), 2)
        volume = random.randint(100000, 2000000)
        amount = round(close_p * volume / 10000, 2)

        klines.append({
            "date": d.isoformat(),
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
            "amount": amount,
            "change_pct": round((close_p - open_p) / open_p * 100, 2),
            "ma5": round(close_p * (1 + random.uniform(-0.01, 0.01)), 2),
            "ma10": round(close_p * (1 + random.uniform(-0.02, 0.02)), 2),
            "ma20": round(close_p * (1 + random.uniform(-0.03, 0.03)), 2),
        })
        current_price = close_p

    return klines


def _generate_mock_fundamentals(ticker: str) -> Dict:
    """生成模拟基本面数据"""
    return {
        "ticker": ticker,
        "profitability": {
            "roe": round(random.uniform(5, 25), 2),
            "roa": round(random.uniform(3, 15), 2),
            "gross_margin": round(random.uniform(20, 65), 2),
            "net_margin": round(random.uniform(8, 30), 2),
            "eps": round(random.uniform(0.5, 15), 2),
        },
        "growth": {
            "revenue_growth_yoy": round(random.uniform(-10, 50), 2),
            "profit_growth_yoy": round(random.uniform(-20, 80), 2),
            "net_profit_growth_yoy": round(random.uniform(-15, 60), 2),
            "roe_growth": round(random.uniform(-5, 20), 2),
        },
        "capital_structure": {
            "debt_to_asset": round(random.uniform(0.2, 0.7), 2),
            "equity_ratio": round(random.uniform(0.3, 0.8), 2),
            "current_ratio": round(random.uniform(1.0, 3.0), 2),
            "quick_ratio": round(random.uniform(0.8, 2.5), 2),
        },
        "liquidity": {
            "turnover_rate": round(random.uniform(0.5, 8.0), 2),
            "volume_ratio": round(random.uniform(0.3, 5.0), 2),
            "amplitude": round(random.uniform(2, 12), 2),
        },
        "valuation": {
            "pe_ttm": round(random.uniform(10, 80), 2),
            "pb": round(random.uniform(1, 15), 2),
            "ps": round(random.uniform(1, 20), 2),
            "market_cap": round(random.uniform(50, 5000), 2),
        },
    }


def _generate_mock_holders(ticker: str) -> Dict:
    """生成模拟股东信息"""
    top_holders = []
    names = ["香港中央结算", "中国证券金融", "中央汇金", "社保基金", "公募基金", "QFII", "保险公司", "券商自营"]
    for i in range(10):
        top_holders.append({
            "rank": i + 1,
            "holder_name": f'{random.choice(names)}{i+1}' if random.random() > 0.3 else f'股东{i+1}',
            "hold_count": round(random.uniform(100, 5000), 2),
            "hold_pct": round(random.uniform(0.5, 15), 2),
            "change": round(random.uniform(-3, 3), 2),
            "change_type": random.choice(["增持", "减持", "不变"]),
        })

    top_holders.sort(key=lambda x: x["hold_pct"], reverse=True)
    for i, h in enumerate(top_holders):
        h["rank"] = i + 1

    return {
        "ticker": ticker,
        "holder_count": random.randint(20000, 150000),
        "holder_count_change": random.randint(-5000, 5000),
        "avg_shares_per_holder": round(random.uniform(5000, 20000), 2),
        "concentration": round(random.uniform(20, 80), 2),
        "top10_hold_pct": round(sum(h["hold_pct"] for h in top_holders), 2),
        "top10_liquid_hold_pct": round(random.uniform(30, 70), 2),
        "top_holders": top_holders,
        "fund_holders": random.randint(50, 500),
        "fund_hold_pct": round(random.uniform(2, 25), 2),
        "northbound_hold_pct": round(random.uniform(0.5, 12), 2),
    }


def _generate_mock_announcements(ticker: str, days: int = 30) -> List[Dict]:
    """生成模拟公告"""
    categories = [
        "定期报告", "重大事项", "股权激励", "股东增减持", "关联交易",
        "对外担保", "收购兼并", "股权质押", "澄清公告", "其他",
    ]
    titles = [
        "2026年第一季度报告", "关于签订重大合同的公告", "关于回购股份方案的公告",
        "关于股东减持股份的预披露公告", "关于对外投资设立子公司的公告",
        "关于2025年度利润分配方案的公告", "关于召开股东大会的通知",
        "关于获得政府补助的公告", "关于聘任高级管理人员的公告",
        "关于公司实际控制人变更的公告", "关于发行股份购买资产暨关联交易预案",
        "关于募集资金使用进展的公告", "关于股价异常波动的公告",
        "关于解除股权质押的公告", "关于重大合同中标公告",
    ]

    announcements = []
    for i in range(min(days, len(titles))):
        d = date.today() - timedelta(days=i * 3)
        announcements.append({
            "id": f"ANN{i+1:03d}",
            "ticker": ticker,
            "date": d.isoformat(),
            "category": random.choice(categories),
            "title": random.choice(titles),
            "is_important": random.random() > 0.5,
            "content_summary": f'公司于{d.isoformat()}发布{random.choice(categories)}相关公告，具体内容详见公告全文。',
            "source": "巨潮资讯网",
        })

    return sorted(announcements, key=lambda x: x["date"], reverse=True)


def _generate_yingyou_matches(ticker: str) -> List[YingYouMatch]:
    """生成游资匹配数据"""
    yingyous = ["章盟主", "方新侠", "赵老哥", "作手新一", "炒股养家", "著名刺客", "上塘路", "宁波桑田路"]
    matches = []
    for yy in yingyous[:random.randint(2, 5)]:
        score = round(random.uniform(50, 95), 1)
        matches.append(YingYouMatch(
            yingyou_name=yy,
            ticker=ticker,
            name="",
            match_score=score,
            recommendation="积极跟踪" if score >= 70 else "谨慎关注",
            operation="跟随建仓" if score >= 75 else "观望",
            position="20-30%" if score >= 75 else "10-15%",
            stop_loss="-5%" if score >= 75 else "-3%",
            take_profit="+15%" if score >= 75 else "+8%",
        ))
    matches.sort(key=lambda x: x.match_score, reverse=True)
    return matches


def _generate_tactic_matches(ticker: str) -> List[TacticMatch]:
    """生成战法匹配数据"""
    tactics = [
        ("龙回头", "强势股回调后的二次启动机会"),
        ("首板竞价", "竞价阶段捕捉首板涨停机会"),
        ("弱转强", "从弱势转为强势的拐点介入"),
        ("趋势突破", "突破关键阻力位后的趋势延续"),
        ("一字首开", "一字板首次打开后的博弈机会"),
    ]
    matches = []
    for name, desc in tactics[:random.randint(2, 4)]:
        score = round(random.uniform(50, 92), 1)
        matches.append(TacticMatch(
            tactic_name=name,
            ticker=ticker,
            name="",
            match_score=score,
            shape_verdict=desc,
            adaptability="高" if score >= 70 else "中",
            sustainability="强" if score >= 75 else "一般",
            prediction="有望延续" if score >= 70 else "需谨慎",
        ))
    matches.sort(key=lambda x: x.match_score, reverse=True)
    return matches


# ── 路由 ────────────────────────────────────────────────


@router.get("/{ticker}", response_model=Dict)
async def get_stock_detail(ticker: str):
    """获取个股全维度详情

    返回指定股票的全维度数据，包括价格、情绪定位、评分、游资匹配、战法匹配、交易计划等。
    """
    logger.info(f"GET /stock/{ticker}")

    try:
        # 获取K线（最近1日用于当前价）
        klines = _generate_mock_kline(5)
        current_price = klines[-1]["close"] if klines else 0
        change_pct = klines[-1]["change_pct"] if klines else 0

        # 综合评分
        dim_scores = [
            DimensionScore(dimension="新闻催化", weight=15, score=round(random.uniform(55, 92), 1), details={}),
            DimensionScore(dimension="基本面", weight=10, score=round(random.uniform(50, 88), 1), details={}),
            DimensionScore(dimension="技术面", weight=20, score=round(random.uniform(55, 90), 1), details={}),
            DimensionScore(dimension="筹码结构", weight=20, score=round(random.uniform(50, 85), 1), details={}),
            DimensionScore(dimension="情绪周期", weight=15, score=round(random.uniform(60, 95), 1), details={}),
            DimensionScore(dimension="资金流向", weight=20, score=round(random.uniform(55, 93), 1), details={}),
        ]
        total_score = round(sum(d.score * d.weight for d in dim_scores) / 100, 1)

        rating = "优质标的" if total_score >= 70 else "良好标的" if total_score >= 55 else "一般标的"
        yingyou = _generate_yingyou_matches(ticker)
        tactics = _generate_tactic_matches(ticker)

        plan = TradePlanResponse(
            ticker=ticker,
            name="",
            entry_price=round(current_price * 1.02, 2),
            entry_type=random.choice(["竞价抢筹", "突破入场", "回踩低吸"]),
            stop_loss=round(current_price * 0.95, 2),
            take_profit=round(current_price * 1.15, 2),
            position_pct=min(total_score * 0.4, 30),
            risk_reward=f'{round((current_price * 0.15) / (current_price * 0.05), 1)}:1',
            hold_conditions=["封单稳定", "板块强势", "大盘无风险"],
            sell_conditions=["跌破止损", "炸板不回封", "达到止盈"],
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "name": ticker,
                "current_price": current_price,
                "change_pct": change_pct,
                "emotion_cycle": random.choice(["发酵期", "高潮期", "回暖期"]),
                "theme_position": random.choice(["主线龙头", "板块中军", "后排跟风"]),
                "anchor_position": random.choice(["情绪锚定", "板块锚定", "观察标的"]),
                "comprehensive_score": total_score,
                "rating": rating,
                "yingyou_matches": [m.model_dump() for m in yingyou],
                "tactic_matches": [m.model_dump() for m in tactics],
                "trade_plan": plan.model_dump(),
                "risk_points": [
                    "大盘情绪退潮风险",
                    "板块轮动导致资金分流",
                    "高位股补跌风险",
                ],
                "success_logic": [
                    "主线题材核心标的",
                    "资金持续流入",
                    "技术形态良好",
                ],
                "kline": klines,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Stock detail failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取个股详情失败: {str(e)}")


@router.get("/{ticker}/prices", response_model=Dict)
async def get_stock_prices(
    ticker: str,
    days: int = Query(60, ge=5, le=252, description="K线天数"),
    interval: str = Query("D", description="周期: D/ W / M"),
):
    """获取K线数据

    返回指定股票的K线数据（开盘价、最高价、最低价、收盘价、成交量等），
    支持日线、周线、月线。
    """
    logger.info(f"GET /stock/{ticker}/prices days={days} interval={interval}")

    try:
        if config.ifind_enabled:
            try:
                prices = await ifind_service.get_recent_prices([ticker], days=days)
                if prices:
                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "ticker": ticker,
                            "interval": interval,
                            "count": len(prices),
                            "prices": prices,
                            "source": "ifind",
                        },
                    }
            except Exception as e:
                logger.warning(f"iFind prices failed for {ticker}: {e}")

        klines = _generate_mock_kline(days)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "interval": interval,
                "count": len(klines),
                "prices": klines,
                "source": "mock",
                "latest": klines[-1] if klines else None,
                "stats": {
                    "high": max(k["high"] for k in klines) if klines else 0,
                    "low": min(k["low"] for k in klines) if klines else 0,
                    "avg_volume": round(sum(k["volume"] for k in klines) / len(klines), 0) if klines else 0,
                    "total_change_pct": round((klines[-1]["close"] - klines[0]["open"]) / klines[0]["open"] * 100, 2) if klines else 0,
                },
            },
        }
    except Exception as e:
        logger.error(f"Prices query failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/{ticker}/fundamentals", response_model=Dict)
async def get_stock_fundamentals(
    ticker: str,
    refresh: bool = Query(False, description="强制刷新"),
):
    """获取基本面数据

    返回指定股票的财务指标，包括盈利能力、成长性、资本结构、流动性、估值等。
    """
    logger.info(f"GET /stock/{ticker}/fundamentals refresh={refresh}")

    try:
        if config.ifind_enabled and not refresh:
            try:
                fundamentals = await ifind_service.get_stock_fundamentals(ticker)
                if fundamentals:
                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "ticker": ticker,
                            "fundamentals": fundamentals,
                            "source": "ifind",
                        },
                    }
            except Exception as e:
                logger.warning(f"iFind fundamentals failed for {ticker}: {e}")

        fundamentals = _generate_mock_fundamentals(ticker)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "fundamentals": fundamentals,
                "source": "mock",
                "score": {
                    "profitability": round(fundamentals["profitability"]["roe"] / 30 * 100, 1),
                    "growth": round(max(0, fundamentals["growth"]["profit_growth_yoy"]) / 100 * 100, 1),
                    "valuation": round(max(0, 100 - fundamentals["valuation"]["pe_ttm"]) / 100 * 100, 1),
                    "overall": round(
                        (fundamentals["profitability"]["roe"] +
                         max(0, fundamentals["growth"]["profit_growth_yoy"]) / 3 +
                         max(0, 100 - fundamentals["valuation"]["pe_ttm"])) / 3, 1
                    ),
                },
            },
        }
    except Exception as e:
        logger.error(f"Fundamentals query failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取基本面失败: {str(e)}")


@router.get("/{ticker}/holders", response_model=Dict)
async def get_stock_holders(
    ticker: str,
    refresh: bool = Query(False),
):
    """获取股东信息

    返回指定股票的股东结构、十大股东、机构持仓、北向资金持仓等。
    """
    logger.info(f"GET /stock/{ticker}/holders refresh={refresh}")

    try:
        if config.ifind_enabled and not refresh:
            try:
                holders = await ifind_service.get_holder_info(ticker)
                if holders:
                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "ticker": ticker,
                            "holders": holders,
                            "source": "ifind",
                        },
                    }
            except Exception as e:
                logger.warning(f"iFind holders failed for {ticker}: {e}")

        holders = _generate_mock_holders(ticker)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "holders": holders,
                "source": "mock",
                "analysis": {
                    "concentration_level": "集中" if holders["concentration"] > 60 else "分散" if holders["concentration"] < 40 else "适中",
                    "institutional_influence": "强" if holders["fund_hold_pct"] > 15 else "弱" if holders["fund_hold_pct"] < 5 else "中等",
                    "northbound_active": "活跃" if holders["northbound_hold_pct"] > 5 else "一般",
                },
            },
        }
    except Exception as e:
        logger.error(f"Holders query failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取股东信息失败: {str(e)}")


@router.get("/{ticker}/announcements", response_model=Dict)
async def get_stock_announcements(
    ticker: str,
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    category: Optional[str] = Query(None, description="公告类别过滤"),
):
    """获取公告

    返回指定股票在指定天数内的公告列表，可按类别过滤。
    """
    logger.info(f"GET /stock/{ticker}/announcements days={days} category={category}")

    try:
        if config.ifind_enabled:
            try:
                announcements = await ifind_service.get_announcements(ticker, days=days)
                if announcements:
                    if category:
                        announcements = [a for a in announcements if a.get("category") == category]
                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "ticker": ticker,
                            "count": len(announcements),
                            "announcements": announcements,
                            "source": "ifind",
                        },
                    }
            except Exception as e:
                logger.warning(f"iFind announcements failed for {ticker}: {e}")

        announcements = _generate_mock_announcements(ticker, days)
        if category:
            announcements = [a for a in announcements if a["category"] == category]

        important = [a for a in announcements if a.get("is_important")]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "count": len(announcements),
                "announcements": announcements,
                "important_count": len(important),
                "important_announcements": important[:5],
                "category_distribution": _count_by_category(announcements),
                "source": "mock",
            },
        }
    except Exception as e:
        logger.error(f"Announcements query failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取公告失败: {str(e)}")


def _count_by_category(announcements: List[Dict]) -> Dict:
    """按类别统计公告数量"""
    counts = {}
    for a in announcements:
        cat = a.get("category", "其他")
        counts[cat] = counts.get(cat, 0) + 1
    return counts
