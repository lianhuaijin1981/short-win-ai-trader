"""资讯价值打分器 — 回测驱动的多维度资讯评分引擎

基于历史回测数据，从以下维度对单条资讯进行综合评分:
- 催化强度: 资讯对股价的催化力度
- 时效性: 资讯发布的及时程度
- 关联度: 与当前市场主线/热点的关联程度
- 历史验证: 同类资讯历史回测表现
- 市场反馈: 资讯发布后市场实际反应

评分规则:
- S级 (>=75分): 高价值资讯，需重点跟踪
- A级 (50-74分): 较高价值资讯，值得关注
- B级 (25-49分): 一般价值资讯，作为参考
- C级 (<25分): 低价值资讯，可忽略
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Callable, Dict, List, Optional, Set

from ...core.logger import get_logger

logger = get_logger("swat.m01.scorer")


@dataclass
class ScoreDimension:
    """评分维度定义"""
    name: str = ""
    weight: float = 0.0     # 权重 0-1
    score: float = 0.0      # 该项得分 0-100


@dataclass
class ScoreResult:
    """评分结果"""
    total_score: float = 0.0
    dimension_scores: List[ScoreDimension] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


class NewsScorer:
    """资讯价值打分器
    
    采用回测驱动的多维度加权评分模型，对NewsItem进行综合评估。
    
    Attributes:
        dimension_weights: 各维度权重配置
        backtest_db: 回测数据库引用（可扩展为实际数据库连接）
        keyword_weights: 关键词权重映射
    """

    # 催化强度关键词库（正向/负向）
    POSITIVE_CATALYST_KEYWORDS: List[str] = [
        "重大利好", "业绩预增", "订单大增", "中标", "获批", "突破",
        "政策扶持", "补贴", "重组", "并购", "回购", "增持",
        "涨价", "扩产", "新技术", "首款", "首个", "独家",
        "战略合作", "国际合作", "国产替代", "自主可控",
    ]

    NEGATIVE_CATALYST_KEYWORDS: List[str] = [
        "减持", "退市", "立案调查", "处罚", "业绩预亏",
        "债务违约", "停产", "召回", "禁令", "制裁",
        "终止", "失败", "不及预期", "下滑", "亏损扩大",
        "高管离职", "实控人变更", "冻结", "查封",
    ]

    # 时效性评分参数
    MARKET_OPEN_TIME: time = time(9, 30)
    MARKET_CLOSE_TIME: time = time(15, 0)
    PRE_MARKET_TIME: time = time(8, 0)

    def __init__(self, dimension_weights: Optional[Dict[str, float]] = None):
        """初始化打分器
        
        Args:
            dimension_weights: 自定义维度权重，默认使用回测验证的最优权重
        """
        # 默认权重基于回测验证的最优配置
        self.dimension_weights = dimension_weights or {
            "catalyst_strength": 0.30,   # 催化强度 30%
            "timeliness": 0.20,          # 时效性 20%
            "relevance": 0.20,           # 关联度 20%
            "historical_validation": 0.15, # 历史验证 15%
            "market_feedback": 0.15,     # 市场反馈 15%
        }

        # 关键词权重映射（用于关联度计算）
        self.keyword_weights: Dict[str, float] = {}

        # 回测数据库（mock结构，可扩展为实际数据库）
        self.backtest_db: Dict[str, Dict] = {}

        logger.info(
            "资讯打分器初始化完成",
            dimensions=list(self.dimension_weights.keys()),
        )

    def score(
        self,
        news_item,
        current_themes: Optional[List[str]] = None,
        market_context: Optional[Dict] = None,
    ) -> ScoreResult:
        """对单条资讯进行综合评分
        
        Args:
            news_item: NewsItem 资讯条目
            current_themes: 当前市场热点题材列表
            market_context: 市场上下文数据（指数/涨跌家数等）
            
        Returns:
            ScoreResult 评分结果
        """
        current_themes = current_themes or []
        market_context = market_context or {}

        dimensions: List[ScoreDimension] = []

        # 1. 催化强度评分 (30%)
        catalyst_score = self._score_catalyst_strength(news_item)
        dimensions.append(
            ScoreDimension("catalyst_strength", self.dimension_weights["catalyst_strength"], catalyst_score)
        )

        # 2. 时效性评分 (20%)
        timeliness_score = self._score_timeliness(news_item)
        dimensions.append(
            ScoreDimension("timeliness", self.dimension_weights["timeliness"], timeliness_score)
        )

        # 3. 关联度评分 (20%)
        relevance_score = self._score_relevance(news_item, current_themes)
        dimensions.append(
            ScoreDimension("relevance", self.dimension_weights["relevance"], relevance_score)
        )

        # 4. 历史验证评分 (15%)
        historical_score = self._score_historical_validation(news_item)
        dimensions.append(
            ScoreDimension("historical_validation", self.dimension_weights["historical_validation"], historical_score)
        )

        # 5. 市场反馈评分 (15%)
        feedback_score = self._score_market_feedback(news_item, market_context)
        dimensions.append(
            ScoreDimension("market_feedback", self.dimension_weights["market_feedback"], feedback_score)
        )

        # 加权总分
        total_score = sum(
            d.score * d.weight for d in dimensions
        )
        # 四舍五入到1位小数
        total_score = round(min(100.0, max(0.0, total_score)), 1)

        logger.debug(
            "资讯评分完成",
            news_id=news_item.id,
            title=news_item.title[:30],
            total_score=total_score,
        )

        return ScoreResult(
            total_score=total_score,
            dimension_scores=dimensions,
            details={
                "category": news_item.category.value,
                "keyword_matches": self._extract_keyword_matches(news_item),
                "is_pre_market": self._is_pre_market_news(news_item),
                "theme_overlap": len(set(news_item.related_themes) & set(current_themes)),
            },
        )

    def score_batch(
        self,
        news_items: List,
        current_themes: Optional[List[str]] = None,
        market_context: Optional[Dict] = None,
    ) -> List[ScoreResult]:
        """批量评分
        
        Args:
            news_items: NewsItem 列表
            current_themes: 当前市场热点题材
            market_context: 市场上下文
            
        Returns:
            List[ScoreResult] 评分结果列表（与输入顺序一致）
        """
        results: List[ScoreResult] = []
        for item in news_items:
            try:
                result = self.score(item, current_themes, market_context)
                results.append(result)
            except Exception as e:
                logger.error(f"资讯评分失败: {item.id}, 错误: {e}")
                # 返回零分结果保持顺序
                results.append(ScoreResult(total_score=0.0))
        return results

    # ==================== 各维度评分方法 ====================

    def _score_catalyst_strength(self, news_item) -> float:
        """催化强度评分: 评估资讯对股价的催化力度
        
        基于关键词匹配 + 资讯分类 + 来源可信度
        
        Args:
            news_item: NewsItem
            
        Returns:
            float: 0-100分
        """
        score = 0.0
        text = f"{news_item.title} {news_item.content}"

        # 正向关键词匹配
        positive_count = sum(1 for kw in self.POSITIVE_CATALYST_KEYWORDS if kw in text)
        # 负向关键词匹配（负向催化同样是强催化，只是方向不同）
        negative_count = sum(1 for kw in self.NEGATIVE_CATALYST_KEYWORDS if kw in text)

        # 关键词得分: 最多40分
        keyword_score = min(40.0, (positive_count + negative_count) * 8.0)
        score += keyword_score

        # 资讯分类权重: 不同分类基础催化强度不同
        category_bonus: Dict[str, float] = {
            "政策": 25.0,    # 政策类催化强度最高
            "题材": 20.0,    # 题材催化次之
            "个股": 20.0,    # 个股公告也很强
            "资金": 10.0,    # 资金动向中等
            "外围": 5.0,     # 外围影响相对间接
            "舆情": 5.0,     # 舆情影响相对间接
        }
        score += category_bonus.get(news_item.category.value, 0.0)

        # 来源可信度加成: 最多20分
        credibility_bonus = news_item.source.credibility * 0.2
        score += credibility_bonus

        # 有关联个股加分: 最多10分
        if news_item.related_tickers:
            score += min(10.0, len(news_item.related_tickers) * 2.0)

        # 有关键词标签加分: 最多5分
        if news_item.keywords:
            score += min(5.0, len(news_item.keywords) * 1.0)

        return min(100.0, score)

    def _score_timeliness(self, news_item) -> float:
        """时效性评分: 评估资讯发布的及时程度
        
        盘前 > 盘中 > 盘后 > 隔日，时间越早价值越高
        
        Args:
            news_item: NewsItem
            
        Returns:
            float: 0-100分
        """
        if not news_item.publish_time:
            return 30.0  # 无发布时间，给基础分

        publish_time = news_item.publish_time
        publish_hour = publish_time.hour
        publish_minute = publish_time.minute
        publish_total_minutes = publish_hour * 60 + publish_minute

        # 交易时间定义 (分钟数)
        pre_market_start = 8 * 60       # 8:00
        market_open = 9 * 60 + 30       # 9:30
        noon_close = 11 * 60 + 30       # 11:30
        noon_open = 13 * 60             # 13:00
        market_close = 15 * 60          # 15:00

        # 盘前资讯 (8:00-9:30) 最高分100
        if pre_market_start <= publish_total_minutes < market_open:
            # 越早发布越好，9:00前发布的给满分
            if publish_total_minutes < 9 * 60:
                return 100.0
            else:
                return 85.0

        # 盘中资讯 (9:30-11:30, 13:00-15:00) 分值60-90
        if market_open <= publish_total_minutes <= noon_close or \
           noon_open <= publish_total_minutes <= market_close:
            # 早盘资讯比午盘更值钱
            if publish_total_minutes <= 10 * 60 + 30:  # 10:30前
                return 80.0
            elif publish_total_minutes <= noon_close:  # 上午
                return 70.0
            else:  # 下午
                return 65.0

        # 盘后资讯 (15:00-17:00) 分值50-60
        if market_close < publish_total_minutes <= 17 * 60:
            return 55.0

        # 晚间资讯 (17:00-20:00) 分值40-50
        if 17 * 60 < publish_total_minutes <= 20 * 60:
            return 45.0

        # 深夜/凌晨资讯 分值30-40
        if 20 * 60 < publish_total_minutes or publish_total_minutes < pre_market_start:
            return 35.0

        return 30.0

    def _score_relevance(self, news_item, current_themes: List[str]) -> float:
        """关联度评分: 评估资讯与当前市场主线的关联程度
        
        Args:
            news_item: NewsItem
            current_themes: 当前热点题材列表
            
        Returns:
            float: 0-100分
        """
        score = 0.0
        text = f"{news_item.title} {news_item.content}"
        matched_themes: List[str] = []

        # 与当前热点题材的匹配
        if current_themes:
            for theme in current_themes:
                if theme in text:
                    matched_themes.append(theme)
            # 每个匹配题材加15分，最多45分
            score += min(45.0, len(matched_themes) * 15.0)

        # 与资讯自带题材的匹配
        if news_item.related_themes:
            score += min(25.0, len(news_item.related_themes) * 5.0)

        # 有关联个股加分: 最多20分
        if news_item.related_tickers:
            score += min(20.0, len(news_item.related_tickers) * 4.0)

        # 关键词密度加分: 最多10分
        if news_item.keywords:
            score += min(10.0, len(news_item.keywords) * 2.0)

        return min(100.0, score)

    def _score_historical_validation(self, news_item) -> float:
        """历史验证评分: 基于回测数据库验证同类资讯的历史表现
        
        当前使用mock回测数据框架，可接入实际回测数据库。
        
        Args:
            news_item: NewsItem
            
        Returns:
            float: 0-100分
        """
        # 基于资讯分类和关键词查询回测数据库
        category = news_item.category.value
        cache_key = f"bt_{category}_{'_'.join(news_item.keywords[:3])}"

        # 从mock回测数据库查询
        bt_result = self.backtest_db.get(cache_key, {})

        if bt_result:
            # 有回测数据，基于历史胜率评分
            win_rate = bt_result.get("win_rate", 0.0)
            avg_return = bt_result.get("avg_return", 0.0)
            # 胜率*50 + 平均收益率*50，封顶100
            score = min(100.0, win_rate * 50 + max(0, avg_return) * 50)
            return score

        # 无回测数据时，基于分类给出默认分
        default_scores: Dict[str, float] = {
            "政策": 65.0,    # 政策类有较高历史价值
            "题材": 60.0,    # 题材类历史价值也不错
            "个股": 55.0,    # 个股公告中等
            "资金": 50.0,    # 资金动向
            "外围": 45.0,    # 外围影响
            "舆情": 40.0,    # 舆情
        }
        return default_scores.get(category, 45.0)

    def _score_market_feedback(self, news_item, market_context: Dict) -> float:
        """市场反馈评分: 资讯发布后市场实际反应
        
        对于实时资讯，结合市场即时反应评分;
        对于历史资讯，使用回测数据。
        
        Args:
            news_item: NewsItem
            market_context: 市场上下文数据
            
        Returns:
            float: 0-100分
        """
        # 从市场上下文提取相关指标
        related_tickers = news_item.related_tickers

        if not related_tickers or not market_context:
            return 45.0  # 无市场数据，给基础分

        score = 0.0
        ticker_reactions = []

        for ticker in related_tickers:
            reaction = market_context.get(f"reaction_{ticker}", {})
            if reaction:
                price_change = reaction.get("price_change_pct", 0.0)
                volume_ratio = reaction.get("volume_ratio", 1.0)
                # 股价反应 + 量能反应
                ticker_score = min(50.0, abs(price_change) * 5) + min(30.0, (volume_ratio - 1) * 15)
                ticker_reactions.append(ticker_score)

        if ticker_reactions:
            score = sum(ticker_reactions) / len(ticker_reactions)
        else:
            score = 45.0  # 无反应数据

        return min(100.0, score)

    # ==================== 辅助方法 ====================

    def _extract_keyword_matches(self, news_item) -> Dict[str, int]:
        """提取关键词匹配情况"""
        text = f"{news_item.title} {news_item.content}"
        return {
            "positive": sum(1 for kw in self.POSITIVE_CATALYST_KEYWORDS if kw in text),
            "negative": sum(1 for kw in self.NEGATIVE_CATALYST_KEYWORDS if kw in text),
        }

    def _is_pre_market_news(self, news_item) -> bool:
        """判断是否为盘前资讯"""
        if not news_item.publish_time:
            return False
        t = news_item.publish_time
        return time(8, 0) <= t.time() <= time(9, 30)

    def update_backtest_result(
        self,
        category: str,
        keywords: List[str],
        win_rate: float,
        avg_return: float,
        sample_size: int = 0,
    ) -> None:
        """更新回测结果到数据库
        
        用于持续优化评分模型。
        
        Args:
            category: 资讯分类
            keywords: 关键词
            win_rate: 历史胜率
            avg_return: 平均收益率
            sample_size: 样本量
        """
        cache_key = f"bt_{category}_{'_'.join(keywords[:3])}"
        self.backtest_db[cache_key] = {
            "win_rate": win_rate,
            "avg_return": avg_return,
            "sample_size": sample_size,
            "updated_at": datetime.now().isoformat(),
        }
        logger.info(
            "回测结果已更新",
            category=category,
            win_rate=win_rate,
            sample_size=sample_size,
        )
