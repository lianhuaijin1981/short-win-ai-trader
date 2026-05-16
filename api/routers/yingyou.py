"""游资模式诊断 API 路由

路由:
    GET /yingyou/list         — 游资列表
    GET /yingyou/{name}/profile   — 游资详情
    GET /yingyou/{name}/radar     — 数字指纹雷达图数据
    GET /yingyou/diagnose     — 盘面诊断
    GET /yingyou/recommend    — 推荐标的
    GET /yingyou/consensus    — 共识分析
    GET /yingyou/portfolio    — 组合策略
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.logger import get_logger
from api.models.responses import (
    BaseResponse,
    DataResponse,
    YingYouMatch,
)
from api.services.ifind_service import ifind_service

from short_win_ai_trader.modules.m04_yingyou_diagnosis import (
    consensus_analyzer,
    consensus_pool,
    diagnosis_engine,
    portfolio_engine,
    recommender,
    registry,
)

logger = get_logger("swat.api.yingyou")

router = APIRouter()


# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def _yingyou_to_dict(name: str, detail: bool = False) -> dict:
    """将游资指纹转换为字典"""
    fp = registry.get(name)
    if not fp:
        return {}

    base = {
        "name": fp.name,
        "nickname": fp.nickname,
        "philosophy": fp.philosophy,
        "quote": fp.quote,
        "radar_scores": fp.radar_scores,
        "position_limit": fp.position_limit,
        "single_position_limit": fp.single_position_limit,
        "applicable_cycles": fp.applicable_cycles,
        "behavioral_tags": fp.behavioral_tags if isinstance(fp.behavioral_tags, list) else list(fp.behavioral_tags),
    }

    if detail:
        base.update({
            "philosophy_detail": fp.philosophy_detail,
            "stock_selection": fp.stock_selection,
            "entry_timing": fp.entry_timing,
            "risk_control": fp.risk_control,
            "classic_tactics": fp.classic_tactics,
            "position_strategy": fp.position_strategy,
            "stop_loss_rule": fp.stop_loss_rule,
            "take_profit_rule": fp.take_profit_rule,
            "key_indicators": fp.key_indicators,
        })

    return base


# ═══════════════════════════════════════════════════════════
# 路由: 游资列表
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/list", response_model=DataResponse)
async def yingyou_list():
    """获取游资列表

    返回8大顶级游资的基本信息:
    - 炒股养家、退学炒股、涅槃重生、92科比
    - 小鳄鱼、龙飞虎、职业炒手、Asking
    """
    try:
        all_names = registry.list_all()
        items = [_yingyou_to_dict(name) for name in all_names]

        return DataResponse(
            code=200,
            message="success",
            data={
                "total": len(items),
                "items": items,
            },
        )
    except Exception as e:
        logger.error(f"yingyou_list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 游资详情
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/{name}/profile", response_model=DataResponse)
async def yingyou_profile(name: str):
    """获取游资详情

    参数:
        name: 游资名称，如"炒股养家""退学炒股"等

    返回完整的游资数字指纹:
    - 交易哲学、选股标准、买入时机
    - 风控铁律、经典战法、雷达图评分
    """
    try:
        if name not in registry.list_all():
            raise HTTPException(status_code=404, detail=f"游资'{name}'不存在")

        data = _yingyou_to_dict(name, detail=True)

        return DataResponse(
            code=200,
            message="success",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"yingyou_profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 雷达图数据
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/{name}/radar", response_model=DataResponse)
async def yingyou_radar(name: str):
    """获取游资数字指纹雷达图数据

    参数:
        name: 游资名称

    返回5维雷达图数据:
    - 情绪敏感度、执行力、选股能力、风控水平、盈利稳定性
    """
    try:
        if name not in registry.list_all():
            raise HTTPException(status_code=404, detail=f"游资'{name}'不存在")

        radar = registry.get_radar_data(name)
        if not radar:
            raise HTTPException(status_code=404, detail="雷达图数据不存在")

        fp = registry.get(name)

        return DataResponse(
            code=200,
            message="success",
            data={
                "yingyou": name,
                "nickname": fp.nickname if fp else "",
                "dimensions": radar["dimensions"],
                "scores": radar["scores"],
                "full_marks": radar["full_marks"],
                "max_score": max(radar["scores"]) if radar["scores"] else 0,
                "avg_score": round(sum(radar["scores"]) / len(radar["scores"]), 2) if radar["scores"] else 0,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"yingyou_radar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 盘面诊断
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/diagnose", response_model=DataResponse)
async def yingyou_diagnose(
    quick: bool = Query(False, description="快速诊断模式(简化版)"),
):
    """游资视角盘面诊断

    三维诊断:
    - 情绪阶段: 当前市场情绪周期(冰点/修复/高潮/退潮)
    - 资金方向: 游资资金流向与热点题材
    - 模式契合度: 当前盘面与各游资模式的匹配程度

    参数:
        quick: 是否快速诊断(简化输出)
    """
    try:
        if quick:
            result = await diagnosis_engine.diagnose_quick()
            return DataResponse(
                code=200,
                message="success",
                data=result,
            )

        report = await diagnosis_engine.diagnose()

        # 序列化报告
        mode_fits_data = [
            {
                "yingyou_name": m.yingyou_name,
                "fit_score": m.fit_score,
                "applicable": m.applicable,
                "reason": m.reason,
                "opportunity_level": m.opportunity_level,
                "risk_level": m.risk_level,
                "best_tactic": m.best_tactic,
                "position_pct": m.position_pct,
            }
            for m in report.mode_fits
        ]

        data = {
            "timestamp": report.timestamp,
            "emotion_phase": {
                "phase": report.emotion_phase.phase,
                "confidence": report.emotion_phase.confidence,
                "indicators": report.emotion_phase.indicators,
                "position_suggestion": report.emotion_phase.position_suggestion,
                "operation_suggestion": report.emotion_phase.operation_suggestion,
            },
            "fund_direction": {
                "primary_direction": report.fund_direction.primary_direction,
                "secondary_direction": report.fund_direction.secondary_direction,
                "hot_themes": report.fund_direction.hot_themes,
                "fund_flow_score": report.fund_direction.fund_flow_score,
                "activity_level": report.fund_direction.activity_level,
                "inflow_sectors": report.fund_direction.inflow_sectors,
                "outflow_sectors": report.fund_direction.outflow_sectors,
            },
            "mode_fits": mode_fits_data,
            "consensus_opinion": report.consensus_opinion,
            "risk_warnings": report.risk_warnings,
            "opportunity_summary": report.opportunity_summary,
            "top_recommendations": report.top_recommendations,
        }

        return DataResponse(
            code=200,
            message="success",
            data=data,
        )
    except Exception as e:
        logger.error(f"yingyou_diagnose error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 推荐标的
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/recommend", response_model=DataResponse)
async def yingyou_recommend(
    ticker: str = Query(..., description="股票代码, 如600519.SH"),
    name: str = Query("", description="股票名称"),
    yingyou_filter: Optional[str] = Query(None, description="游资筛选(逗号分隔)"),
    threshold: float = Query(50.0, description="匹配度阈值"),
):
    """游资模式标的推荐

    对指定标的进行8大游资模式匹配度评分:
    - 趋势强度、题材契合、量能质量
    - 位置优劣、换手水平、情绪匹配、资金动向

    参数:
        ticker: 股票代码
        name: 股票名称
        yingyou_filter: 只匹配指定游资(逗号分隔)
        threshold: 匹配度阈值(默认50)

    返回:
        按匹配度排序的游资推荐列表
    """
    try:
        # 解析游资筛选
        yingyou_list = None
        if yingyou_filter:
            yingyou_list = [y.strip() for y in yingyou_filter.split(",")]
            valid = registry.list_all()
            yingyou_list = [y for y in yingyou_list if y in valid]
            if not yingyou_list:
                yingyou_list = None

        # 获取推荐
        matches = await recommender.recommend(ticker, name, yingyou_list)

        # 筛选高匹配度
        top_matches = recommender.get_top_matches(matches, threshold=threshold, top_n=8)

        # 转换为响应模型
        yingyou_matches = [
            YingYouMatch(
                yingyou_name=m.yingyou_name,
                ticker=m.ticker,
                name=m.name,
                match_score=m.match_score,
                recommendation=m.recommendation,
                operation=m.operation,
                position=m.position,
                stop_loss=m.stop_loss,
                take_profit=m.take_profit,
            )
            for m in top_matches
        ]

        # 维度评分详情
        dimension_details = []
        for m in top_matches[:3]:
            dimension_details.append({
                "yingyou": m.yingyou_name,
                "dimensions": m.dimension_scores if hasattr(m, 'dimension_scores') else {},
            })

        return DataResponse(
            code=200,
            message="success",
            data={
                "ticker": ticker,
                "name": name,
                "threshold": threshold,
                "total_matches": len(matches),
                "filtered_matches": len(top_matches),
                "matches": [m.model_dump() for m in yingyou_matches],
                "dimension_details": dimension_details,
                "summary": (
                    f"共{len(matches)}位游资匹配，"
                    f"{len(top_matches)}位超过{threshold}分阈值"
                ),
            },
        )
    except Exception as e:
        logger.error(f"yingyou_recommend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 共识分析
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/consensus", response_model=DataResponse)
async def yingyou_consensus(
    tickers: str = Query("", description="股票代码列表(逗号分隔)，如600519.SH,000001.SZ"),
    threshold: float = Query(50.0, description="匹配度阈值"),
):
    """游资共识分析

    分析多只标的的游资共识度:
    - 强共识(>=4位游资): A级信号
    - 中共识(3位游资): B级信号
    - 弱共识(2位游资): C级信号
    - 分歧预警: 游资间看法分化

    参数:
        tickers: 股票代码列表(逗号分隔)
        threshold: 匹配度阈值
    """
    try:
        # 解析股票列表
        if tickers:
            ticker_list = [t.strip() for t in tickers.split(",")]
            ticker_dicts = [{"ticker": t, "name": ""} for t in ticker_list]
        else:
            # 默认使用智能选股
            try:
                screen_result = await ifind_service.screen_stocks("热点题材")
                ticker_dicts = [{"ticker": t, "name": ""} for t in screen_result[:10]]
            except Exception:
                ticker_dicts = [
                    {"ticker": "600519.SH", "name": "贵州茅台"},
                    {"ticker": "000001.SZ", "name": "平安银行"},
                    {"ticker": "002230.SZ", "name": "科大讯飞"},
                    {"ticker": "300750.SZ", "name": "宁德时代"},
                    {"ticker": "688981.SH", "name": "中芯国际"},
                ]

        # 执行共识分析
        report = await consensus_analyzer.analyze(ticker_dicts, threshold)

        data = {
            "timestamp": report.timestamp,
            "summary": report.summary,
            "strong_consensus": [
                {
                    "ticker": s.ticker,
                    "name": s.name,
                    "level": s.consensus_level,
                    "yingyou_names": s.yingyou_names,
                    "avg_score": s.avg_score,
                    "max_score": s.max_score,
                    "agreement_score": s.agreement_score,
                    "summary": s.summary,
                    "risk_note": s.risk_note,
                }
                for s in report.strong_consensus
            ],
            "medium_consensus": [
                {
                    "ticker": s.ticker,
                    "name": s.name,
                    "level": s.consensus_level,
                    "yingyou_names": s.yingyou_names,
                    "avg_score": s.avg_score,
                    "agreement_score": s.agreement_score,
                }
                for s in report.medium_consensus
            ],
            "weak_consensus": [
                {
                    "ticker": s.ticker,
                    "name": s.name,
                    "level": s.consensus_level,
                    "yingyou_names": s.yingyou_names,
                    "avg_score": s.avg_score,
                }
                for s in report.weak_consensus
            ],
            "divergence_alerts": [
                {
                    "ticker": a.ticker,
                    "name": a.name,
                    "divergence_score": a.divergence_score,
                    "bull_yingyou": a.bull_yingyou,
                    "bear_yingyou": a.bear_yingyou,
                    "reason": a.reason,
                    "alert_level": a.alert_level,
                    "suggestion": a.suggestion,
                }
                for a in report.divergence_alerts
            ],
            "stats": {
                "total_analyzed": len(ticker_dicts),
                "strong_count": len(report.strong_consensus),
                "medium_count": len(report.medium_consensus),
                "weak_count": len(report.weak_consensus),
                "divergence_count": len(report.divergence_alerts),
            },
        }

        return DataResponse(
            code=200,
            message="success",
            data=data,
        )
    except Exception as e:
        logger.error(f"yingyou_consensus error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 路由: 组合策略
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/portfolio", response_model=DataResponse)
async def yingyou_portfolio(
    level: str = Query("新手", description="组合等级: 新手/进阶/高手"),
    detail: bool = Query(False, description="是否返回详细执行方案"),
):
    """游资组合策略

    根据交易者水平提供不同的游资组合:
    - 新手(退学炒股+92科比): 严控风险，提高胜率
    - 进阶(炒股养家+小鳄鱼): 情绪周期+打板，稳定盈利
    - 高手(Asking+职业炒手): 只做最强，追求暴利

    参数:
        level: 组合等级(新手/进阶/高手)
        detail: 是否返回详细执行方案

    返回:
        组合策略配置、今日计划、风险提醒
    """
    try:
        valid_levels = portfolio_engine.get_all_levels()
        if level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"无效等级'{level}'，可选: {', '.join(valid_levels)}"
            )

        # 生成策略
        strategy = await portfolio_engine.generate_strategy(level)

        data = {
            "level": strategy.level,
            "config": {
                "max_position": f"{strategy.config.max_position}%",
                "single_position_limit": f"{strategy.config.single_position_limit}%",
                "stop_loss_rule": strategy.config.stop_loss_rule,
                "take_profit_rule": strategy.config.take_profit_rule,
                "daily_trade_limit": strategy.config.daily_trade_limit,
                "expected_return": strategy.config.expected_return_monthly,
                "max_drawdown": f"{strategy.config.max_drawdown_limit}%",
                "core_philosophy": strategy.config.core_philosophy,
            },
            "primary_yingyou": strategy.primary_yingyou,
            "current_diagnosis": strategy.current_diagnosis,
            "today_plan": strategy.today_plan,
            "risk_reminder": strategy.risk_reminder,
        }

        # 详细执行方案
        if detail:
            execution = await portfolio_engine.generate_execution(level)
            data["execution"] = {
                "total_position": f"{execution.total_position}%",
                "positions": execution.positions,
                "entry_plan": execution.entry_plan,
                "exit_plan": execution.exit_plan,
                "emergency_plan": execution.emergency_plan,
                "review_criteria": execution.review_criteria,
            }

        # 添加等级说明
        data["available_levels"] = [
            portfolio_engine.get_level_description(l)
            for l in valid_levels
        ]

        return DataResponse(
            code=200,
            message="success",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"yingyou_portfolio error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 额外路由: 游资对比
# ═══════════════════════════════════════════════════════════

@router.get("/yingyou/compare", response_model=DataResponse)
async def yingyou_compare(
    names: str = Query(..., description="游资名称列表(逗号分隔)"),
):
    """游资对比

    对比多个游资的雷达图数据

    参数:
        names: 游资名称列表(逗号分隔)
    """
    try:
        name_list = [n.strip() for n in names.split(",")]
        valid_names = [n for n in name_list if n in registry.list_all()]

        if not valid_names:
            raise HTTPException(status_code=400, detail="没有有效的游资名称")

        compare_data = registry.compare(valid_names)

        # 添加详细信息
        details = [_yingyou_to_dict(n, detail=False) for n in valid_names]

        return DataResponse(
            code=200,
            message="success",
            data={
                "compare": compare_data,
                "details": details,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"yingyou_compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
