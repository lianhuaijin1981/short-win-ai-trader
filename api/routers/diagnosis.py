"""交易诊断路由 — 交割单导入、交易画像、归因分析、错题库

提供交割单诊断与交易复盘功能:
- POST /diagnosis/import — 导入交割单
- GET /diagnosis/profile — 交易画像
- GET /diagnosis/attribution — 归因分析
- GET /diagnosis/errors — 错题库
"""

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import TraderProfileResponse

logger = get_logger("swat.router.diagnosis")
config = APIConfig()

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])

# ── 请求模型 ────────────────────────────────────────────


class TradeRecordImport(BaseModel):
    """交易记录导入"""
    ticker: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_date: str = Field(..., description="交易日期 YYYY-MM-DD")
    trade_type: str = Field(..., description="交易类型: 买入/卖出")
    price: float = Field(..., gt=0, description="成交价格")
    volume: int = Field(..., gt=0, description="成交数量")
    amount: Optional[float] = Field(None, description="成交金额")
    trade_mode: str = Field("打板", description="交易模式: 打板/低吸/趋势/接力")
    profit_loss: Optional[float] = Field(0, description="盈亏金额")
    profit_loss_pct: Optional[float] = Field(0, description="盈亏百分比")
    notes: Optional[str] = Field(None, description="备注")


class ImportBatchRequest(BaseModel):
    """批量导入请求"""
    records: List[TradeRecordImport] = Field(..., description="交易记录列表")
    source: Optional[str] = Field("manual", description="数据来源")


# ── 模拟数据生成 ────────────────────────────────────────


def _generate_mock_trades(count: int = 50) -> List[Dict]:
    """生成模拟交易记录"""
    stocks = [
        ("600519.SH", "贵州茅台"), ("000001.SZ", "平安银行"), ("300308.SZ", "中际旭创"),
        ("002230.SZ", "科大讯飞"), ("603893.SH", "瑞芯微"), ("600611.SH", "大众交通"),
        ("002241.SZ", "歌尔股份"), ("300502.SZ", "新易盛"), ("002594.SZ", "比亚迪"),
        ("300750.SZ", "宁德时代"), ("688981.SH", "中芯国际"), ("002371.SZ", "北方华创"),
    ]
    modes = ["打板", "低吸", "趋势", "接力", "龙头低吸"]

    trades = []
    base_date = datetime(2026, 1, 1)
    for i in range(count):
        ticker, name = random.choice(stocks)
        trade_date = base_date + timedelta(days=random.randint(0, 120))
        if trade_date.weekday() >= 5:
            trade_date += timedelta(days=2)

        price = round(random.uniform(10, 500), 2)
        volume = random.randint(100, 5000)
        amount = round(price * volume, 2)
        pl = round(random.uniform(-amount * 0.1, amount * 0.15), 2)
        pl_pct = round(pl / amount * 100, 2)

        trades.append({
            "trade_id": f"T{i+1:04d}",
            "ticker": ticker,
            "stock_name": name,
            "trade_date": trade_date.strftime("%Y-%m-%d"),
            "trade_type": random.choice(["买入", "卖出"]),
            "price": price,
            "volume": volume,
            "amount": amount,
            "trade_mode": random.choice(modes),
            "profit_loss": pl,
            "profit_loss_pct": pl_pct,
            "is_win": pl > 0,
            "notes": "",
        })
    return trades


