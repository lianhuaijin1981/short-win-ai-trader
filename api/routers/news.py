"""资讯采集路由 — 多源资讯采集、消息影响力评估、利好介入建议、利空风险预警

基于历史回测的消息类型重要性研判机制，提供:
- GET  /news/collect          — 多源资讯采集
- GET  /news/scored           — 已评分资讯列表
- GET  /news/recommendations  — 利好介入建议
- GET  /news/risk-alerts      — 利空风险预警
- GET  /news/analysis         — 综合分析（利好+利空）
- GET  /news/backtest/profiles — 消息类型回测画像
- GET  /news/sources/status   — 资讯来源状态
- GET  /news/risk-list        — 避雷清单（兼容旧版）
- GET  /news/pre-market       — 盘前汇总（兼容旧版）
- GET  /news/latest           — 最新资讯（兼容旧版）

Author: SWAT Engine
Version: 2.0.0
"""

import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.logger import get_logger
from api.models.responses import BaseResponse, DataResponse

logger = get_logger("swat.router.news")

router = APIRouter(prefix="/news", tags=["News"])

# 全局实例（延迟初始化）
_news_collector = None
_multi_fetcher = None
_backtest_engine = None
_recommendation_engine = None


def _get_news_collector():
    """获取资讯采集器实例（延迟初始化）"""
    global _news_collector
    if _news_collector is None:
        from short_win_ai_trader.core.config import AppConfig
        from short_win_ai_trader.modules.m01_news_collector.collector import NewsCollector
        _news_collector = NewsCollector(AppConfig(), use_mock=True)
    return _news_collector


def _get_multi_fetcher():
    """获取多源采集器实例"""
    global _multi_fetcher
    if _multi_fetcher is None:
        from short_win_ai_trader.modules.m01_news_collector.multi_source_fetcher import MultiSourceFetcher
        _multi_fetcher = MultiSourceFetcher(use_mock=True)
    return _multi_fetcher


def _get_backtest_engine():
    """获取回测引擎实例"""
    global _backtest_engine
    if _backtest_engine is None:
        from short_win_ai_trader.modules.m01_news_collector.backtest_engine import BacktestEngine
        _backtest_engine = BacktestEngine()
    return _backtest_engine


def _get_recommendation_engine():
    """获取建议引擎实例"""
    global _recommendation_engine
    if _recommendation_engine is None:
        from short_win_ai_trader.modules.m01_news_collector.recommendation_engine import RecommendationEngine
        _recommendation_engine = RecommendationEngine(_get_backtest_engine())
    return _recommendation_engine


# ──────────────────────────────────────────────────────────
# 核心路由 — 新版资讯采集系统
# ──────────────────────────────────────────────────────────

@router.get("/collect", response_model=DataResponse)
async def collect_news(
    trade_date: Optional[str] = Query(None, description="交易日 (YYYY-MM-DD)，默认今日"),
    sources: Optional[str] = Query(None, description="指定资讯来源（逗号分隔），默认全部"),
    use_mock: bool = Query(True, description="是否使用模拟数据"),
):
    """多源资讯采集
    
    从多个重要资讯来源并行采集当日资讯:
    - 巨潮资讯: 上市公司公告
    - 财联社: 实时财经快讯
    - 东方财富: 资金流向
    - 雪球: 投资者社区热股
    - 淘股吧: 短线投资者社区
    - 开盘啦: 盘前竞价数据
    
    Returns:
        采集的资讯列表及来源统计
    """
    import asyncio
    
    logger.info(f"多源资讯采集: trade_date={trade_date}, sources={sources}")
    
    try:
        # 解析参数
        target_date = date.fromisoformat(trade_date) if trade_date else date.today()
        source_list = [s.strip() for s in sources.split(",")] if sources else None
        
        # 获取多源采集器
        fetcher = _get_multi_fetcher()
        fetcher.use_mock = use_mock
        
        # 并行采集
        news_items = await fetcher.fetch_all(target_date, source_list)
        
        # 按来源统计
        source_stats: Dict[str, int] = {}
        category_stats: Dict[str, int] = {}
        
        for item in news_items:
            src = item.source.name
            source_stats[src] = source_stats.get(src, 0) + 1
            cat = item.category.value
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        # 转换为响应格式
        news_data = [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category": item.category.value,
                "source": {
                    "name": item.source.name,
                    "url": item.source.url,
                    "source_type": item.source.source_type,
                    "credibility": item.source.credibility,
                },
                "publish_time": item.publish_time.isoformat() if item.publish_time else None,
                "trade_date": item.trade_date.isoformat() if item.trade_date else None,
                "related_tickers": item.related_tickers,
                "related_themes": item.related_themes,
                "keywords": item.keywords,
            }
            for item in news_items
        ]
        
        return DataResponse(
            data={
                "trade_date": target_date.isoformat(),
                "total_count": len(news_items),
                "source_statistics": source_stats,
                "category_statistics": category_stats,
                "news": news_data,
            }
        )
    except Exception as e:
        logger.error(f"多源资讯采集失败: {e}")
        raise HTTPException(status_code=500, detail=f"资讯采集失败: {str(e)}")


