"""资讯路由 — 最新资讯、避雷清单、盘前汇总

提供A股市场资讯聚合:
- GET /news/latest — 最新资讯
- GET /news/risk-list — 避雷清单
- GET /news/pre-market — 盘前汇总
"""

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.core.config import APIConfig
from api.core.logger import get_logger

logger = get_logger("swat.router.news")
config = APIConfig()

router = APIRouter(prefix="/news", tags=["News"])

# ── 模拟资讯数据 ────────────────────────────────────────


def _generate_mock_news(count: int = 30) -> List[Dict]:
    """生成模拟最新资讯"""
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
        {"title": "某新能源车企宣布降价10%，行业价格战持续", "category": "行业", "impact": "medium",
         "related_sectors": ["新能源汽车", "汽车零部件"]},
        {"title": "科创板首批企业半年报业绩亮眼", "category": "财报", "impact": "medium",
         "related_sectors": ["半导体", "生物医药", "高端装备"]},
        {"title": "国常会：审议通过促进消费若干措施", "category": "政策", "impact": "medium",
         "related_sectors": ["白酒", "消费电子", "免税"]},
        {"title": "北向资金连续5日净流入，累计超200亿", "category": "资金", "impact": "medium",
         "related_sectors": ["核心资产", "白马股"]},
        {"title": "光模块龙头获海外大客户追加订单", "category": "公司", "impact": "high",
         "related_sectors": ["光模块", "光通信"]},
        {"title": "工信部：加快6G技术研发，推进卫星互联网建设", "category": "政策", "impact": "medium",
         "related_sectors": ["卫星通信", "6G", "通信设备"]},
        {"title": "多家上市公司发布回购计划", "category": "公司", "impact": "low",
         "related_sectors": ["综合"]},
        {"title": "美国拟限制对华AI芯片出口，国产替代加速", "category": "国际", "impact": "high",
         "related_sectors": ["芯片设计", "半导体设备", "EDA"]},
        {"title": "某医药公司新药获批上市，市场空间超百亿", "category": "公司", "impact": "high",
         "related_sectors": ["创新药", "CRO"]},
        {"title": "房地产投资数据持续低迷，政策底已现", "category": "宏观", "impact": "medium",
         "related_sectors": ["地产", "建材", "家电"]},
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
            "source": random.choice(["财联社", "证券时报", "上海证券报", "每日经济新闻", "华尔街见闻"]),
            "publish_time": pub_time.isoformat(),
            "url": "",
            "is_important": item["impact"] == "high",
        })

    news.sort(key=lambda x: x["publish_time"], reverse=True)
    return news


def _generate_risk_list() -> List[Dict]:
    """生成避雷清单"""
    risks = [
        {"ticker": "600XXX.SH", "name": "某问题公司", "risk_type": "退市风险", "level": "高危",
         "description": "连续3年亏损，可能被实施退市风险警示", "action": "立即回避"},
        {"ticker": "002XXX.SZ", "name": "某ST公司", "risk_type": "财务造假", "level": "高危",
         "description": "涉嫌信息披露违法违规被证监会立案调查", "action": "坚决回避"},
        {"ticker": "300XXX.SZ", "name": "某高质押公司", "risk_type": "股权质押", "level": "中危",
         "description": "大股东质押比例超过80%，存在平仓风险", "action": "谨慎对待"},
        {"ticker": "688XXX.SH", "name": "某解禁股", "risk_type": "大额解禁", "level": "中危",
         "description": "下周解禁市值超50亿，占总股本30%", "action": "注意回避"},
        {"ticker": "000XXX.SZ", "name": "某减持股", "risk_type": "股东减持", "level": "低危",
         "description": "控股股东计划减持不超过3%股份", "action": "关注走势"},
        {"ticker": "601XXX.SH", "name": "某业绩暴雷", "risk_type": "业绩预亏", "level": "高危",
         "description": "Q2业绩预亏超5亿，远超市场预期", "action": "立即回避"},
        {"ticker": "603XXX.SH", "name": "某监管股", "risk_type": "监管函", "level": "中危",
         "description": "收到交易所问询函，要求说明关联交易", "action": "谨慎对待"},
        {"ticker": "002XXX.SZ", "name": "某违约股", "risk_type": "债务违约", "level": "高危",
         "description": "公司债券未能按期兑付，构成实质违约", "action": "坚决回避"},
    ]
    return risks


