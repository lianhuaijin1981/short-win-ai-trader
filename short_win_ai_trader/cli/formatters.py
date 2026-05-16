"""CLI输出格式化 — Rich美化"""

from datetime import date
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner():
    """打印SWAT欢迎横幅"""
    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗
║         短线致胜 AI 交易智能体 v1.0.0                    ║
║     Short-Win AI Trader — A股超短线决策系统               ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


def print_score_table(scores: List[Dict]):
    """打印评分表格"""
    table = Table(title="综合评分排名", show_header=True, header_style="bold magenta")
    table.add_column("排名", style="cyan", width=4)
    table.add_column("代码", style="white", width=12)
    table.add_column("名称", style="white", width=12)
    table.add_column("总分", justify="right", width=6)
    table.add_column("评级", width=8)
    table.add_column("风险等级", width=8)
    table.add_column("RR比", justify="right", width=8)
    table.add_column("建议仓位", width=8)
    table.add_column("决策", width=20)

    rating_colors = {
        "顶级标的": "bold green",
        "优质标的": "green",
        "良好标的": "yellow",
        "一般标的": "red",
        "劣质标的": "bold red",
    }
    risk_colors = {
        "安全": "green",
        "谨慎": "yellow",
        "高风险": "red",
        "禁入": "bold red",
    }

    for i, s in enumerate(scores, 1):
        r_color = rating_colors.get(s.get("rating", ""), "white")
        risk_color = risk_colors.get(s.get("risk_level", ""), "white")
        table.add_row(
            str(i),
            s.get("ticker", ""),
            s.get("stock_name", ""),
            f"{s.get('total_score', 0):.0f}",
            f"[{r_color}]{s.get('rating', '')}[/{r_color}]",
            f"[{risk_color}]{s.get('risk_level', '')}[/{risk_color}]",
            f"{s.get('risk_reward_ratio', 0)}:1",
            s.get("position", ""),
            s.get("decision", "")[:20],
        )
    console.print(table)


def print_dimension_scores(dimensions: List[Dict]):
    """打印维度评分明细"""
    table = Table(title="维度评分详情", show_header=True, header_style="bold blue")
    table.add_column("维度", style="white")
    table.add_column("权重", justify="right")
    table.add_column("得分", justify="right")
    table.add_column("状态")

    for d in dimensions:
        score = d.get("score", 0)
        status = "[green]优秀[/]" if score >= 80 else "[yellow]一般[/]" if score >= 60 else "[red]不足[/]"
        table.add_row(
            d.get("dimension", ""),
            f"{d.get('weight', 0)}%",
            f"{score:.1f}",
            status,
        )
    console.print(table)


def print_trade_plan(plan: Dict):
    """打印交易计划"""
    table = Table(title="交易计划", show_header=True, header_style="bold cyan")
    table.add_column("项目", style="white")
    table.add_column("内容", style="green")

    items = [
        ("标的", f"{plan.get('ticker', '')} {plan.get('stock_name', '')}"),
        ("入场价", f"{plan.get('entry_price', 0):.2f}元"),
        ("入场类型", plan.get("entry_type", "")),
        ("止损价", f"[red]{plan.get('stop_loss_price', 0):.2f}元[/red]"),
        ("止盈价", f"[green]{plan.get('take_profit_price', 0):.2f}元[/green]"),
        ("建议仓位", f"{plan.get('position_pct', 0)}%"),
    ]
    for k, v in items:
        table.add_row(k, v)

    console.print(table)

    # 持有条件
    if plan.get("hold_conditions"):
        console.print("[bold]持有条件:[/bold]")
        for c in plan["hold_conditions"]:
            console.print(f"  [green]* {c}[/green]")

    # 卖出条件
    if plan.get("sell_conditions"):
        console.print("[bold]卖出条件(满足任一):[/bold]")
        for c in plan["sell_conditions"]:
            console.print(f"  [red]* {c}[/red]")


def print_emotion_diagnosis(diagnosis: Dict):
    """打印情绪周期诊断"""
    cycle_colors = {
        "混沌期": "white",
        "启动期": "blue",
        "发酵期": "green",
        "高潮期": "bold green",
        "分歧期": "yellow",
        "退潮期": "red",
    }
    cycle = diagnosis.get("current_cycle", "未知")
    color = cycle_colors.get(cycle, "white")

    panel = Panel(
        f"[bold {color}]当前情绪: {cycle}[/bold {color}]\n"
        f"置信度: {diagnosis.get('confidence', 0)}%\n"
        f"建议仓位: [bold]{diagnosis.get('position_limit', 0)}成[/bold]\n"
        f"适配模式: {diagnosis.get('adapted_mode', '')}\n"
        f"核心原则: {diagnosis.get('core_principle', '')}\n"
        f"次日预判: {diagnosis.get('next_day_prediction', '')}",
        title="情绪周期诊断",
        border_style=color,
    )
    console.print(panel)


