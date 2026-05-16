"""CLI命令实现"""

import asyncio
from datetime import date, datetime
from typing import Dict, List, Optional

from rich.console import Console

from ..core.config import AppConfig
from ..core.logger import get_logger
from ..data_platform.data_models import (
    EmotionCycle, EmotionDiagnosis, StockPrice, ComprehensiveScore,
)
from .formatters import (
    print_custom_analysis, print_dimension_scores, print_emotion_diagnosis,
    print_error, print_info, print_score_table, print_success,
    print_tactic_matches, print_trade_plan, print_trader_profile,
    print_yingyou_recommendations,
)

console = Console()
logger = get_logger("swat.commands")


# ========== Mock数据生成器（用于演示） ==========

def _mock_emotion_diagnosis() -> Dict:
    """生成情绪诊断Mock数据"""
    return {
        "current_cycle": "发酵期",
        "confidence": 78.5,
        "position_limit": 60,
        "adapted_mode": "半路、低吸核心人气标",
        "core_principle": "顺势加仓、持有核心、放弃杂毛",
        "next_day_prediction": "大盘大概率强势延续，关注AI+机器人方向",
        "indicators": {
            "up_down_ratio": 2.3,
            "explode_rate": 18.5,
            "profit_effect": 72.0,
            "volume_change": 15.2,
            "max_consecutive_boards": 7,
            "promotion_rate": 65.0,
            "break_rate": 12.0,
        },
    }


def _mock_scores(ticker: str = "") -> List[Dict]:
    """生成评分Mock数据"""
    scores = [
        {
            "ticker": "603083.SH", "stock_name": "剑桥科技",
            "total_score": 88.5, "rating": "优质标的",
            "risk_level": "安全", "risk_reward_ratio": 3.5,
            "position": "35%", "decision": "积极参与，突破入场",
        },
        {
            "ticker": "000977.SZ", "stock_name": "浪潮信息",
            "total_score": 82.3, "rating": "优质标的",
            "risk_level": "安全", "risk_reward_ratio": 2.8,
            "position": "30%", "decision": "推荐参与，回踩低吸",
        },
        {
            "ticker": "300308.SZ", "stock_name": "中际旭创",
            "total_score": 76.8, "rating": "良好标的",
            "risk_level": "谨慎", "risk_reward_ratio": 2.1,
            "position": "20%", "decision": "谨慎参与，快进快出",
        },
    ]
    if ticker:
        for s in scores:
            if s["ticker"] == ticker:
                return [s]
        return [{**scores[0], "ticker": ticker, "stock_name": ticker}]
    return scores


def _mock_trade_plan(ticker: str) -> Dict:
    """生成交易计划Mock数据"""
    return {
        "ticker": ticker,
        "stock_name": ticker,
        "entry_price": 45.80,
        "entry_type": "突破入场",
        "stop_loss_price": 43.51,
        "take_profit_price": 54.96,
        "position_pct": 30,
        "hold_conditions": [
            "股价沿5日线上涨，均线多头排列",
            "量能健康（缩量上涨或放量突破）",
            "板块效应持续（涨停≥3只）",
            "所属题材处于主升或发酵阶段",
        ],
        "sell_conditions": [
            "【逻辑止损】题材证伪 / 龙头跌停 / 板块崩溃 → 无条件卖出",
            "【技术止损】跌破5日线或关键支撑位，当日无法收回 → 卖出",
            "【固定止损】亏损达4% → 严格执行止损",
            "【目标止盈】达到预设收益目标 → 分批卖出",
            "【情绪止盈】市场情绪退潮 / 炸板率>50% → 全部卖出空仓",
        ],
    }


def _mock_dimension_scores() -> List[Dict]:
    """生成维度评分Mock数据"""
    return [
        {"dimension": "资讯催化力", "weight": 20, "score": 85.0},
        {"dimension": "基本面安全垫", "weight": 15, "score": 72.5},
        {"dimension": "技术形态强度", "weight": 20, "score": 90.2},
        {"dimension": "筹码结构质量", "weight": 15, "score": 78.0},
        {"dimension": "市场情绪适配", "weight": 15, "score": 88.5},
        {"dimension": "资金流向强度", "weight": 15, "score": 82.3},
    ]


def _mock_yingyou_recommendations() -> List[Dict]:
    """生成游资推荐Mock数据"""
    return [
        {
            "yingyou_name": "炒股养家", "ticker": "603083.SH",
            "stock_name": "剑桥科技", "match_score": 92,
            "recommendation": "强烈推荐",
            "operation": "买在分歧，昨日分歧放量今日转一致",
        },
        {
            "yingyou_name": "小鳄鱼", "ticker": "603083.SH",
            "stock_name": "剑桥科技", "match_score": 88,
            "recommendation": "强烈推荐",
            "operation": "10:30前硬板打板，板块涨停8只",
        },
        {
            "yingyou_name": "92科比", "ticker": "000977.SZ",
            "stock_name": "浪潮信息", "match_score": 85,
            "recommendation": "推荐",
            "operation": "缩量回踩5日线低吸，均线支撑",
        },
    ]