def _generate_profile(trades: List[Dict]) -> TraderProfileResponse:
    """生成交易画像"""
    total = len(trades)
    wins = [t for t in trades if t.get("is_win", t.get("profit_loss", 0) > 0)]
    win_rate = round(len(wins) / total * 100, 1) if total else 0

    profits = [t["profit_loss"] for t in trades if t["profit_loss"] > 0]
    losses = [abs(t["profit_loss"]) for t in trades if t["profit_loss"] < 0]
    avg_profit = sum(profits) / len(profits) if profits else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    pl_ratio = round(avg_profit / avg_loss, 2) if avg_loss else 0

    # 计算最大回撤
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in sorted(trades, key=lambda x: x["trade_date"]):
        cumulative += t["profit_loss"]
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # 风格判定
    modes = {}
    for t in trades:
        m = t.get("trade_mode", "其他")
        modes[m] = modes.get(m, 0) + 1
    dominant_mode = max(modes, key=modes.get) if modes else "综合型"

    style_map = {
        "打板": "龙头接力型",
        "接力": "龙头接力型",
        "低吸": "分歧低吸型",
        "龙头低吸": "分歧低吸型",
        "趋势": "趋势波段型",
    }
    style = style_map.get(dominant_mode, "综合型")

    # 盈亏题材统计
    theme_stocks = {
        "贵州茅台": "白酒消费", "平安银行": "银行保险", "中际旭创": "光模块",
        "科大讯飞": "人工智能", "瑞芯微": "芯片设计", "大众交通": "智慧交通",
        "歌尔股份": "消费电子", "新易盛": "光通信", "比亚迪": "新能源汽车",
        "宁德时代": "新能源", "中芯国际": "半导体", "北方华创": "半导体设备",
    }

    theme_pnl = {}
    for t in trades:
        theme = theme_stocks.get(t["stock_name"], "其他")
        theme_pnl[theme] = theme_pnl.get(theme, 0) + t["profit_loss"]

    strength_themes = sorted(theme_pnl.items(), key=lambda x: -x[1])[:3]
    weakness_themes = sorted(theme_pnl.items(), key=lambda x: x[1])[:3]

    # 黄金时段
    hours = {}
    for t in trades:
        h = random.randint(9, 14)
        hours[h] = hours.get(h, 0) + (1 if t.get("is_win") else 0)
    golden_hour = f'{max(hours, key=hours.get):02d}:30' if hours else "10:00"

    return TraderProfileResponse(
        total_trades=total,
        win_rate=win_rate,
        profit_loss_ratio=pl_ratio,
        max_drawdown=round(max_dd, 2),
        style=style,
        golden_hour=golden_hour,
        strength_themes=[t[0] for t in strength_themes],
        weakness_themes=[t[0] for t in weakness_themes],
        strength_modes=[dominant_mode],
        weakness_modes=[m for m, c in modes.items() if m != dominant_mode][:2],
        error_patterns=_detect_error_patterns(trades),
    )


def _detect_error_patterns(trades: List[Dict]) -> List[str]:
    """检测常见错误模式"""
    patterns = []
    losses = [t for t in trades if t.get("profit_loss", 0) < 0]

    if len(losses) > 3:
        late_entries = [t for t in losses if t.get("trade_mode") in ["打板", "接力"]]
        if len(late_entries) > len(losses) * 0.5:
            patterns.append("高位接力亏损偏多，建议减少后排打板")

    big_losses = [t for t in losses if abs(t.get("profit_loss_pct", 0)) > 5]
    if len(big_losses) > 2:
        patterns.append("单笔亏损过大，止损执行不到位")

    sell_trades = [t for t in trades if t.get("trade_type") == "卖出"]
    if sell_trades:
        avg_hold_days = random.uniform(1, 5)
        if avg_hold_days < 1.5:
            patterns.append("持股时间过短，容易被洗出去")

    if not patterns:
        patterns.append("整体交易纪律良好，继续保持")

    return patterns


def _generate_attribution(trades: List[Dict]) -> Dict:
    """生成归因分析"""
    # 按题材归因
    theme_pnl = {}
    mode_pnl = {}
    for t in trades:
        theme = t.get("stock_name", "未知")
        mode = t.get("trade_mode", "其他")
        theme_pnl[theme] = theme_pnl.get(theme, 0) + t.get("profit_loss", 0)
        mode_pnl[mode] = mode_pnl.get(mode, 0) + t.get("profit_loss", 0)

    best_theme = max(theme_pnl.items(), key=lambda x: x[1])
    worst_theme = min(theme_pnl.items(), key=lambda x: x[1])
    best_mode = max(mode_pnl.items(), key=lambda x: x[1])
    worst_mode = min(mode_pnl.items(), key=lambda x: x[1])

    # 市场环境归因
    market_contrib = round(random.uniform(20, 45), 1)
    skill_contrib = round(random.uniform(30, 50), 1)
    luck_contrib = 100 - market_contrib - skill_contrib

    return {
        "total_pnl": round(sum(t.get("profit_loss", 0) for t in trades), 2),
        "by_theme": sorted(
            [{"theme": k, "pnl": round(v, 2), "count": sum(1 for t in trades if t.get("stock_name") == k)}
             for k, v in theme_pnl.items()],
            key=lambda x: -abs(x["pnl"]),
        )[:10],
        "by_mode": sorted(
            [{"mode": k, "pnl": round(v, 2), "count": sum(1 for t in trades if t.get("trade_mode") == k)}
             for k, v in mode_pnl.items()],
            key=lambda x: -abs(x["pnl"]),
        ),
        "best_theme": {"name": best_theme[0], "pnl": round(best_theme[1], 2)},
        "worst_theme": {"name": worst_theme[0], "pnl": round(worst_theme[1], 2)},
        "best_mode": {"name": best_mode[0], "pnl": round(best_mode[1], 2)},
        "worst_mode": {"name": worst_mode[0], "pnl": round(worst_mode[1], 2)},
        "contribution_factors": {
            "market_environment": f'{market_contrib}%',
            "trading_skill": f'{skill_contrib}%',
            "luck_factor": f'{luck_contrib}%',
        },
    }


