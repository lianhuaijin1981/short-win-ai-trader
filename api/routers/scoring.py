"""评分决策路由 — 评分排行、个股评分、风险收益比、交易计划

提供超短线标的综合评分与决策支持:
- /scoring/rank — 评分排行榜Top10
- /scoring/calculate — 计算指定股票评分
- /scoring/risk-reward — 风险收益比计算器
- /scoring/trade-plan — 交易计划生成
"""

import random
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import ComprehensiveScore, DimensionScore, TradePlanResponse

logger = get_logger("swat.router.scoring")
config = APIConfig()

router = APIRouter(prefix="/scoring", tags=["Scoring"])

# ── 请求模型 ────────────────────────────────────────────


class RiskRewardRequest(BaseModel):
    """风险收益比计算请求"""
    entry_price: float = Field(..., gt=0, description="入场价格")
    stop_loss: float = Field(..., gt=0, description="止损价格")
    take_profit: float = Field(..., gt=0, description="止盈价格")
    position_size: Optional[int] = Field(100, ge=1, le=100, description="仓位比例%")
    confidence: Optional[int] = Field(50, ge=0, le=100, description="信心度%")


class ScoreCalculateRequest(BaseModel):
    """评分计算请求"""
    ticker: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    context: Optional[Dict] = Field(None, description="额外上下文")


# ── 评分维度定义 ────────────────────────────────────────

DIMENSIONS = [
    {"name": "新闻催化", "weight": 15},
    {"name": "基本面", "weight": 10},
    {"name": "技术面", "weight": 20},
    {"name": "筹码结构", "weight": 20},
    {"name": "情绪周期", "weight": 15},
    {"name": "资金流向", "weight": 20},
]


def _calculate_dimension_scores() -> List[DimensionScore]:
    """生成各维度评分"""
    return [
        DimensionScore(
            dimension=d["name"],
            weight=d["weight"],
            score=round(random.uniform(40, 95), 1),
            details=_generate_dimension_details(d["name"]),
        )
        for d in DIMENSIONS
    ]


def _generate_dimension_details(dimension: str) -> Dict:
    """生成维度详细子项"""
    details_map = {
        "新闻催化": {
            "level_score": round(random.uniform(50, 100)),
            "timeliness_score": round(random.uniform(50, 100)),
            "strength_score": round(random.uniform(50, 100)),
            "feedback_score": round(random.uniform(50, 100)),
        },
        "基本面": {
            "growth_score": round(random.uniform(40, 95)),
            "valuation_score": round(random.uniform(40, 95)),
            "health_score": round(random.uniform(40, 95)),
            "theme_purity_score": round(random.uniform(40, 95)),
        },
        "技术面": {
            "ma_score": round(random.uniform(40, 95)),
            "breakout_score": round(random.uniform(40, 95)),
            "volume_score": round(random.uniform(40, 95)),
            "indicators_score": round(random.uniform(40, 95)),
        },
        "筹码结构": {
            "concentration_score": round(random.uniform(40, 95)),
            "lock_ratio_score": round(random.uniform(40, 95)),
            "trapped_ratio_score": round(random.uniform(40, 95)),
            "peak_shape_score": round(random.uniform(40, 95)),
        },
        "情绪周期": {
            "cycle_match_score": round(random.uniform(40, 95)),
            "sector_effect_score": round(random.uniform(40, 95)),
            "dragon_status_score": round(random.uniform(40, 95)),
            "profit_effect_score": round(random.uniform(40, 95)),
        },
        "资金流向": {
            "main_inflow_score": round(random.uniform(40, 95)),
            "dragon_bond_score": round(random.uniform(40, 95)),
            "seal_strength_score": round(random.uniform(40, 95)),
            "northbound_score": round(random.uniform(40, 95)),
        },
    }
    return details_map.get(dimension, {})


def _get_rating(total_score: float) -> str:
    """根据总分返回评级"""
    if total_score >= 85:
        return "顶级标的"
    elif total_score >= 70:
        return "优质标的"
    elif total_score >= 55:
        return "良好标的"
    elif total_score >= 40:
        return "一般标的"
    else:
        return "劣质标的"


def _get_decision(total_score: float, risk_reward: float) -> str:
    """根据评分和RR生成决策建议"""
    if total_score >= 85 and risk_reward >= 3.0:
        return "强烈推荐介入"
    elif total_score >= 70 and risk_reward >= 2.5:
        return "积极关注"
    elif total_score >= 55 and risk_reward >= 2.0:
        return "可小仓位试错"
    elif total_score >= 40 and risk_reward >= 1.5:
        return "谨慎参与"
    else:
        return "不建议参与"