def _generate_pre_market_summary() -> Dict:
    """生成盘前汇总"""
    # 隔夜外盘
    overseas = {
        "道琼斯": {"close": round(35000 + random.uniform(-500, 500), 2), "change_pct": round(random.uniform(-1.5, 1.5), 2)},
        "纳斯达克": {"close": round(14000 + random.uniform(-300, 300), 2), "change_pct": round(random.uniform(-2, 2), 2)},
        "标普500": {"close": round(4500 + random.uniform(-60, 60), 2), "change_pct": round(random.uniform(-1.5, 1.5), 2)},
        "恒生期指": {"close": round(18000 + random.uniform(-300, 300), 2), "change_pct": round(random.uniform(-2, 2), 2)},
        "A50期指": {"close": round(13000 + random.uniform(-200, 200), 2), "change_pct": round(random.uniform(-1.5, 1.5), 2)},
    }

    # 重要资讯
    key_news = [
        {"title": "美联储会议纪要显示多数官员支持年内降息", "impact": "偏多", "sector": "全球市场"},
        {"title": "国资委：推动央企加快布局人工智能产业", "impact": "偏多", "sector": "人工智能/央企"},
        {"title": "工信部发布光模块行业白皮书，2026年市场规模有望达千亿", "impact": "偏多", "sector": "光模块"},
        {"title": "某大型房企债务重组方案获通过", "impact": "中性", "sector": "房地产"},
        {"title": "美股科技股集体回调，英伟达跌超5%", "impact": "偏空", "sector": "AI/芯片"},
    ]

    # 今日关注
    today_focus = [
        {"event": "统计局发布7月CPI/PPI数据", "time": "09:30", "impact": "宏观"},
        {"event": "某某科技新股申购", "time": "09:15", "impact": "新股"},
        {"event": "美联储官员发表讲话", "time": "22:00", "impact": "外盘"},
    ]

    # 板块前瞻
    sector_outlook = [
        {"sector": "光模块/CPO", "outlook": "强势", "reason": "海外订单持续超预期"},
        {"sector": "新能源汽车", "outlook": "分化", "reason": "价格战持续，关注龙头"},
        {"sector": "消费电子", "outlook": "积极", "reason": "新品发布周期到来"},
        {"sector": "白酒", "outlook": "弱势", "reason": "消费复苏不及预期"},
        {"sector": "房地产", "outlook": "承压", "reason": "政策效果有待观察"},
    ]

    return {
        "date": date.today().isoformat(),
        "overseas_markets": overseas,
        "key_news": key_news,
        "today_focus": today_focus,
        "sector_outlook": sector_outlook,
        "sentiment_indicator": random.choice(["偏多", "中性偏多", "中性", "中性偏空", "偏空"]),
        "trading_strategy": random.choice([
            "关注光模块、消费电子等主线机会",
            "控制仓位，等待市场方向明朗",
            "积极布局AI产业链",
            "防守为主，关注高股息标的",
        ]),
    }


# ── 路由 ────────────────────────────────────────────────


@router.get("/latest", response_model=Dict)
async def get_latest_news(
    category: Optional[str] = Query(None, description="类别过滤: 科技/政策/宏观/行业/公司/国际"),
    impact: Optional[str] = Query(None, description="影响级别过滤: high/medium/low"),
    limit: int = Query(30, ge=1, le=100),
    sector: Optional[str] = Query(None, description="关联板块过滤"),
):
    """获取最新资讯

    返回最新A股市场资讯，支持按类别、影响级别、板块过滤。
    """
    logger.info(f"GET /news/latest category={category} impact={impact} limit={limit}")

    try:
        news = _generate_mock_news(count=limit)

        if category:
            news = [n for n in news if n["category"] == category]
        if impact:
            news = [n for n in news if n["impact"] == impact]
        if sector:
            news = [n for n in news if sector in n.get("related_sectors", [])]

        # 统计
        category_counts = {}
        for n in news:
            cat = n["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        important = [n for n in news if n.get("is_important")]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "news": news,
                "total": len(news),
                "important_count": len(important),
                "category_distribution": category_counts,
                "important_news": important[:5],
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"News query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取资讯失败: {str(e)}")


@router.get("/risk-list", response_model=Dict)
async def get_risk_list(
        level: Optional[str] = Query(None, description="风险级别过滤: 高危/中危/低危"),
        risk_type: Optional[str] = Query(None, description="风险类型过滤"),
):
    """获取避雷清单

    返回存在风险的股票清单，包括退市风险、财务造假、高质押、大额解禁等。
    """
    logger.info(f"GET /news/risk-list level={level} type={risk_type}")

    try:
        risks = _generate_risk_list()

        if level:
            risks = [r for r in risks if r["level"] == level]
        if risk_type:
            risks = [r for r in risks if r["risk_type"] == risk_type]

        # 统计
        level_counts = {}
        type_counts = {}
        for r in risks:
            level_counts[r["level"]] = level_counts.get(r["level"], 0) + 1
            type_counts[r["risk_type"]] = type_counts.get(r["risk_type"], 0) + 1

        high_risks = [r for r in risks if r["level"] == "高危"]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "risks": risks,
                "total": len(risks),
                "high_risk_count": len(high_risks),
                "statistics": {
                    "by_level": level_counts,
                    "by_type": type_counts,
                },
                "high_risk_stocks": high_risks,
                "disclaimer": "本清单仅供参考，不构成投资建议。投资有风险，入市需谨慎。",
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Risk list query failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取避雷清单失败: {str(e)}")


@router.get("/pre-market", response_model=Dict)
async def get_pre_market_summary():
    """获取盘前汇总

    返回每日盘前关键信息汇总，包括隔夜外盘、重要资讯、今日关注、板块前瞻等。
    """
    logger.info("GET /news/pre-market")

    try:
        summary = _generate_pre_market_summary()

        return {
            "code": 200,
            "message": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Pre-market summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取盘前汇总失败: {str(e)}")