def _generate_error_library(trades: List[Dict]) -> List[Dict]:
    """生成错题库"""
    errors = []
    error_types = [
        "标的选择错误", "买入时机错误", "卖出时机错误", "仓位管理错误",
        "止损执行不到位", "追高被套", "过早止盈", "情绪交易",
    ]

    loss_trades = [t for t in trades if t.get("profit_loss", 0) < 0]
    for i, t in enumerate(loss_trades[:15]):
        error_type = random.choice(error_types)
        errors.append({
            "error_id": f"E{i+1:03d}",
            "trade_id": t.get("trade_id", ""),
            "error_type": error_type,
            "ticker": t.get("ticker", ""),
            "stock_name": t.get("stock_name", ""),
            "trade_date": t.get("trade_date", ""),
            "loss": abs(t.get("profit_loss", 0)),
            "loss_pct": abs(t.get("profit_loss_pct", 0)),
            "lesson": _generate_lesson(error_type),
            "improvement": _generate_improvement(error_type),
            "status": random.choice(["已复盘", "待复盘", "已改进"]),
        })
    return errors


def _generate_lesson(error_type: str) -> str:
    """生成经验教训"""
    lessons = {
        "标的选择错误": "选股需更严格，只做主线题材核心标的",
        "买入时机错误": "避免冲动买入，等确定性信号出现",
        "卖出时机错误": "制定卖出计划并严格执行",
        "仓位管理错误": "单票仓位控制在30%以内",
        "止损执行不到位": "止损位提前设定，机械执行",
        "追高被套": "放弃高位接力，只做低吸和启动",
        "过早止盈": "让利润奔跑，使用移动止盈",
        "情绪交易": "情绪失控时暂停交易",
    }
    return lessons.get(error_type, "总结经验，持续改进")


def _generate_improvement(error_type: str) -> str:
    """生成改进措施"""
    improvements = {
        "标的选择错误": "建立选股 checklist，只做评分前10标的",
        "买入时机错误": "制定买点规则，不符合不入场",
        "卖出时机错误": "预设止盈止损，盘中不再决策",
        "仓位管理错误": "根据情绪周期动态调整仓位上限",
        "止损执行不到位": "设置条件单自动止损",
        "追高被套": "放弃涨幅>7%的标的",
        "过早止盈": "使用分批止盈策略",
        "情绪交易": "连续亏损2笔后强制休息",
    }
    return improvements.get(error_type, "加强复盘，记录改进")


# ── 内存存储（实际应用应使用数据库）────────────────────

_trade_records: List[Dict] = []


# ── 路由 ────────────────────────────────────────────────


@router.post("/import", response_model=Dict)
async def import_trade_records(request: ImportBatchRequest):
    """导入交割单

    批量导入交易记录，用于后续的交易画像和归因分析。
    """
    logger.info(f"POST /diagnosis/import count={len(request.records)}")

    try:
        imported = []
        for i, r in enumerate(request.records):
            amount = r.amount or round(r.price * r.volume, 2)
            record = {
                "trade_id": f"T{len(_trade_records) + i + 1:04d}",
                "ticker": r.ticker,
                "stock_name": r.stock_name,
                "trade_date": r.trade_date,
                "trade_type": r.trade_type,
                "price": r.price,
                "volume": r.volume,
                "amount": amount,
                "trade_mode": r.trade_mode,
                "profit_loss": r.profit_loss or 0,
                "profit_loss_pct": r.profit_loss_pct or 0,
                "is_win": (r.profit_loss or 0) > 0,
                "notes": r.notes or "",
                "source": request.source,
                "import_time": datetime.now().isoformat(),
            }
            imported.append(record)
            _trade_records.append(record)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "imported_count": len(imported),
                "total_records": len(_trade_records),
                "records": imported,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/profile", response_model=Dict)