def print_yingyou_recommendations(recommendations: List[Dict]):
    """打印游资推荐"""
    table = Table(title="游资推荐标的", show_header=True, header_style="bold yellow")
    table.add_column("游资", style="cyan")
    table.add_column("代码", style="white")
    table.add_column("名称", style="white")
    table.add_column("匹配度", justify="right")
    table.add_column("推荐", width=8)
    table.add_column("操作建议", width=30)

    for r in recommendations:
        score = r.get("match_score", 0)
        rec_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        table.add_row(
            r.get("yingyou_name", ""),
            r.get("ticker", ""),
            r.get("stock_name", ""),
            f"{score:.0f}分",
            f"[{rec_color}]{r.get('recommendation', '')}[/{rec_color}]",
            r.get("operation", "")[:30],
        )
    console.print(table)


def print_tactic_matches(matches: List[Dict]):
    """打印战法匹配结果"""
    table = Table(title="战法选股结果", show_header=True, header_style="bold green")
    table.add_column("战法", style="cyan")
    table.add_column("代码", style="white")
    table.add_column("名称", style="white")
    table.add_column("匹配分", justify="right")
    table.add_column("形态判定", width=10)
    table.add_column("走势预判", width=20)

    for m in matches:
        table.add_row(
            m.get("tactic_name", ""),
            m.get("ticker", ""),
            m.get("stock_name", ""),
            f"{m.get('match_score', 0):.0f}分",
            m.get("shape_verdict", ""),
            m.get("prediction", "")[:20],
        )
    console.print(table)


def print_trader_profile(profile: Dict):
    """打印交易者画像"""
    panel = Panel(
        f"[bold]交易统计[/bold]\n"
        f"总交易: {profile.get('total_trades', 0)}笔 | "
        f"胜率: {profile.get('win_rate', 0)}% | "
        f"盈亏比: {profile.get('profit_loss_ratio', 0)}\n"
        f"最大回撤: {profile.get('max_drawdown', 0)}%\n\n"
        f"[bold]风格定型[/bold]: {profile.get('style', '未定型')}\n"
        f"[bold]黄金时段[/bold]: {profile.get('golden_hour', '未确定')}\n\n"
        f"[bold]擅长题材[/bold]: {', '.join(profile.get('strength_themes', [])) or '暂无'}\n"
        f"[bold]亏损题材[/bold]: {', '.join(profile.get('weakness_themes', [])) or '暂无'}\n\n"
        f"[bold]高频错误[/bold]:\n" +
        "\n".join(f"  [red]* {e}[/red]" for e in profile.get('error_patterns', [])),
        title="个人交易画像",
        border_style="blue",
    )
    console.print(panel)


def print_custom_analysis(analysis: Dict):
    """打印自定义标的研判"""
    console.print(Panel(
        f"[bold cyan]{analysis.get('ticker', '')} {analysis.get('name', '')}[/bold cyan] "
        f"综合评分: {analysis.get('comprehensive_score', 0):.0f}分 [{analysis.get('rating', '')}]",
        title="全维度标的研判",
        border_style="cyan",
    ))

    # 成功逻辑
    if analysis.get("success_logic"):
        console.print("[bold green]做多核心逻辑:[/bold green]")
        for s in analysis["success_logic"]:
            console.print(f"  [green]+ {s}[/green]")

    # 风险败点
    if analysis.get("risk_points"):
        console.print("[bold red]潜在风险败点:[/bold red]")
        for r in analysis["risk_points"]:
            console.print(f"  [red]- {r}[/red]")

    # 风格建议
    if analysis.get("style_advice"):
        console.print(f"[bold yellow]个人风格建议: {analysis['style_advice']}[/bold yellow]")


def print_error(message: str):
    """打印错误信息"""
    console.print(f"[bold red]错误: {message}[/bold red]")


def print_success(message: str):
    """打印成功信息"""
    console.print(f"[bold green]{message}[/bold green]")


def print_info(message: str):
    """打印提示信息"""
    console.print(f"[blue]{message}[/blue]")