@router.get("/scored", response_model=DataResponse)
async def get_scored_news(
    trade_date: Optional[str] = Query(None, description="交易日 (YYYY-MM-DD)"),
    min_score: float = Query(0.0, description="最低评分（0-100）"),
    grade: Optional[str] = Query(None, description="等级过滤: S/A/B/C"),
    category: Optional[str] = Query(None, description="分类过滤: 政策/外围/资金/题材/个股/舆情"),
    use_mock: bool = Query(True, description="是否使用模拟数据"),
):
    """获取已评分资讯列表
    
    基于历史回测的多维度评分系统:
    - 催化强度 (30%): 资讯对股价的催化力度
    - 时效性 (20%): 资讯发布的及时程度
    - 关联度 (20%): 与当前市场主线的关联程度
    - 历史验证 (15%): 同类资讯历史回测表现
    - 市场反馈 (15%): 资讯发布后市场实际反应
    
    评分等级:
    - S级 (>=75分): 高价值资讯，需重点跟踪
    - A级 (50-74分): 较高价值资讯，值得关注
    - B级 (25-49分): 一般价值资讯，作为参考
    - C级 (<25分): 低价值资讯，可忽略
    
    Returns:
        已评分资讯列表（按分数降序）
    """
    import asyncio
    
    logger.info(f"获取已评分资讯: min_score={min_score}, grade={grade}")
    
    try:
        target_date = date.fromisoformat(trade_date) if trade_date else date.today()
        
        # 采集资讯
        collector = _get_news_collector()
        collector._use_mock = use_mock
        
        news_items = await collector.collect_news(target_date)
        
        # 评分
        scored_news = collector.score_news(news_items)
        
        # 过滤
        filtered = [sn for sn in scored_news if sn.score >= min_score]
        
        if grade:
            filtered = [sn for sn in filtered if sn.grade.value == grade]
        
        if category:
            filtered = [sn for sn in filtered if sn.news.category.value == category]
        
        # 统计
        grade_stats = {"S": 0, "A": 0, "B": 0, "C": 0}
        for sn in scored_news:
            grade_stats[sn.grade.value] = grade_stats.get(sn.grade.value, 0) + 1
        
        # 转换为响应格式
        scored_data = [
            {
                "id": sn.news.id,
                "title": sn.news.title,
                "content": sn.news.content,
                "category": sn.news.category.value,
                "source": sn.news.source.name,
                "score": sn.score,
                "grade": sn.grade.value,
                "score_details": sn.score_details,
                "backtest_evidence": sn.backtest_evidence,
                "recommendation": sn.recommendation,
                "related_tickers": sn.news.related_tickers,
                "related_themes": sn.news.related_themes,
                "publish_time": sn.news.publish_time.isoformat() if sn.news.publish_time else None,
            }
            for sn in filtered
        ]
        
        return DataResponse(
            data={
                "trade_date": target_date.isoformat(),
                "total_scored": len(scored_news),
                "filtered_count": len(filtered),
                "grade_statistics": grade_stats,
                "scored_news": scored_data,
            }
        )
    except Exception as e:
        logger.error(f"获取已评分资讯失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分资讯失败: {str(e)}")


