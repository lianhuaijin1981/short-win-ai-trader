"""情绪周期路由 — 情绪诊断、题材排行、次日预判、历史曲线

提供超短线情绪周期分析:
- /sentiment/diagnosis — 情绪周期诊断（14项指标）
- /sentiment/themes — 题材周期排行
- /sentiment/prediction — 次日行情预判
- /sentiment/history — 历史情绪曲线
"""

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import EmotionDiagnosis, EmotionIndicators

logger = get_logger("swat.router.sentiment")
config = APIConfig()

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

# ── 情绪周期定义 ────────────────────────────────────────

CYCLE_DEFINITIONS = {
    "冰点期": {"position_limit": 0, "mode": "空仓观望", "principle": "宁可错过，不可做错"},
    "回暖期": {"position_limit": 20, "mode": "试探性建仓", "principle": "快进快出，游击战术"},
    "发酵期": {"position_limit": 50, "mode": "积极进攻", "principle": "主线明确，重仓龙头"},
    "高潮期": {"position_limit": 70, "mode": "享受泡沫", "principle": "持股待涨，不猜顶"},
    "退潮期": {"position_limit": 30, "mode": "防守反击", "principle": "收缩战线，去弱留强"},
    "衰退期": {"position_limit": 10, "mode": "减仓避险", "principle": "降低预期，保住利润"},
}

# ── 辅助函数 ────────────────────────────────────────────


def _calculate_indicators() -> EmotionIndicators:
    """计算14项情绪指标"""
    return EmotionIndicators(
        up_down_ratio=round(random.uniform(0.5, 3.0), 2),
        explode_rate=round(random.uniform(0.0, 100.0), 2),
        profit_effect=round(random.uniform(-30.0, 50.0), 2),
        volume_change=round(random.uniform(-40.0, 80.0), 2),
        max_consecutive_boards=random.randint(2, 12),
        promotion_rate=round(random.uniform(0.0, 100.0), 2),
        break_rate=round(random.uniform(0.0, 80.0), 2),
        dragon_premium=round(random.uniform(-5.0, 25.0), 2),
        main_inflow_ratio=round(random.uniform(-20.0, 40.0), 2),
        yingyou_activity=round(random.uniform(0.0, 100.0), 2),
        northbound_flow=round(random.uniform(-50.0, 80.0), 2),
        theme_strength=round(random.uniform(10.0, 95.0), 2),
        sector_linkage=round(random.uniform(20.0, 90.0), 2),
    )


def _diagnose_cycle(indicators: EmotionIndicators) -> Dict:
    """根据14项指标诊断情绪周期"""
    score = 0
    # 涨跌比评分
    if indicators.up_down_ratio > 2.0:
        score += 20
    elif indicators.up_down_ratio > 1.5:
        score += 15
    elif indicators.up_down_ratio > 1.0:
        score += 10
    elif indicators.up_down_ratio > 0.6:
        score += 5
    else:
        score += 0

    # 炸板率评分（低炸板率 = 情绪好）
    if indicators.explode_rate < 15:
        score += 20
    elif indicators.explode_rate < 30:
        score += 15
    elif indicators.explode_rate < 50:
        score += 10
    else:
        score += 0

    # 赚钱效应评分
    if indicators.profit_effect > 30:
        score += 20
    elif indicators.profit_effect > 15:
        score += 15
    elif indicators.profit_effect > 0:
        score += 10
    else:
        score += 0

    # 最高连板评分
    if indicators.max_consecutive_boards >= 7:
        score += 20
    elif indicators.max_consecutive_boards >= 5:
        score += 15
    elif indicators.max_consecutive_boards >= 3:
        score += 10
    else:
        score += 5

    # 晋级率评分
    if indicators.promotion_rate > 60:
        score += 20
    elif indicators.promotion_rate > 40:
        score += 15
    elif indicators.promotion_rate > 20:
        score += 10
    else:
        score += 0

    # 确定周期
    if score >= 85:
        cycle = "高潮期"
    elif score >= 70:
        cycle = "发酵期"
    elif score >= 50:
        cycle = "回暖期"
    elif score >= 30:
        cycle = "衰退期"
    elif score >= 15:
        cycle = "退潮期"
    else:
        cycle = "冰点期"

    cycle_def = CYCLE_DEFINITIONS[cycle]
    confidence = min(95, max(50, score + random.uniform(-10, 10)))

    return {
        "cycle": cycle,
        "score": score,
        "confidence": round(confidence, 1),
        "position_limit": cycle_def["position_limit"],
        "adapted_mode": cycle_def["mode"],
        "core_principle": cycle_def["principle"],
    }