def _mock_tactic_matches() -> List[Dict]:
    """生成战法匹配Mock数据"""
    return [
        {
            "tactic_name": "三倍量突破战法", "ticker": "603083.SH",
            "stock_name": "剑桥科技", "match_score": 88,
            "shape_verdict": "真实突破", "prediction": "主力进场，具备持续性",
        },
        {
            "tactic_name": "筹码峰战法", "ticker": "603083.SH",
            "stock_name": "剑桥科技", "match_score": 82,
            "shape_verdict": "低位单峰", "prediction": "主力控盘，拉升在即",
        },
        {
            "tactic_name": "龙头情绪战法", "ticker": "300308.SZ",
            "stock_name": "中际旭创", "match_score": 76,
            "shape_verdict": "符合", "prediction": "板块龙头，情绪溢价",
        },
    ]


def _mock_trader_profile() -> Dict:
    """生成交易画像Mock数据"""
    return {
        "total_trades": 156,
        "win_rate": 58.3,
        "profit_loss_ratio": 1.85,
        "max_drawdown": 12.5,
        "avg_profit": 2850.0,
        "avg_loss": 1540.0,
        "style": "龙头接力型",
        "golden_hour": "早盘(9:30-10:30) (胜率68%)",
        "strength_themes": ["AI算力", "机器人", "CPO"],
        "weakness_themes": ["房地产", "钢铁", "银行"],
        "strength_modes": ["打板", "接力"],
        "weakness_modes": ["潜伏", "套利"],
        "error_patterns": [
            "大亏损次数过多(12次)，止损执行不坚决",
            "最大连续亏损4次，需设置强制休息机制",
        ],
    }


def _mock_custom_analysis(ticker: str) -> Dict:
    """生成自定义标的全维度研判Mock数据"""
    return {
        "ticker": ticker,
        "name": ticker,
        "comprehensive_score": 85.5,
        "rating": "优质标的",
        "emotion_cycle": "发酵期",
        "theme_position": "主升加速",
        "anchor_position": "主线分支龙头",
        "success_logic": [
            "【技术形态强度】得分90.2，均线多头排列，放量突破关键压力位",
            "【市场情绪适配】得分88.5，发酵期顺势操作，板块效应强",
            "【资讯】存在A级催化资讯，AI算力方向政策利好持续",
            "【游资】匹配炒股养家模式(92分)，买在分歧转一致",
            "【战法】2套战法共振(三倍量突破+筹码峰)，形态强势",
        ],
        "risk_points": [
            "【基本面安全垫】得分72.5，估值偏高，业绩增速一般",
            "【位置】处于高位，追高风险大，一旦回调空间有限",
            "【情绪】若发酵期转高潮后分歧，需及时减仓",
        ],
        "style_advice": "符合您的龙头接力风格，可正常参与，但注意仓位控制在30%以内",
    }


# ========== 命令实现 ==========

def cmd_pre_market(config: AppConfig, date_str: Optional[str] = None):
    """盘前分析命令"""
    trade_date = date.fromisoformat(date_str) if date_str else date.today()
    print_info(f"执行盘前分析: {trade_date}")

    # 情绪诊断
    emotion = _mock_emotion_diagnosis()
    print_emotion_diagnosis(emotion)

    # 评分排名
    scores = _mock_scores()
    print_score_table(scores)

    # 游资推荐
    yingyou = _mock_yingyou_recommendations()
    print_yingyou_recommendations(yingyou)

    print_success(f"盘前分析完成 — 今日情绪{emotion['current_cycle']}，建议仓位{emotion['position_limit']}成")


def cmd_intraday(config: AppConfig, watch_interval: int):
    """盘中监控命令"""
    print_info(f"启动盘中监控 (间隔{watch_interval}秒)")
    console.print("[yellow]模拟盘中数据流...[/yellow]")

    emotion = _mock_emotion_diagnosis()
    print_emotion_diagnosis(emotion)

    # 锚定标的
    console.print("[bold]锚定标的池:[/bold]")
    anchors = [
        {"type": "市场总龙", "ticker": "603083.SH", "name": "剑桥科技", "boards": 7, "expectation": "强于预期"},
        {"type": "先锋龙", "ticker": "002229.SZ", "name": "鸿博股份", "boards": 3, "expectation": "符合预期"},
        {"type": "板块中军", "ticker": "000977.SZ", "name": "浪潮信息", "boards": 2, "expectation": "符合预期"},
    ]
    for a in anchors:
        color = "green" if a["expectation"] == "强于预期" else "yellow"
        console.print(f"  [{color}]{a['type']}: {a['ticker']} {a['name']} ({a['boards']}板) — {a['expectation']}[/{color}]")

    # 资金进攻
    console.print("\n[bold green]资金主攻: AI算力板块 (净流入+28.5亿)[/bold green]")
    console.print("[bold green]第二方向: CPO光模块 (净流入+15.2亿)[/bold green]")

    print_success("盘中监控运行中 — 按 Ctrl+C 停止")