@router.get("/recommendations", response_model=DataResponse)
async def get_entry_recommendations(
    trade_date: Optional[str] = Query(None, description="交易日 (YYYY-MM-DD)"),
    min_score: float = Query(50.0, description="最低影响力评分"),
    urgency: Optional[str] = Query(None, description="紧急程度过滤: urgent/normal/low"),
    use_mock: bool = Query(True, description="是否使用模拟数据"),
):
    """获取利好介入建议
    
    基于历史回测数据，对研判为重要利好的资讯提供操作建议:
    - 介入时机: 集合竞价/开盘后/盘中回调
    - 建议仓位: 基于影响力评分动态计算
    - 持有周期: 基于消息类型最优持有天数
    - 止盈止损: 基于历史收益/回撤数据
    
    Returns:
        利好介入建议列表（按紧急程度排序）
    """
    import asyncio
    
    logger.info(f"获取利好介入建议: min_score={min_score}")
    
    try:
        target_date = date.fromisoformat(trade_date) if trade_date else date.today()
        
        # 采集并评分
        collector = _get_news_collector()
        collector._use_mock = use_mock
        
        news_items = await collector.collect_news(target_date)
        scored_news = collector.score_news(news_items)
        
        # 生成介入建议
        rec_engine = _get_recommendation_engine()
        market_context = {"emotion_cycle": "发酵期"}  # 可从其他模块获取
        
        result = rec_engine.analyze(scored_news, market_context)
        
        # 过滤
        recommendations = result["entry_recommendations"]
        if min_score > 0:
            recommendations = [r for r in recommendations if r["impact_score"] >= min_score]
        
        if urgency:
            recommendations = [r for r in recommendations if r["urgency"] == urgency]
        
        return DataResponse(
            data={
                "trade_date": target_date.isoformat(),
                "summary": result["summary"],
                "total_recommendations": len(recommendations),
                "statistics": result["statistics"],
                "recommendations": recommendations,
            }
        )
    except Exception as e:
        logger.error(f"获取利好介入建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取介入建议失败: {str(e)}")


@router.get("/risk-alerts", response_model=DataResponse)
async def get_risk_alerts(
    trade_date: Optional[str] = Query(None, description="交易日 (YYYY-MM-DD)"),
    severity: Optional[str] = Query(None, description="严重程度过滤: extreme/high/medium/low"),
    use_mock: bool = Query(True, description="是否使用模拟数据"),
):
    """获取利空风险预警
    
    基于历史回测数据，对重大利空资讯提供风险预警:
    - 风险类型: 业绩风险/筹码风险/合规风险/财务风险等
    - 严重程度: extreme(极端)/high(高)/medium(中)/low(低)
    - 预期亏损: 基于历史平均下跌幅度
    - 应对建议: 绝对禁入/高度谨慎/谨慎对待
    
    Returns:
        利空风险预警列表（按严重程度排序）
    """
    import asyncio
    
    logger.info(f"获取利空风险预警: severity={severity}")
    
    try:
        target_date = date.fromisoformat(trade_date) if trade_date else date.today()
        
        # 采集并评分
        collector = _get_news_collector()
        collector._use_mock = use_mock
        
        news_items = await collector.collect_news(target_date)
        scored_news = collector.score_news(news_items)
        
        # 生成风险预警
        rec_engine = _get_recommendation_engine()
        market_context = {"emotion_cycle": "发酵期"}
        
        result = rec_engine.analyze(scored_news, market_context)
        
        # 过滤
        alerts = result["risk_alerts"]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return DataResponse(
            data={
                "trade_date": target_date.isoformat(),
                "summary": result["summary"],
                "total_alerts": len(alerts),
                "statistics": result["statistics"],
                "risk_alerts": alerts,
            }
        )
    except Exception as e:
        logger.error(f"获取利空风险预警失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取风险预警失败: {str(e)}")