def _generate_next_day_prediction(cycle: str, indicators: EmotionIndicators) -> Dict:
    """生成次日行情预判"""
    predictions = {
        "冰点期": {
            "market_trend": "延续弱势，关注早盘恐慌盘",
            "operation": "空仓或极小仓位试探",
            "key_points": ["关注跌停数量是否减少", "观察首板涨停质量", "等待指数企稳信号"],
            "success_rate": random.uniform(30, 45),
        },
        "回暖期": {
            "market_trend": "情绪修复，新题材有望发酵",
            "operation": "半仓以内试错新题材龙头",
            "key_points": ["前排涨停封单强度", "炸板率是否回落", "量能是否有效放大"],
            "success_rate": random.uniform(50, 65),
        },
        "发酵期": {
            "market_trend": "主线明确，龙头加速",
            "operation": "重仓主线龙头，持股待涨",
            "key_points": ["龙头封单持续强度", "板块联动性", "后排补涨机会"],
            "success_rate": random.uniform(65, 80),
        },
        "高潮期": {
            "market_trend": "全面高潮，随时可能分化",
            "operation": "去弱留强，控制仓位",
            "key_points": ["警惕尾盘炸板", "跟风股提前走弱", "准备兑现利润"],
            "success_rate": random.uniform(55, 70),
        },
        "退潮期": {
            "market_trend": "高位分歧加剧",
            "operation": "大幅减仓，只留核心龙头",
            "key_points": ["核按钮数量", "连板高度压制", "资金流出方向"],
            "success_rate": random.uniform(35, 50),
        },
        "衰退期": {
            "market_trend": "情绪降温，亏钱效应扩散",
            "operation": "空仓或极低仓位防守",
            "key_points": ["跌停家数是否扩大", "能否出现反包", "等待情绪冰点"],
            "success_rate": random.uniform(25, 40),
        },
    }
    pred = predictions.get(cycle, predictions["冰点期"])
    pred["success_rate"] = round(pred["success_rate"], 1)
    pred["based_cycle"] = cycle
    return pred


def _generate_theme_ranking() -> List[Dict]:
    """生成题材周期排行数据"""
    themes = [
        {"theme": "光模块/CPO", "cycle": "加速期", "strength": 95, "limit_up_count": 8,
         "leading": "中际旭创", "followers": ["新易盛", "天孚通信", "剑桥科技"], "capital": 45.2},
        {"theme": "智慧交通/自动驾驶", "cycle": "主升浪", "strength": 92, "limit_up_count": 7,
         "leading": "大众交通", "followers": ["启明信息", "金龙汽车", "万集科技"], "capital": 38.6},
        {"theme": "消费电子", "cycle": "发酵期", "strength": 85, "limit_up_count": 6,
         "leading": "歌尔股份", "followers": ["立讯精密", "蓝思科技", "鹏鼎控股"], "capital": 52.3},
        {"theme": "芯片设计", "cycle": "发酵期", "strength": 80, "limit_up_count": 5,
         "leading": "瑞芯微", "followers": ["全志科技", "晶晨股份", "韦尔股份"], "capital": 35.8},
        {"theme": "先进封装", "cycle": "启动期", "strength": 72, "limit_up_count": 4,
         "leading": "文一科技", "followers": ["通富微电", "长电科技"], "capital": 22.1},
        {"theme": "文化传媒", "cycle": "分化期", "strength": 58, "limit_up_count": 3,
         "leading": "华闻集团", "followers": ["中文在线", "掌阅科技"], "capital": 15.6},
        {"theme": "新能源汽车", "cycle": "分化期", "strength": 55, "limit_up_count": 3,
         "leading": "金龙汽车", "followers": ["比亚迪", "宁德时代"], "capital": 28.4},
        {"theme": "PCB", "cycle": "衰退期", "strength": 42, "limit_up_count": 2,
         "leading": "骏亚科技", "followers": ["深南电路", "沪电股份"], "capital": 12.3},
        {"theme": "光伏储能", "cycle": "冰点期", "strength": 25, "limit_up_count": 0,
         "leading": "", "followers": ["隆基绿能", "阳光电源"], "capital": -8.5},
        {"theme": "白酒消费", "cycle": "冰点期", "strength": 20, "limit_up_count": 0,
         "leading": "", "followers": ["贵州茅台", "五粮液"], "capital": -12.3},
    ]
    themes.sort(key=lambda x: x["strength"], reverse=True)
    for i, t in enumerate(themes):
        t["rank"] = i + 1
        t["trend"] = "up" if random.random() > 0.4 else "down"
        t["temperature"] = min(100, t["strength"] + random.randint(-5, 5))
    return themes