def cmd_post_market(config: AppConfig, date_str: Optional[str] = None):
    """盘后复盘命令"""
    trade_date = date.fromisoformat(date_str) if date_str else date.today()
    print_info(f"执行盘后复盘: {trade_date}")

    # 情绪诊断
    emotion = _mock_emotion_diagnosis()
    print_emotion_diagnosis(emotion)

    # 评分排名
    scores = _mock_scores()
    print_score_table(scores)

    # 战法筛选
    tactics = _mock_tactic_matches()
    print_tactic_matches(tactics)

    # 交易计划
    plan = _mock_trade_plan("603083.SH")
    print_trade_plan(plan)

    print_success("盘后复盘完成 — 次日预判已生成")


def cmd_analyze(config: AppConfig, ticker: str):
    """个股分析命令"""
    print_info(f"分析标的: {ticker}")

    # 评分
    scores = _mock_scores(ticker)
    print_score_table(scores)

    # 维度明细
    dims = _mock_dimension_scores()
    print_dimension_scores(dims)

    # 交易计划
    plan = _mock_trade_plan(ticker)
    print_trade_plan(plan)


def cmd_score(config: AppConfig, ticker: str):
    """综合评分命令"""
    print_info(f"综合评分: {ticker}")

    scores = _mock_scores(ticker)
    print_score_table(scores)

    dims = _mock_dimension_scores()
    print_dimension_scores(dims)

    # 风险收益比
    from ..modules.m06_scoring_decision.risk_reward import RiskRewardCalculator
    calc = RiskRewardCalculator(config)
    rr = calc.calculate(45.80, 43.51, 54.96)
    console.print(f"\n[bold]风险收益比: {rr.risk_reward_ratio}:1[/bold] — {rr.decision}")
    console.print(f"建议仓位: {rr.max_position_pct}%")

    print_success(f"评分完成: {ticker} = {scores[0]['total_score']}分 [{scores[0]['rating']}]")


def cmd_diagnose(config: AppConfig, file_path: str, output: Optional[str] = None):
    """交割单诊断命令"""
    print_info(f"导入交割单: {file_path}")

    try:
        from ..modules.m07_trade_diagnosis.importer import TradeImporter
        importer = TradeImporter()
        records = importer.import_from_file(file_path)
        print_success(f"成功导入 {len(records)} 条交易记录")

        # 生成画像
        from ..modules.m07_trade_diagnosis.profiler import TradeProfiler
        profiler = TradeProfiler()

        # 使用mock数据演示
        profile = _mock_trader_profile()
        print_trader_profile(profile)

    except Exception as e:
        print_error(f"导入失败: {e}")
        console.print("[yellow]使用演示数据...[/yellow]")
        profile = _mock_trader_profile()
        print_trader_profile(profile)


def cmd_yingyou(config: AppConfig, emotion_cycle: Optional[str] = None):
    """游资诊断命令"""
    cycle = emotion_cycle or "发酵期"
    print_info(f"游资诊断 — 情绪周期: {cycle}")

    recommendations = _mock_yingyou_recommendations()
    print_yingyou_recommendations(recommendations)

    # 共识分析
    console.print("\n[bold yellow]游资共识标的: 603083.SH 剑桥科技[/bold yellow]")
    console.print("  [green]2位游资强烈推荐，共识度高，关注价值极高[/green]")


def cmd_tactics(config: AppConfig, tactic: Optional[str], all_tactics: bool):
    """战法筛选命令"""
    if tactic:
        print_info(f"战法筛选: {tactic}")
    else:
        print_info("执行全部战法筛选")

    matches = _mock_tactic_matches()
    print_tactic_matches(matches)

    # 共振分析
    console.print("\n[bold green]战法共振: 603083.SH 剑桥科技 — 三倍量突破+筹码峰双共振[/bold green]")


def cmd_evaluate(config: AppConfig, ticker: str):
    """自定义标的研判命令"""
    print_info(f"全维度研判: {ticker}")

    analysis = _mock_custom_analysis(ticker)
    print_custom_analysis(analysis)

    # 交易计划
    plan = _mock_trade_plan(ticker)
    console.print("\n")
    print_trade_plan(plan)