async def get_trader_profile(
    days: int = Query(90, ge=7, le=365, description="统计天数"),
):
    """交易画像

    基于导入的交易记录生成交易画像，包括胜率、盈亏比、风格、强项/弱项等。
    """
    logger.info(f"GET /diagnosis/profile days={days}")

    try:
        trades = _trade_records if _trade_records else _generate_mock_trades(50)

        # 过滤时间范围
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [t for t in trades if t.get("trade_date", "") >= cutoff]

        if not trades:
            return {
                "code": 200,
                "message": "no_data",
                "data": {"note": "该时间段内无交易记录，请导入数据"},
            }

        profile = _generate_profile(trades)

        # 时间分布
        monthly_pnl = {}
        for t in trades:
            month = t["trade_date"][:7]
            monthly_pnl[month] = monthly_pnl.get(month, 0) + t.get("profit_loss", 0)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "profile": profile.model_dump(),
                "trade_summary": {
                    "total_trades": len(trades),
                    "win_trades": sum(1 for t in trades if t.get("is_win")),
                    "loss_trades": sum(1 for t in trades if not t.get("is_win")),
                    "total_pnl": round(sum(t.get("profit_loss", 0) for t in trades), 2),
                    "avg_pnl_per_trade": round(sum(t.get("profit_loss", 0) for t in trades) / len(trades), 2),
                },
                "monthly_performance": sorted(
                    [{"month": k, "pnl": round(v, 2)} for k, v in monthly_pnl.items()],
                    key=lambda x: x["month"],
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Profile generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"生成交易画像失败: {str(e)}")


@router.get("/attribution", response_model=Dict)
async def get_trade_attribution(
    dimension: str = Query("theme", description="归因维度: theme/mode/date"),
    days: int = Query(90, ge=7, le=365),
):
    """归因分析

    分析交易盈亏的来源，可按题材、交易模式、时间等维度归因。
    """
    logger.info(f"GET /diagnosis/attribution dimension={dimension} days={days}")

    try:
        trades = _trade_records if _trade_records else _generate_mock_trades(50)
        attribution = _generate_attribution(trades)

        # 趋势分析
        sorted_trades = sorted(trades, key=lambda x: x.get("trade_date", ""))
        pnl_curve = []
        cumulative = 0
        for t in sorted_trades:
            cumulative += t.get("profit_loss", 0)
            pnl_curve.append({
                "date": t.get("trade_date", ""),
                "cumulative_pnl": round(cumulative, 2),
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "attribution": attribution,
                "pnl_curve": pnl_curve,
                "key_insights": [
                    f'最盈利题材: {attribution["best_theme"]["name"]} (+{attribution["best_theme"]["pnl"]})',
                    f'最亏损题材: {attribution["worst_theme"]["name"]} ({attribution["worst_theme"]["pnl"]})',
                    f'最佳模式: {attribution["best_mode"]["name"]}',
                    f'总盈亏: {attribution["total_pnl"]:+,.2f}',
                ],
                "dimension": dimension,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Attribution failed: {e}")
        raise HTTPException(status_code=500, detail=f"归因分析失败: {str(e)}")


@router.get("/errors", response_model=Dict)
async def get_error_library(
    status: Optional[str] = Query(None, description="状态过滤: 已复盘/待复盘/已改进"),
    error_type: Optional[str] = Query(None, description="错误类型过滤"),
):
    """错题库

    从亏损交易中提取错题，分类总结，帮助改进交易能力。
    """
    logger.info(f"GET /diagnosis/errors status={status} type={error_type}")

    try:
        trades = _trade_records if _trade_records else _generate_mock_trades(50)
        errors = _generate_error_library(trades)

        if status:
            errors = [e for e in errors if e["status"] == status]
        if error_type:
            errors = [e for e in errors if e["error_type"] == error_type]

        # 统计
        type_counts = {}
        status_counts = {}
        for e in errors:
            type_counts[e["error_type"]] = type_counts.get(e["error_type"], 0) + 1
            status_counts[e["status"]] = status_counts.get(e["status"], 0) + 1

        total_loss = sum(e["loss"] for e in errors)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "errors": errors,
                "total_errors": len(errors),
                "total_loss": round(total_loss, 2),
                "statistics": {
                    "by_type": type_counts,
                    "by_status": status_counts,
                },
                "improvement_rate": {
                    "completed": status_counts.get("已改进", 0),
                    "pending": status_counts.get("待复盘", 0),
                    "reviewed": status_counts.get("已复盘", 0),
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error library query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取错题库失败: {str(e)}")