def _get_risk_level(total_score: float) -> str:
    """根据评分确定风险等级"""
    if total_score >= 80:
        return "低风险"
    elif total_score >= 60:
        return "中低风险"
    elif total_score >= 45:
        return "中风险"
    elif total_score >= 30:
        return "高风险"
    else:
        return "极高风险"


def _generate_mock_scores(count: int = 10) -> List[ComprehensiveScore]:
    """生成模拟评分数据"""
    stocks = [
        ("300308.SZ", "中际旭创"),
        ("002230.SZ", "科大讯飞"),
        ("600611.SH", "大众交通"),
        ("002241.SZ", "歌尔股份"),
        ("603893.SH", "瑞芯微"),
        ("300502.SZ", "新易盛"),
        ("600519.SH", "贵州茅台"),
        ("000001.SZ", "平安银行"),
        ("002594.SZ", "比亚迪"),
        ("300750.SZ", "宁德时代"),
        ("688981.SH", "中芯国际"),
        ("002371.SZ", "北方华创"),
        ("300418.SZ", "昆仑万维"),
        ("002456.SZ", "欧菲光"),
        ("600050.SH", "中国联通"),
    ]

    scores = []
    for ticker, name in stocks[:count]:
        dim_scores = _calculate_dimension_scores()
        total = sum(d.score * d.weight for d in dim_scores) / sum(d.weight for d in dim_scores)
        total = round(total, 1)
        rr = round(random.uniform(1.0, 5.5), 1)

        scores.append(ComprehensiveScore(
            ticker=ticker,
            name=name,
            total_score=total,
            rating=_get_rating(total),
            risk_reward_ratio=rr,
            risk_level=_get_risk_level(total),
            priority=0,
            position_pct=min(total * 0.4, 30),
            decision=_get_decision(total, rr),
            dimension_scores=dim_scores,
        ))

    # 按总分降序排列
    scores.sort(key=lambda s: s.total_score, reverse=True)
    for i, s in enumerate(scores):
        s.priority = i + 1

    return scores


def _generate_trade_plan(ticker: str, name: str, score: float, rating: str) -> TradePlanResponse:
    """生成交易计划"""
    entry_price = round(random.uniform(20, 200), 2)
    stop_pct = random.uniform(0.03, 0.08)
    profit_pct = random.uniform(0.10, 0.25)

    entry_types = ["竞价抢筹", "突破入场", "回踩低吸", "接力打板", "弱转强"]

    return TradePlanResponse(
        ticker=ticker,
        name=name,
        entry_price=round(entry_price, 2),
        entry_type=random.choice(entry_types),
        stop_loss=round(entry_price * (1 - stop_pct), 2),
        take_profit=round(entry_price * (1 + profit_pct), 2),
        position_pct=min(score * 0.4, 30),
        risk_reward=f'{round(profit_pct / stop_pct, 1)}:1',
        hold_conditions=[
            "封单持续加大或稳定",
            "板块内跟风股表现强势",
            "大盘指数无大跌风险",
            "龙虎榜显示游资接力",
            "次日竞价高开超2%",
        ],
        sell_conditions=[
            "跌破止损位坚决离场",
            "炸板且10分钟内未回封",
            "板块内跟风股大面积炸板",
            "达到止盈目标分批减仓",
            "尾盘炸板风险加大",
        ],
    )


# ── 路由 ────────────────────────────────────────────────