@router.get("/analysis", response_model=DataResponse)
async def get_comprehensive_analysis(
    trade_date: Optional[str] = Query(None, description="交易日 (YYYY-MM-DD)"),
    use_mock: bool = Query(True, description="是否使用模拟数据"),
):
    """综合分析 — 利好介入建议 + 利空风险预警
    
    整合所有分析结果，提供完整的操作指导:
    - 利好介入建议（按紧急程度排序）
    - 利空风险预警（按严重程度排序）
    - 综合摘要
    - 统计数据
    
    Returns:
        完整分析结果
    """
    import asyncio
    
    logger.info(f"获取综合分析: trade_date={trade_date}")
    
    try:
        target_date = date.fromisoformat(trade_date) if trade_date else date.today()
        
        # 采集并评分
        collector = _get_news_collector()
        collector._use_mock = use_mock
        
        news_items = await collector.collect_news(target_date)
        scored_news = collector.score_news(news_items)
        
        # 综合分析
        rec_engine = _get_recommendation_engine()
        market_context = {"emotion_cycle": "发酵期"}
        
        result = rec_engine.analyze(scored_news, market_context)
        
        # 添加评分统计
        grade_stats = {"S": 0, "A": 0, "B": 0, "C": 0}
        for sn in scored_news:
            grade_stats[sn.grade.value] = grade_stats.get(sn.grade.value, 0) + 1
        
        result["grade_statistics"] = grade_stats
        result["total_news"] = len(news_items)
        result["trade_date"] = target_date.isoformat()
        
        return DataResponse(data=result)
    except Exception as e:
        logger.error(f"综合分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"综合分析失败: {str(e)}")


@router.get("/backtest/profiles", response_model=DataResponse)
async def get_backtest_profiles(
    direction: Optional[str] = Query(None, description="方向过滤: bullish/bearish/neutral"),
):
    """获取消息类型回测画像
    
    返回所有消息类型的历史回测数据:
    - 胜率、平均收益、最大回撤
    - 影响力评分、影响等级
    - 最佳操作策略、最优持有天数
    - 关键词列表
    
    Returns:
        消息类型画像字典
    """
    logger.info(f"获取回测画像: direction={direction}")
    
    try:
        engine = _get_backtest_engine()
        summary = engine.get_backtest_summary()
        
        # 过滤
        profiles = summary["profiles"]
        if direction:
            profiles = {
                k: v for k, v in profiles.items()
                if v.get("direction") == direction
            }
        
        return DataResponse(
            data={
                "total_types": len(profiles),
                "bullish_count": sum(1 for p in profiles.values() if p.get("direction") == "bullish"),
                "bearish_count": sum(1 for p in profiles.values() if p.get("direction") == "bearish"),
                "neutral_count": sum(1 for p in profiles.values() if p.get("direction") == "neutral"),
                "profiles": profiles,
            }
        )
    except Exception as e:
        logger.error(f"获取回测画像失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取回测画像失败: {str(e)}")


@router.get("/sources/status", response_model=DataResponse)
async def get_sources_status():
    """获取资讯来源状态
    
    返回所有资讯来源的当前状态:
    - 是否启用
    - 是否使用模拟数据
    - 最后采集时间
    - 可信度评分
    - 覆盖的资讯分类
    
    Returns:
        来源状态字典
    """
    logger.info("获取资讯来源状态")
    
    try:
        fetcher = _get_multi_fetcher()
        status = fetcher.get_source_status()
        
        return DataResponse(
            data={
                "total_sources": len(status),
                "sources": status,
            }
        )
    except Exception as e:
        logger.error(f"获取来源状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取来源状态失败: {str(e)}")


# ──────────────────────────────────────────────────────────
# 兼容旧版路由
# ──────────────────────────────────────────────────────────

def _generate_mock_news(count: int = 30) -> List[Dict]:
    """生成模拟最新资讯（兼容旧版）"""
    news_items = [
        {"title": "OpenAI发布GPT-5模型，AI算力需求再迎爆发", "category": "科技", "impact": "high",
         "related_sectors": ["人工智能", "算力", "光模块"]},
        {"title": "六部门发文支持新能源汽车下乡", "category": "政策", "impact": "high",
         "related_sectors": ["新能源汽车", "充电桩", "锂电池"]},
        {"title": "美联储维持利率不变，市场预期年内降息3次", "category": "宏观", "impact": "medium",
         "related_sectors": ["银行", "地产", "黄金"]},
        {"title": "华为发布新一代AI芯片，性能提升40%", "category": "科技", "impact": "high",
         "related_sectors": ["芯片设计", "先进封装", "半导体设备"]},
        {"title": "证监会就活跃资本市场发布一揽子政策", "category": "政策", "impact": "high",
         "related_sectors": ["券商", "保险", "银行"]},
    ]
    
    news = []
    base_time = datetime.now()
    for i in range(count):
        item = random.choice(news_items)
        pub_time = base_time - timedelta(hours=random.randint(0, 72))
        news.append({
            "id": f"N{i+1:04d}",
            "title": item["title"],
            "category": item["category"],
            "impact": item["impact"],
            "related_sectors": item["related_sectors"],
            "source": random.choice(["财联社", "证券时报", "上海证券报"]),
            "publish_time": pub_time.isoformat(),
            "is_important": item["impact"] == "high",
        })
    
    news.sort(key=lambda x: x["publish_time"], reverse=True)
    return news


def _generate_risk_list() -> List[Dict]:
    """生成避雷清单（兼容旧版）"""
    return [
        {"ticker": "600XXX.SH", "name": "某问题公司", "risk_type": "退市风险", "level": "高危",
         "description": "连续3年亏损，可能被实施退市风险警示", "action": "立即回避"},
        {"ticker": "002XXX.SZ", "name": "某ST公司", "risk_type": "财务造假", "level": "高危",
         "description": "涉嫌信息披露违法违规被证监会立案调查", "action": "坚决回避"},
        {"ticker": "300XXX.SZ", "name": "某高质押公司", "risk_type": "股权质押", "level": "中危",
         "description": "大股东质押比例超过80%，存在平仓风险", "action": "谨慎对待"},
    ]


def _generate_pre_market_summary() -> Dict:
    """生成盘前汇总（兼容旧版）"""
    return {
        "date": date.today().isoformat(),
        "overseas_markets": {
            "道琼斯": {"close": 35000.0, "change_pct": 0.5},
            "纳斯达克": {"close": 14000.0, "change_pct": 1.0},
        },
        "key_news": [
            {"title": "美联储会议纪要显示多数官员支持年内降息", "impact": "偏多"},
        ],
        "sentiment_indicator": "偏多",
    }


@router.get("/latest", response_model=Dict)
async def get_latest_news(
    category: Optional[str] = Query(None, description="类别过滤"),
    impact: Optional[str] = Query(None, description="影响级别过滤: high/medium/low"),
    limit: int = Query(30, ge=1, le=100),
):
    """获取最新资讯（兼容旧版）"""
    try:
        news = _generate_mock_news(count=limit)
        
        if category:
            news = [n for n in news if n["category"] == category]
        if impact:
            news = [n for n in news if n["impact"] == impact]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "news": news,
                "total": len(news),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资讯失败: {str(e)}")


@router.get("/risk-list", response_model=Dict)
async def get_risk_list(
    level: Optional[str] = Query(None, description="风险级别过滤: 高危/中危/低危"),
):
    """获取避雷清单（兼容旧版）"""
    try:
        risks = _generate_risk_list()
        
        if level:
            risks = [r for r in risks if r["level"] == level]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "risks": risks,
                "total": len(risks),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取避雷清单失败: {str(e)}")


@router.get("/pre-market", response_model=Dict)
async def get_pre_market_summary():
    """获取盘前汇总（兼容旧版）"""
    try:
        summary = _generate_pre_market_summary()
        
        return {
            "code": 200,
            "message": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取盘前汇总失败: {str(e)}")