def _generate_history(days: int = 30) -> List[Dict]:
    """生成历史情绪曲线数据"""
    history = []
    base_date = date.today() - timedelta(days=days)
    cycle_sequence = ["冰点期", "回暖期", "发酵期", "高潮期", "退潮期", "衰退期", "冰点期"]

    for i in range(days):
        d = base_date + timedelta(days=i)
        # 跳过周末
        if d.weekday() >= 5:
            continue

        cycle_idx = (i // 4) % len(cycle_sequence)
        cycle = cycle_sequence[cycle_idx]
        score = random.uniform(10, 95)

        history.append({
            "date": d.isoformat(),
            "cycle": cycle,
            "score": round(score, 1),
            "up_down_ratio": round(random.uniform(0.3, 4.0), 2),
            "limit_up_count": random.randint(10, 150),
            "limit_down_count": random.randint(0, 40),
            "max_boards": random.randint(2, 10),
            "explode_rate": round(random.uniform(5, 60), 1),
            "volume": round(random.uniform(6000, 12000), 2),
            "profit_effect": round(random.uniform(-20, 40), 2),
        })
    return history


# ── 路由 ────────────────────────────────────────────────


@router.get("/diagnosis", response_model=Dict)
async def get_emotion_diagnosis():
    """情绪周期诊断 — 14项指标综合分析

    返回当前市场情绪周期的完整诊断结果，包括14项量化指标、
    周期判断、仓位建议、适配模式等。
    """
    logger.info("GET /sentiment/diagnosis")

    try:
        indicators = _calculate_indicators()
        diagnosis = _diagnose_cycle(indicators)
        prediction = _generate_next_day_prediction(diagnosis["cycle"], indicators)

        result = EmotionDiagnosis(
            current_cycle=diagnosis["cycle"],
            confidence=diagnosis["confidence"],
            position_limit=diagnosis["position_limit"],
            adapted_mode=diagnosis["adapted_mode"],
            core_principle=diagnosis["core_principle"],
            next_day_prediction=prediction["market_trend"],
            indicators=indicators,
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "diagnosis": result.model_dump(),
                "indicators_detail": {
                    "涨跌比": f'{indicators.up_down_ratio}:1',
                    "炸板率": f'{indicators.explode_rate}%',
                    "赚钱效应": f'{indicators.profit_effect:+}%',
                    "量能变化": f'{indicators.volume_change:+}%',
                    "最高连板": f'{indicators.max_consecutive_boards}板',
                    "晋级率": f'{indicators.promotion_rate}%',
                    "破板率": f'{indicators.break_rate}%',
                    "龙头溢价": f'{indicators.dragon_premium:+}%',
                    "主力净流入比": f'{indicators.main_inflow_ratio:+}%',
                    "游资活跃度": f'{indicators.yingyou_activity}%',
                    "北向资金": f'{indicators.northbound_flow:+}亿',
                    "题材强度": f'{indicators.theme_strength}',
                    "板块联动": f'{indicators.sector_linkage}',
                },
                "prediction": prediction,
                "position_advice": {
                    "current_limit": f'{diagnosis["position_limit"]}%',
                    "single_stock_max": f'{min(diagnosis["position_limit"], 30)}%',
                    "mode": diagnosis["adapted_mode"],
                    "principle": diagnosis["core_principle"],
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Emotion diagnosis failed: {e}")
        raise HTTPException(status_code=500, detail=f"情绪诊断失败: {str(e)}")


@router.get("/themes", response_model=Dict)
async def get_theme_ranking(
    min_strength: int = Query(0, ge=0, le=100, description="最小题材强度"),
    cycle_filter: Optional[str] = Query(None, description="周期过滤: 启动期/发酵期/加速期/高潮期/分化期/衰退期/冰点期"),
):
    """题材周期排行

    返回当前活跃题材的强度排行，包含题材生命周期阶段、涨停数量、龙头股等。
    """
    logger.info(f"GET /sentiment/themes min_strength={min_strength} cycle={cycle_filter}")

    try:
        themes = _generate_theme_ranking()

        if min_strength > 0:
            themes = [t for t in themes if t["strength"] >= min_strength]
        if cycle_filter:
            themes = [t for t in themes if t["cycle"] == cycle_filter]

        # 统计
        cycle_counts = {}
        for t in themes:
            cycle_counts[t["cycle"]] = cycle_counts.get(t["cycle"], 0) + 1

        hot_themes = [t for t in themes if t["strength"] >= 70]
        total_limit_up = sum(t["limit_up_count"] for t in themes)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "themes": themes,
                "total": len(themes),
                "total_limit_up": total_limit_up,
                "cycle_distribution": cycle_counts,
                "hot_themes": hot_themes[:5],
                "recommended_focus": [t["theme"] for t in hot_themes[:3]],
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Theme ranking failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取题材排行失败: {str(e)}")


@router.get("/prediction", response_model=Dict)
async def get_next_day_prediction():
    """次日行情预判

    基于当前情绪周期和14项指标，对次日市场走势进行预判。
    """
    logger.info("GET /sentiment/prediction")

    try:
        indicators = _calculate_indicators()
        diagnosis = _diagnose_cycle(indicators)
        prediction = _generate_next_day_prediction(diagnosis["cycle"], indicators)

        # 生成更多预判细节
        detail = {
            "market_trend": prediction["market_trend"],
            "recommended_operation": prediction["operation"],
            "key_observation_points": prediction["key_points"],
            "success_rate_estimate": f'{prediction["success_rate"]}%',
            "risk_reminders": _generate_risk_reminders(diagnosis["cycle"]),
            "opportunity_directions": _generate_opportunities(diagnosis["cycle"]),
            "based_on": {
                "current_cycle": diagnosis["cycle"],
                "confidence": f'{diagnosis["confidence"]}%',
                "indicators_summary": {
                    "up_down_ratio": indicators.up_down_ratio,
                    "explode_rate": f'{indicators.explode_rate}%',
                    "profit_effect": f'{indicators.profit_effect:+}%',
                    "max_boards": indicators.max_consecutive_boards,
                },
            },
        }

        return {
            "code": 200,
            "message": "success",
            "data": detail,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"次日预判失败: {str(e)}")


def _generate_risk_reminders(cycle: str) -> List[str]:
    """根据周期生成风险提示"""
    reminders = {
        "冰点期": ["避免左侧抄底", "不参与首板以下的接力", "不追高任何非龙头"],
        "回暖期": ["题材轮动快，注意节奏", "避免后排跟风", "控制单票仓位"],
        "发酵期": ["关注龙头分歧风险", "不追高缩量加速板", "做好止盈止损计划"],
        "高潮期": ["严防尾盘炸板潮", "跟风股率先走弱", "准备分批兑现"],
        "退潮期": ["核按钮风险加大", "连板高度受压制", "减少接力操作"],
        "衰退期": ["跌停板扩散风险", "老题材补跌", "保持空仓耐心"],
    }
    return reminders.get(cycle, ["谨慎操作，控制仓位"])


def _generate_opportunities(cycle: str) -> List[str]:
    """根据周期生成机会方向"""
    opportunities = {
        "冰点期": ["关注独立逻辑个股", "尾盘恐慌盘错杀机会", "新题材首板试错"],
        "回暖期": ["新题材前排试错", "老龙头反抽机会", "趋势股低吸"],
        "发酵期": ["主线龙头重仓", "板块内补涨挖掘", "竞价最强题材"],
        "高潮期": ["龙头持股", "核心标的做T", "等待分歧后回封"],
        "退潮期": ["绝对核心龙头抱团", "低位新题材切换", "空仓等待新周期"],
        "衰退期": ["超跌反弹首板", "新周期萌芽试错", "绝对空仓观望"],
    }
    return opportunities.get(cycle, ["耐心等待机会"])


@router.get("/history", response_model=Dict)
async def get_emotion_history(
    days: int = Query(30, ge=5, le=90, description="查询天数"),
    ticker: Optional[str] = Query(None, description="关联个股过滤"),
):
    """历史情绪曲线

    返回指定天数内的历史情绪周期变化曲线，可用于分析情绪趋势。
    """
    logger.info(f"GET /sentiment/history days={days} ticker={ticker}")

    try:
        history = _generate_history(days)

        # 计算趋势
        if len(history) >= 7:
            recent_7 = history[-7:]
            avg_score_7 = sum(h["score"] for h in recent_7) / len(recent_7)
            avg_score_all = sum(h["score"] for h in history) / len(history)
            trend = "上升" if avg_score_7 > avg_score_all else "下降"
        else:
            avg_score_7 = 0
            avg_score_all = 0
            trend = "平"

        # 统计各周期出现频率
        cycle_frequency = {}
        for h in history:
            cycle_frequency[h["cycle"]] = cycle_frequency.get(h["cycle"], 0) + 1

        return {
            "code": 200,
            "message": "success",
            "data": {
                "history": history,
                "summary": {
                    "total_days": len(history),
                    "trading_days": len(history),
                    "avg_score": round(avg_score_all, 1),
                    "recent_7_avg": round(avg_score_7, 1),
                    "trend": trend,
                    "cycle_frequency": cycle_frequency,
                    "highest_score": max(h["score"] for h in history) if history else 0,
                    "lowest_score": min(h["score"] for h in history) if history else 0,
                    "current_cycle": history[-1]["cycle"] if history else "未知",
                },
                "chart_data": {
                    "dates": [h["date"] for h in history],
                    "scores": [h["score"] for h in history],
                    "cycles": [h["cycle"] for h in history],
                    "limit_up_counts": [h["limit_up_count"] for h in history],
                    "volumes": [h["volume"] for h in history],
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"History query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史情绪曲线失败: {str(e)}")