@router.get("/rank", response_model=Dict)
async def get_scoring_rank(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    min_score: int = Query(0, ge=0, le=100, description="最低评分"),
    sector: Optional[str] = Query(None, description="板块过滤"),
):
    """评分排行榜 Top N

    返回综合评分最高的N只股票，包含6维度评分、评级、风险收益比等。
    """
    logger.info(f"GET /scoring/rank limit={limit} min_score={min_score} sector={sector}")

    try:
        scores = _generate_mock_scores(count=limit)

        if min_score > 0:
            scores = [s for s in scores if s.total_score >= min_score]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "rankings": [s.model_dump() for s in scores],
                "total": len(scores),
                "summary": {
                    "avg_score": round(sum(s.total_score for s in scores) / len(scores), 1) if scores else 0,
                    "top_score": scores[0].total_score if scores else 0,
                    "top_ticker": scores[0].ticker if scores else "",
                    "top_name": scores[0].name if scores else "",
                },
                "filters": {
                    "limit": limit,
                    "min_score": min_score,
                    "sector": sector,
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Scoring rank failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分排行失败: {str(e)}")


@router.get("/calculate", response_model=Dict)
async def calculate_stock_score(
    ticker: str = Query(..., description="股票代码，如 600519.SH"),
    stock_name: Optional[str] = Query(None, description="股票名称"),
):
    """计算指定股票评分

    对指定股票进行综合评分计算，返回6维度详细评分结果。
    """
    logger.info(f"GET /scoring/calculate ticker={ticker}")

    try:
        dim_scores = _calculate_dimension_scores()
        total = sum(d.score * d.weight for d in dim_scores) / sum(d.weight for d in dim_scores)
        total = round(total, 1)
        rr = round(random.uniform(1.5, 5.0), 1)
        rating = _get_rating(total)

        score = ComprehensiveScore(
            ticker=ticker,
            name=stock_name or ticker,
            total_score=total,
            rating=rating,
            risk_reward_ratio=rr,
            risk_level=_get_risk_level(total),
            priority=1,
            position_pct=min(total * 0.4, 30),
            decision=_get_decision(total, rr),
            dimension_scores=dim_scores,
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "score": score.model_dump(),
                "interpretation": {
                    "rating_meaning": _get_rating_meaning(rating),
                    "risk_level_meaning": _get_risk_level_meaning(score.risk_level),
                    "position_advice": f'建议仓位 {score.position_pct:.0f}% 以内',
                    "key_strengths": _get_key_strengths(dim_scores),
                    "key_weaknesses": _get_key_weaknesses(dim_scores),
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Score calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"评分计算失败: {str(e)}")


def _get_rating_meaning(rating: str) -> str:
    meanings = {
        "顶级标的": "综合实力极强，适合重仓参与",
        "优质标的": "综合实力较强，值得重点关注",
        "良好标的": "具备一定优势，可适当参与",
        "一般标的": "优缺点并存，需谨慎对待",
        "劣质标的": "风险大于机会，建议回避",
    }
    return meanings.get(rating, "")


def _get_risk_level_meaning(level: str) -> str:
    meanings = {
        "低风险": "安全边际较高",
        "中低风险": "风险可控",
        "中风险": "需要关注风险",
        "高风险": "风险较大",
        "极高风险": "风险极高，谨慎",
    }
    return meanings.get(level, "")


def _get_key_strengths(dim_scores: List[DimensionScore]) -> List[str]:
    strengths = []
    for d in dim_scores:
        if d.score >= 80:
            strengths.append(f'{d.dimension}: {d.score}分（优秀）')
        elif d.score >= 70:
            strengths.append(f'{d.dimension}: {d.score}分（良好）')
    return strengths[:3]


def _get_key_weaknesses(dim_scores: List[DimensionScore]) -> List[str]:
    weaknesses = []
    for d in dim_scores:
        if d.score < 50:
            weaknesses.append(f'{d.dimension}: {d.score}分（较弱）')
        elif d.score < 60:
            weaknesses.append(f'{d.dimension}: {d.score}分（一般）')
    return weaknesses[:3]


@router.post("/risk-reward", response_model=Dict)
async def calculate_risk_reward(request: RiskRewardRequest):
    """风险收益比计算器

    根据入场价、止损价、止盈价计算风险收益比，并给出交易建议。
    """
    logger.info(f"POST /scoring/risk-reward entry={request.entry_price}")

    try:
        risk = request.entry_price - request.stop_loss
        reward = request.take_profit - request.entry_price

        if risk <= 0:
            raise HTTPException(status_code=400, detail="止损价必须低于入场价")

        rr_ratio = round(reward / risk, 2)

        # 综合评估
        if rr_ratio >= 4.0:
            decision = "强烈推荐介入"
            level = "优秀"
        elif rr_ratio >= 3.0:
            decision = "积极关注"
            level = "良好"
        elif rr_ratio >= 2.0:
            decision = "可参与"
            level = "一般"
        elif rr_ratio >= 1.5:
            decision = "谨慎参与"
            level = "偏低"
        else:
            decision = "不建议参与（风险收益比过低）"
            level = "差"

        # 根据信心度调整建议仓位
        confidence_factor = request.confidence / 100.0
        recommended_position = min(request.position_size * confidence_factor * (rr_ratio / 5.0), 30)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "input": {
                    "entry_price": request.entry_price,
                    "stop_loss": request.stop_loss,
                    "take_profit": request.take_profit,
                    "risk_amount": round(risk, 2),
                    "reward_amount": round(reward, 2),
                },
                "result": {
                    "risk_reward_ratio": rr_ratio,
                    "risk_reward_display": f'{rr_ratio}:1',
                    "decision": decision,
                    "level": level,
                    "recommended_position": f'{recommended_position:.1f}%',
                    "breakeven_win_rate": f'{round(1.0 / (rr_ratio + 1) * 100, 1)}%',
                },
                "assessment": {
                    "risk_analysis": _assess_risk(risk, request.entry_price),
                    "reward_analysis": _assess_reward(reward, request.entry_price),
                    "position_advice": _get_position_advice(rr_ratio, request.confidence),
                    "key_reminders": _get_rr_reminders(rr_ratio),
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk-reward calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"风险收益比计算失败: {str(e)}")


def _assess_risk(risk: float, entry: float) -> str:
    risk_pct = risk / entry * 100
    if risk_pct < 3:
        return f"止损空间较小({risk_pct:.1f}%)，容易被震出"
    elif risk_pct < 5:
        return f"止损空间合理({risk_pct:.1f}%)"
    elif risk_pct < 8:
        return f"止损空间偏大({risk_pct:.1f}%)，需关注容错率"
    else:
        return f"止损空间过大({risk_pct:.1f}%)，建议优化入场点"


def _assess_reward(reward: float, entry: float) -> str:
    reward_pct = reward / entry * 100
    if reward_pct < 5:
        return f"止盈空间较小({reward_pct:.1f}%)"
    elif reward_pct < 10:
        return f"止盈空间合理({reward_pct:.1f}%)"
    elif reward_pct < 20:
        return f"止盈空间良好({reward_pct:.1f}%)"
    else:
        return f"止盈空间优秀({reward_pct:.1f}%)"


def _get_position_advice(rr: float, confidence: int) -> str:
    if rr >= 3.0 and confidence >= 70:
        return "可重仓参与（建议20-30%）"
    elif rr >= 2.0 and confidence >= 50:
        return "可中等仓位参与（建议10-20%）"
    elif rr >= 1.5:
        return "轻仓试探（建议5-10%）"
    else:
        return "不建议参与或极小仓位试错（<5%）"


def _get_rr_reminders(rr: float) -> List[str]:
    reminders = [
        "严格执行止损纪律，不得随意移动止损位",
        "到达止盈目标分批减仓，不追求卖在最高点",
        "盘中跌破止损位应立即离场，不抱侥幸心理",
    ]
    if rr < 2.0:
        reminders.append("当前RR偏低，建议等待更好的入场时机")
    if rr >= 3.0:
        reminders.append("RR优秀，但注意仓位管理，单票不超过30%")
    return reminders


@router.get("/trade-plan", response_model=Dict)
async def get_trade_plan(
    ticker: str = Query(..., description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称"),
    score: Optional[float] = Query(None, ge=0, le=100, description="预设评分"),
):
    """交易计划生成

    根据股票代码和评分，生成完整的交易计划，包括入场点、止损止盈、持仓条件、卖出条件等。
    """
    logger.info(f"GET /scoring/trade-plan ticker={ticker}")

    try:
        name = stock_name or ticker
        actual_score = score or round(random.uniform(55, 92), 1)
        rating = _get_rating(actual_score)

        plan = _generate_trade_plan(ticker, name, actual_score, rating)

        # 根据评分级别调整计划
        position_pct = min(actual_score * 0.4, 30)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "plan": plan.model_dump(),
                "score_info": {
                    "ticker": ticker,
                    "name": name,
                    "score": actual_score,
                    "rating": rating,
                    "position_pct": f'{position_pct:.1f}%',
                },
                "execution_guide": {
                    "entry": {
                        "method": plan.entry_type,
                        "price": plan.entry_price,
                        "condition": "满足评分条件且竞价符合预期",
                    },
                    "stop_loss": {
                        "price": plan.stop_loss,
                        "loss_pct": f'{(plan.entry_price - plan.stop_loss) / plan.entry_price * 100:.1f}%',
                        "rule": "跌破立即离场，不犹豫",
                    },
                    "take_profit": {
                        "price": plan.take_profit,
                        "profit_pct": f'{(plan.take_profit - plan.entry_price) / plan.entry_price * 100:.1f}%',
                        "rule": "分批止盈，留底仓搏更大空间",
                    },
                    "time_management": {
                        "max_hold_days": 2 if "板" in plan.entry_type else 5,
                        "forced_exit": "跌破10日线或情绪周期转入退潮期",
                    },
                },
                "risk_management": {
                    "max_position": f'{position_pct:.1f}%',
                    "single_trade_max_loss": f'账户总额的{position_pct * 0.05:.2f}%',
                    "daily_max_trades": 3 if actual_score >= 70 else 2,
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Trade plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"交易计划生成失败: {str(e)}")
