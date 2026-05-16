"""CLI主入口 — Click命令行界面"""

import click
from rich.console import Console

from .. import __version__
from ..core.config import load_config
from ..core.logger import get_logger, setup_logging
from .formatters import print_banner, print_error, print_success

console = Console()
logger = get_logger("swat.cli")


@click.group()
@click.option("--config", "-c", default=None, help="配置文件路径")
@click.option("--verbose", "-v", is_flag=True, help="详细输出模式")
@click.pass_context
def cli(ctx, config, verbose):
    """短线致胜 AI 交易智能体 (SWAT)
    
    A股超短线AI决策系统，对接同花顺iFind数据
    
    示例:
        swat pre-market --date 2026-05-16    # 盘前分析
        swat score --ticker 600519.SH         # 综合评分
        swat diagnose --file 交割单.xlsx       # 交割单诊断
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["verbose"] = verbose

    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level)


# ============== 核心命令 ==============

@cli.command()
@click.option("--date", "-d", default=None, help="分析日期 (YYYY-MM-DD)")
@click.pass_context
def pre_market(ctx, date):
    """盘前分析: 资讯汇总 + 情绪预判 + 避雷清单"""
    print_banner()
    from .commands import cmd_pre_market
    cmd_pre_market(ctx.obj["config"], date)


@cli.command()
@click.option("--watch-interval", "-i", default=30, help="监控间隔(秒)")
@click.pass_context
def intraday(ctx, watch_interval):
    """盘中监控: 锚定标的 + 资金追踪 + 板块预警"""
    print_banner()
    from .commands import cmd_intraday
    cmd_intraday(ctx.obj["config"], watch_interval)


@cli.command()
@click.option("--date", "-d", default=None, help="复盘日期 (YYYY-MM-DD)")
@click.pass_context
def post_market(ctx, date):
    """盘后复盘: 情绪诊断 + 题材研判 + 次日预判 + 评分排名"""
    print_banner()
    from .commands import cmd_post_market
    cmd_post_market(ctx.obj["config"], date)


@cli.command()
@click.option("--ticker", "-t", required=True, help="股票代码 (如 600519.SH)")
@click.pass_context
def analyze(ctx, ticker):
    """个股全维度分析"""
    print_banner()
    from .commands import cmd_analyze
    cmd_analyze(ctx.obj["config"], ticker)


@cli.command()
@click.option("--ticker", "-t", required=True, help="股票代码")
@click.pass_context
def score(ctx, ticker):
    """综合评分: 6维度量化评分 + 风险收益比 + 仓位建议"""
    from .commands import cmd_score
    cmd_score(ctx.obj["config"], ticker)


@cli.command()
@click.option("--file", "-f", required=True, help="交割单文件路径 (.xlsx 或 .csv)")
@click.option("--output", "-o", default=None, help="输出报告路径")
@click.pass_context
def diagnose(ctx, file, output):
    """交割单诊断: 逐笔归因 + 风格画像 + 错题库"""
    from .commands import cmd_diagnose
    cmd_diagnose(ctx.obj["config"], file, output)


@cli.command()
@click.option("--emotion-cycle", "-e", default=None, help="情绪周期 (如: 发酵期)")
@click.pass_context
def yingyou(ctx, emotion_cycle):
    """游资诊断: 8大游资视角盘面诊断 + 标的推荐"""
    from .commands import cmd_yingyou
    cmd_yingyou(ctx.obj["config"], emotion_cycle)


@cli.command()
@click.option("--tactic", "-t", default=None, help="战法名称 (如: 筹码峰战法)")
@click.option("--all", "all_tactics", is_flag=True, help="执行全部战法筛选")
@click.pass_context
def tactics(ctx, tactic, all_tactics):
    """战法筛选: 15+战法选股 + 共振分析"""
    from .commands import cmd_tactics
    cmd_tactics(ctx.obj["config"], tactic, all_tactics)


@cli.command()
@click.option("--ticker", "-t", required=True, help="股票代码")
@click.pass_context
def evaluate(ctx, ticker):
    """自定义标的研判: 全维度胜败分析"""
    from .commands import cmd_evaluate
    cmd_evaluate(ctx.obj["config"], ticker)


@cli.command()
@click.pass_context
def cache_clear(ctx):
    """清空数据缓存"""
    from ..data_platform.cache_manager import CacheManager
    cache = CacheManager()
    cache.clear_all()
    print_success("数据缓存已清空")


# ============== 版本 ==============

@cli.command()
def version():
    """显示版本信息"""
    print_banner()
    console.print(f"[bold]版本: {__version__}[/bold]")
    console.print(f"[bold]作者: lianhuaijin[/bold]")
    console.print(f"[bold]数据: 同花顺iFind[/bold]")


def main():
    """CLI入口"""
    cli()


if __name__ == "__main__":
    main()
