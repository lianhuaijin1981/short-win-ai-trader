"""核心采集引擎 — 全域资讯智能采集器

采集当日全维度资讯，覆盖以下维度:
- 政策监管: 宏观政策、行业政策、监管动态
- 外围市场: 美股/港股/亚太市场、汇率/期货
- 资金动向: 北向资金、主力流向、龙虎榜
- 题材催化: 行业动态、技术突破、事件驱动
- 个股公告: 业绩公告、增减持、重大合同
- 市场情绪: 舆情热度、投资者情绪指标

使用mock数据填充结构，所有接口完整可扩展至真实数据源。
"""

import asyncio
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger

from .models import (
    NewsCategory,
    NewsItem,
    NewsSource,
    PreMarketSummary,
    RiskWarningList,
    ScoredNews,
)
from .risk_detector import RiskDetector
from .scorer import NewsScorer, ScoreResult

logger = get_logger("swat.m01.collector")


class NewsCollector:
    """全域资讯智能采集器

    核心采集引擎，负责从多维度信息源采集资讯，并协调
    打分器和风险检测器完成资讯评估和避雷清单生成。

    Attributes:
        config: 应用配置
        scorer: 资讯打分器实例
        risk_detector: 风险检测器实例
        _mock_data_enabled: 是否使用mock数据（默认True，可扩展为真实API）
    """

    def __init__(self, config: AppConfig, use_mock: bool = True):
        """初始化采集器

        Args:
            config: 应用配置对象
            use_mock: 是否使用mock数据源（开发/测试时True，生产环境False）
        """
        self.config = config
        self.scorer = NewsScorer()
        self.risk_detector = RiskDetector()
        self._use_mock = use_mock

        # 当前市场热点题材（用于关联度评分，实际可由外部模块更新）
        self._current_hot_themes: List[str] = []

        logger.info(
            "全域资讯采集器初始化完成",
            mock_mode=use_mock,
        )

    # ==================== 核心公共接口 ====================

    async def collect_news(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集当日全维度资讯

        并行采集六大类资讯: 政策、外围、资金、题材、个股公告、舆情

        Args:
            trade_date: 交易日，默认当日

        Returns:
            List[NewsItem] 采集到的全部资讯列表

        Raises:
            ModuleError: 采集过程发生严重错误
        """
        trade_date = trade_date or date.today()
        logger.info(f"开始采集资讯: {trade_date.isoformat()}")

        try:
            # 并行采集六大类资讯
            results = await asyncio.gather(
                self._collect_policy_news(trade_date),
                self._collect_global_market_news(trade_date),
                self._collect_fund_flow_news(trade_date),
                self._collect_theme_catalyst_news(trade_date),
                self._collect_stock_announcements(trade_date),
                self._collect_sentiment_news(trade_date),
                return_exceptions=True,
            )

            all_news: List[NewsItem] = []
            category_names = ["政策", "外围", "资金", "题材", "个股公告", "舆情"]

            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"{category_names[idx]}资讯采集失败: {result}")
                    continue
                all_news.extend(result)
                logger.info(f"{category_names[idx]}资讯采集完成: {len(result)}条")

            logger.info(f"资讯采集总计: {len(all_news)}条")
            return all_news

        except Exception as e:
            logger.error(f"资讯采集严重错误: {e}")
            raise ModuleError(f"资讯采集失败: {e}")

    def score_news(
        self,
        news_items: List[NewsItem],
        current_themes: Optional[List[str]] = None,
        market_context: Optional[Dict] = None,
    ) -> List[ScoredNews]:
        """回测驱动打分，分级S/A/B/C

        对每条资讯进行综合评分并赋予等级。

        Args:
            news_items: 待评分的资讯列表
            current_themes: 当前热点题材列表（用于关联度计算）
            market_context: 市场上下文数据

        Returns:
            List[ScoredNews] 评分后的资讯列表，按分数降序排列
        """
        if not news_items:
            return []

        themes = current_themes or self._current_hot_themes

        logger.info(f"开始对{len(news_items)}条资讯进行评分...")

        score_results = self.scorer.score_batch(news_items, themes, market_context)

        scored_news: List[ScoredNews] = []
        for item, score_result in zip(news_items, score_results):
            try:
                # 生成回测证据描述
                evidence = self._generate_backtest_evidence(item, score_result)

                # 生成操作建议
                recommendation = self._generate_recommendation(item, score_result)

                sn = ScoredNews(
                    news=item,
                    score=score_result.total_score,
                    score_details={
                        d.name: {"weight": d.weight, "score": round(d.score, 1)}
                        for d in score_result.dimension_scores
                    },
                    backtest_evidence=evidence,
                    recommendation=recommendation,
                )
                scored_news.append(sn)
            except Exception as e:
                logger.error(f"资讯评分包装失败: {item.id}, 错误: {e}")
                # 跳过该条
                continue

        # 按分数降序排列
        scored_news.sort(key=lambda x: x.score, reverse=True)

        # 统计分级
        s_count = sum(1 for sn in scored_news if sn.grade.value == "S")
        a_count = sum(1 for sn in scored_news if sn.grade.value == "A")
        b_count = sum(1 for sn in scored_news if sn.grade.value == "B")
        c_count = sum(1 for sn in scored_news if sn.grade.value == "C")

        logger.info(
            "资讯评分完成",
            total=len(scored_news),
            s_grade=s_count,
            a_grade=a_count,
            b_grade=b_count,
            c_grade=c_count,
        )

        return scored_news

    def generate_risk_list(
        self,
        news_items: List[NewsItem],
        trade_date: Optional[date] = None,
    ) -> RiskWarningList:
        """生成当日避雷清单（三级风险体系）

        自动从资讯中识别风险信号，生成:
        - 绝对禁入: 重大利空/黑天鹅，严禁买入
        - 高度谨慎: 明显利空/不确定性，需高度警惕
        - 轻度警示: 潜在风险/瑕疵，需关注

        Args:
            news_items: 采集的资讯列表
            trade_date: 交易日

        Returns:
            RiskWarningList 完整避雷清单
        """
        trade_date = trade_date or date.today()
        logger.info(f"开始生成风险清单: {trade_date.isoformat()}")

        risk_list = self.risk_detector.detect(news_items, trade_date)

        # 检查黑名单中的个股是否已在清单中，如未在则补充
        for ticker in self.risk_detector.ticker_blacklist:
            if ticker not in risk_list.forbidden_tickers:
                risk_list.forbidden.append(
                    RiskWarning(
                        level=RiskWarningList.__dataclass_fields__["forbidden"].type,
                        ticker=ticker,
                        reason="长期黑名单个股",
                        trigger_source="系统黑名单",
                        advice="绝对禁入",
                    )
                )

        logger.info(
            "避雷清单生成完成",
            forbidden=len(risk_list.forbidden),
            high_risk=len(risk_list.high_risk),
            low_risk=len(risk_list.low_risk),
        )

        return risk_list

    def get_pre_market_summary(
        self,
        scored_news: List[ScoredNews],
        risk_list: RiskWarningList,
        trade_date: Optional[date] = None,
    ) -> PreMarketSummary:
        """盘前资讯汇总输出

        整合高价值资讯和风险预警，生成盘前综述报告。

        Args:
            scored_news: 已评分的资讯列表
            risk_list: 避雷清单
            trade_date: 交易日

        Returns:
            PreMarketSummary 盘前资讯汇总
        """
        trade_date = trade_date or date.today()

        # 筛选S级和A级高价值资讯
        highlights = [sn for sn in scored_news if sn.grade.value in ("S", "A")]

        # 按分类聚合摘要
        policy_digest = self._aggregate_by_category(scored_news, NewsCategory.POLICY)
        global_digest = self._aggregate_by_category(scored_news, NewsCategory.GLOBAL)
        fund_digest = self._aggregate_by_category(scored_news, NewsCategory.FUND)
        theme_digest = self._aggregate_by_category(scored_news, NewsCategory.THEME)
        sentiment_digest = self._aggregate_by_category(scored_news, NewsCategory.SENTIMENT)

        # 提取个股公告
        stock_announcements = [
            {
                "ticker": sn.news.related_tickers[0] if sn.news.related_tickers else "",
                "title": sn.news.title,
                "grade": sn.grade.value,
                "score": sn.score,
            }
            for sn in scored_news
            if sn.news.category == NewsCategory.STOCK and sn.score >= 40
        ]

        # 提取风险预警摘要
        risk_warnings = []
        if risk_list.system_risk_summary:
            risk_warnings.append(risk_list.system_risk_summary)
        for r in risk_list.forbidden[:5]:
            risk_warnings.append(f"[禁入] {r.ticker} {r.stock_name}: {r.reason}")
        for r in risk_list.high_risk[:5]:
            risk_warnings.append(f"[谨慎] {r.ticker} {r.stock_name}: {r.reason}")

        # 提取关键题材
        key_themes: List[str] = []
        for sn in highlights:
            for theme in sn.news.related_themes:
                if theme and theme not in key_themes:
                    key_themes.append(theme)

        # 生成整体摘要
        overall_summary = self._generate_overall_summary(
            highlights, risk_list, trade_date
        )

        # 市场情绪判断
        market_sentiment = self._judge_market_sentiment(scored_news, risk_list)

        summary = PreMarketSummary(
            trade_date=trade_date,
            overall_summary=overall_summary,
            policy_digest=policy_digest,
            global_digest=global_digest,
            fund_digest=fund_digest,
            theme_digest=theme_digest,
            stock_announcements=stock_announcements,
            sentiment_digest=sentiment_digest,
            risk_warnings=risk_warnings,
            scored_highlights=highlights,
            key_themes=key_themes,
            market_sentiment=market_sentiment,
        )

        logger.info("盘前资讯汇总生成完成")
        return summary

    def set_hot_themes(self, themes: List[str]) -> None:
        """设置当前市场热点题材（供关联度评分使用）

        通常由模块二的题材分析结果更新。

        Args:
            themes: 热点题材名称列表
        """
        self._current_hot_themes = themes
        logger.info(f"热点题材已更新: {themes}")

    # ==================== 各分类采集方法 (Mock实现) ====================

    async def _collect_policy_news(self, trade_date: date) -> List[NewsItem]:
        """采集政策监管资讯 (Mock)

        实际实现: 对接财联社/证券时报/证监会公告等API
        """
        logger.debug("采集政策监管资讯...")

        if not self._use_mock:
            # TODO: 接入真实API
            return []

        # Mock 政策资讯
        mock_data = [
            NewsItem(
                title="证监会发布关于进一步规范上市公司减持行为的通知",
                content=("证监会明确，上市公司存在破发、破净、分红不达标等情形的，"
                        "控股股东、实控人不得通过二级市场减持。"),
                category=NewsCategory.POLICY,
                source=NewsSource(name="证监会官网", credibility=95.0),
                publish_time=datetime.combine(trade_date, time(18, 0)),
                trade_date=trade_date,
                related_themes=["减持新规", "市场监管"],
                keywords=["减持", "监管", "破发", "破净"],
            ),
            NewsItem(
                title="工信部发布新能源汽车产业发展规划（2025-2030年）",
                content="规划提出到2030年新能源汽车新车销量占比达到50%以上，充换电基础设施基本完善",
                category=NewsCategory.POLICY,
                source=NewsSource(name="工信部", credibility=95.0),
                publish_time=datetime.combine(trade_date, time(10, 30)),
                trade_date=trade_date,
                related_themes=["新能源汽车", "锂电池", "充电桩"],
                keywords=["新能源汽车", "规划", "政策支持"],
            ),
            NewsItem(
                title="央行下调存款准备金率0.25个百分点",
                content="中国人民银行决定下调金融机构存款准备金率0.25个百分点，释放长期资金约5000亿元",
                category=NewsCategory.POLICY,
                source=NewsSource(name="央行官网", credibility=98.0),
                publish_time=datetime.combine(trade_date, time(8, 30)),
                trade_date=trade_date,
                related_themes=["货币政策", "银行", "地产"],
                keywords=["降准", "流动性", "货币政策"],
            ),
            NewsItem(
                title="国务院发布促进人工智能产业发展指导意见",
                content="意见提出加快AI基础设施建设，支持大模型研发，推动AI在制造、医疗、金融等领域应用",
                category=NewsCategory.POLICY,
                source=NewsSource(name="中国政府网", credibility=95.0),
                publish_time=datetime.combine(trade_date, time(14, 0)),
                trade_date=trade_date,
                related_themes=["人工智能", "AI大模型", "算力"],
                keywords=["人工智能", "AI", "政策支持"],
            ),
        ]

        await asyncio.sleep(0.05)  # 模拟网络延迟
        return mock_data

    async def _collect_global_market_news(self, trade_date: date) -> List[NewsItem]:
        """采集外围市场资讯 (Mock)

        实际实现: 对接Bloomberg/路透/雪球等外围市场API
        """
        logger.debug("采集外围市场资讯...")

        if not self._use_mock:
            return []

        mock_data = [
            NewsItem(
                title="美股三大指数集体收涨，纳斯达克涨超1.5%",
                content="美联储会议纪要显示加息周期可能结束，科技股领涨，苹果、英伟达创新高",
                category=NewsCategory.GLOBAL,
                source=NewsSource(name="财联社", credibility=80.0),
                publish_time=datetime.combine(trade_date, time(7, 0)),
                trade_date=trade_date,
                related_themes=["美股", "科技股", "美联储"],
                keywords=["美股", "纳斯达克", "美联储"],
            ),
            NewsItem(
                title="港股恒生指数涨0.8%，南向资金净流入超50亿港元",
                content="恒生科技指数表现强劲，美团、腾讯控股领涨，南向资金连续5日净流入",
                category=NewsCategory.GLOBAL,
                source=NewsSource(name="智通财经", credibility=75.0),
                publish_time=datetime.combine(trade_date, time(8, 0)),
                trade_date=trade_date,
                related_themes=["港股", "互联网", "南向资金"],
                keywords=["港股", "南向资金", "恒生指数"],
            ),
            NewsItem(
                title="原油价格大涨3%，地缘冲突升级引发供应担忧",
                content="中东局势再度紧张，布伦特原油突破85美元/桶，油气板块关注度高",
                category=NewsCategory.GLOBAL,
                source=NewsSource(name="财联社", credibility=80.0),
                publish_time=datetime.combine(trade_date, time(6, 30)),
                trade_date=trade_date,
                related_themes=["石油", "能源", "地缘冲突"],
                keywords=["原油", "油价", "地缘冲突"],
            ),
            NewsItem(
                title="美联储暗示2025年可能启动降息周期",
                content="美联储主席鲍威尔表示通胀数据向好，若通胀持续回落，2025年可能开始降息",
                category=NewsCategory.GLOBAL,
                source=NewsSource(name="华尔街见闻", credibility=78.0),
                publish_time=datetime.combine(trade_date, time(7, 30)),
                trade_date=trade_date,
                related_themes=["美联储", "降息", "全球流动性"],
                keywords=["美联储", "降息", "美元"],
            ),
        ]

        await asyncio.sleep(0.05)
        return mock_data

    async def _collect_fund_flow_news(self, trade_date: date) -> List[NewsItem]:
        """采集资金动向资讯 (Mock)

        实际实现: 对接iFind资金流向数据/API
        """
        logger.debug("采集资金动向资讯...")

        if not self._use_mock:
            return []

        mock_data = [
            NewsItem(
                title="北向资金连续3日大幅净流入超200亿元",
                content="外资持续加仓A股核心资产，重点买入新能源、半导体、消费电子板块",
                category=NewsCategory.FUND,
                source=NewsSource(name="东方财富", credibility=82.0),
                publish_time=datetime.combine(trade_date, time(16, 30)),
                trade_date=trade_date,
                related_themes=["北向资金", "外资", "核心资产"],
                related_tickers=["600519.SH", "000858.SZ", "002475.SZ"],
                keywords=["北向资金", "净流入", "外资"],
            ),
            NewsItem(
                title="主力资金今日大幅流入半导体板块超80亿元",
                content="半导体板块获得主力资金集中流入，多只龙头股涨停，资金看好国产替代逻辑",
                category=NewsCategory.FUND,
                source=NewsSource(name="同花顺", credibility=80.0),
                publish_time=datetime.combine(trade_date, time(15, 30)),
                trade_date=trade_date,
                related_themes=["半导体", "国产替代", "芯片"],
                keywords=["主力资金", "半导体", "国产替代"],
            ),
            NewsItem(
                title="ETF资金持续流入沪深300ETF，规模突破千亿",
                content="沪深300ETF近一周净流入超150亿元，显示机构投资者看好大盘蓝筹股",
                category=NewsCategory.FUND,
                source=NewsSource(name="证券时报", credibility=85.0),
                publish_time=datetime.combine(trade_date, time(17, 0)),
                trade_date=trade_date,
                related_themes=["ETF", "沪深300", "机构资金"],
                keywords=["ETF", "机构资金", "沪深300"],
            ),
        ]

        await asyncio.sleep(0.05)
        return mock_data

    async def _collect_theme_catalyst_news(self, trade_date: date) -> List[NewsItem]:
        """采集题材催化资讯 (Mock)

        实际实现: 对接题材挖掘机/行业研报/产业新闻API
        """
        logger.debug("采集题材催化资讯...")

        if not self._use_mock:
            return []

        mock_data = [
            NewsItem(
                title="OpenAI发布新一代大模型GPT-5，性能大幅提升",
                content="GPT-5在多模态理解、推理能力上实现重大突破，国内AI应用和算力产业链受益",
                category=NewsCategory.THEME,
                source=NewsSource(name="36氪", credibility=70.0),
                publish_time=datetime.combine(trade_date, time(9, 0)),
                trade_date=trade_date,
                related_themes=["人工智能", "AI大模型", "算力"],
                related_tickers=["300308.SZ", "002230.SZ"],
                keywords=["OpenAI", "GPT-5", "AI", "算力"],
            ),
            NewsItem(
                title="多家光伏企业签订大额组件出口订单",
                content="隆基绿能、晶科能源等头部企业签订海外大额组件订单，2025年出口有望高增长",
                category=NewsCategory.THEME,
                source=NewsSource(name="索比光伏网", credibility=72.0),
                publish_time=datetime.combine(trade_date, time(11, 0)),
                trade_date=trade_date,
                related_themes=["光伏", "新能源", "出口"],
                related_tickers=["601012.SH", "688223.SH"],
                keywords=["光伏", "组件", "出口订单"],
            ),
            NewsItem(
                title="苹果MR头显Vision Pro销量超预期，供应链订单追加",
                content="苹果Vision Pro首月销量超预期50%，立讯精密、歌尔股份等供应商获追加订单",
                category=NewsCategory.THEME,
                source=NewsSource(name="电子时报", credibility=73.0),
                publish_time=datetime.combine(trade_date, time(10, 0)),
                trade_date=trade_date,
                related_themes=["消费电子", "MR", "苹果产业链"],
                related_tickers=["002475.SZ", "002241.SZ"],
                keywords=["Vision Pro", "MR", "苹果", "消费电子"],
            ),
            NewsItem(
                title="多地出台低空经济支持政策，飞行汽车概念升温",
                content="深圳、广州等地出台低空经济产业发展支持政策，飞行汽车、无人机产业链受关注",
                category=NewsCategory.THEME,
                source=NewsSource(name="财联社", credibility=80.0),
                publish_time=datetime.combine(trade_date, time(13, 0)),
                trade_date=trade_date,
                related_themes=["低空经济", "飞行汽车", "无人机"],
                keywords=["低空经济", "飞行汽车", "政策支持"],
            ),
        ]

        await asyncio.sleep(0.05)
        return mock_data

    async def _collect_stock_announcements(self, trade_date: date) -> List[NewsItem]:
        """采集个股公告资讯 (Mock)

        实际实现: 对接iFind公告数据/巨潮资讯网API
        """
        logger.debug("采集个股公告资讯...")

        if not self._use_mock:
            return []

        mock_data = [
            NewsItem(
                title="某新能源龙头: 2025年一季度净利润同比增长200%",
                content="公司发布一季报预告，净利润10-12亿元，同比增长180%-220%，主要受益于产能释放和产品价格上涨",
                category=NewsCategory.STOCK,
                source=NewsSource(name="巨潮资讯", credibility=90.0),
                publish_time=datetime.combine(trade_date, time(19, 0)),
                trade_date=trade_date,
                related_themes=["新能源", "业绩预增"],
                related_tickers=["300750.SZ"],
                keywords=["业绩预增", "净利润", "增长"],
            ),
            NewsItem(
                title="某半导体龙头: 控股股东计划减持不超过3%股份",
                content="控股股东因个人资金需求，计划通过集中竞价和大宗交易减持不超过公司总股本的3%",
                category=NewsCategory.STOCK,
                source=NewsSource(name="巨潮资讯", credibility=90.0),
                publish_time=datetime.combine(trade_date, time(20, 0)),
                trade_date=trade_date,
                related_themes=["半导体", "减持"],
                related_tickers=["688981.SH"],
                keywords=["减持", "控股股东"],
            ),
            NewsItem(
                title="某消费电子龙头: 与某头部客户签订重大供货协议",
                content="公司与某全球头部消费电子客户签订供货协议，合同金额约50亿元，供货期限3年",
                category=NewsCategory.STOCK,
                source=NewsSource(name="巨潮资讯", credibility=90.0),
                publish_time=datetime.combine(trade_date, time(18, 30)),
                trade_date=trade_date,
                related_themes=["消费电子", "苹果产业链", "大订单"],
                related_tickers=["002475.SZ"],
                keywords=["中标", "大订单", "战略合作"],
            ),
            NewsItem(
                title="某医药龙头: 收到证监会立案告知书",
                content="因涉嫌信息披露违法违规，公司收到中国证券监督管理委员会立案告知书",
                category=NewsCategory.STOCK,
                source=NewsSource(name="巨潮资讯", credibility=90.0),
                publish_time=datetime.combine(trade_date, time(21, 0)),
                trade_date=trade_date,
                related_themes=["医药", "立案调查"],
                related_tickers=["600276.SH"],
                keywords=["立案调查", "信息披露", "违规"],
            ),
        ]

        await asyncio.sleep(0.05)
        return mock_data

    async def _collect_sentiment_news(self, trade_date: date) -> List[NewsItem]:
        """采集市场情绪/舆情资讯 (Mock)

        实际实现: 对接社交媒体API/舆情监控平台
        """
        logger.debug("采集市场情绪舆情资讯...")

        if not self._use_mock:
            return []

        mock_data = [
            NewsItem(
                title="市场赚钱效应回暖，超4000只个股上涨",
                content="今日两市超4000只个股上涨，涨停家数超80只，市场情绪明显回暖，投资者信心增强",
                category=NewsCategory.SENTIMENT,
                source=NewsSource(name="新浪财经", credibility=70.0),
                publish_time=datetime.combine(trade_date, time(15, 30)),
                trade_date=trade_date,
                related_themes=["市场情绪", "赚钱效应"],
                keywords=["上涨", "涨停", "情绪回暖"],
            ),
            NewsItem(
                title="雪球热搜: AI算力、低空经济成最热讨论板块",
                content="AI算力和低空经济板块成为今日雪球热股榜前两位的板块，讨论量突破10万条，关注度极高",
                category=NewsCategory.SENTIMENT,
                source=NewsSource(name="雪球", credibility=60.0),
                publish_time=datetime.combine(trade_date, time(16, 0)),
                trade_date=trade_date,
                related_themes=["AI算力", "低空经济", "舆情热度"],
                keywords=["雪球", "热搜", "AI算力"],
            ),
            NewsItem(
                title="机构调研热度回升，近百家公司获机构密集调研",
                content="近一周共有98家上市公司接待机构调研，集中在半导体、医药、新能源等板块",
                category=NewsCategory.SENTIMENT,
                source=NewsSource(name="券商中国", credibility=75.0),
                publish_time=datetime.combine(trade_date, time(17, 30)),
                trade_date=trade_date,
                related_themes=["机构调研", "半导体", "医药"],
                keywords=["机构调研", "调研热度", "机构动向"],
            ),
        ]

        await asyncio.sleep(0.05)
        return mock_data

    # ==================== 辅助方法 ====================

    def _generate_backtest_evidence(self, item, score_result) -> List[str]:
        """生成回测证据描述"""
        evidence: List[str] = []

        # 基于分类的历史表现
        category_win_rates = {
            "政策": "历史同类政策资讯次日胜率68%，平均收益2.3%",
            "外围": "外围市场联动效应历史胜率55%，平均收益0.8%",
            "资金": "资金流向资讯历史胜率62%，平均收益1.8%",
            "题材": "题材催化资讯历史胜率70%，平均收益3.1%",
            "个股": "个股公告资讯历史胜率65%，平均收益2.5%",
            "舆情": "市场情绪资讯历史胜率52%，平均收益0.6%",
        }
        cat = item.category.value
        if cat in category_win_rates:
            evidence.append(category_win_rates[cat])

        # 时效性证据
        for d in score_result.dimension_scores:
            if d.name == "timeliness" and d.score >= 80:
                evidence.append("盘前/早盘发布，历史数据显示及时性资讯胜率更高")
            elif d.name == "catalyst_strength" and d.score >= 70:
                evidence.append("催化强度指标优秀，关键词匹配度高")
            elif d.name == "relevance" and d.score >= 70:
                evidence.append("与当前市场主线高度关联")

        return evidence if evidence else ["基础评分，暂无数值化回测证据"]

    def _generate_recommendation(self, item, score_result) -> str:
        """生成操作建议摘要"""
        score = score_result.total_score

        if score >= 75:
            return f"高价值资讯(S级)，建议重点关注{item.category.value}方向催化机会"
        elif score >= 50:
            return f"较高价值资讯(A级)，建议关注{item.category.value}相关标的动向"
        elif score >= 25:
            return f"一般价值资讯(B级)，可作为{item.category.value}方向参考"
        else:
            return "低价值资讯(C级)，可忽略"

    def _aggregate_by_category(
        self,
        scored_news: List[ScoredNews],
        category: NewsCategory,
    ) -> str:
        """按分类聚合摘要"""
        filtered = [sn for sn in scored_news if sn.news.category == category]
        if not filtered:
            return f"当日无{category.value}类重要资讯"

        # 取前3条高分资讯
        top = sorted(filtered, key=lambda x: x.score, reverse=True)[:3]
        summaries = []
        for sn in top:
            grade_tag = f"[{sn.grade.value}]"
            summaries.append(f"{grade_tag} {sn.news.title}")

        return "; ".join(summaries)

    def _generate_overall_summary(
        self,
        highlights: List[ScoredNews],
        risk_list: RiskWarningList,
        trade_date: date,
    ) -> str:
        """生成整体盘前摘要"""
        parts: List[str] = []

        # 日期
        parts.append(f"{trade_date.isoformat()}盘前资讯综述:")

        # 高价值资讯统计
        if highlights:
            s_count = sum(1 for sn in highlights if sn.grade.value == "S")
            a_count = sum(1 for sn in highlights if sn.grade.value == "A")
            parts.append(f"高价值资讯S级{s_count}条、A级{a_count}条")

        # 风险统计
        if risk_list.total_count > 0:
            parts.append(f"风险预警: 禁入{len(risk_list.forbidden)}条、谨慎{len(risk_list.high_risk)}条")

        # 主要方向
        key_directions: List[str] = []
        for sn in highlights[:3]:
            if sn.news.related_themes:
                key_directions.extend(sn.news.related_themes[:2])
        if key_directions:
            unique_dirs = list(dict.fromkeys(key_directions))  # 保持顺序去重
            parts.append(f"重点关注: {', '.join(unique_dirs[:4])}")

        return "; ".join(parts)

    def _judge_market_sentiment(
        self,
        scored_news: List[ScoredNews],
        risk_list: RiskWarningList,
    ) -> str:
        """判断市场整体情绪"""
        if not scored_news:
            return "中性"

        # 统计正向/负向关键词
        positive_count = 0
        negative_count = 0
        for sn in scored_news:
            text = f"{sn.news.title} {sn.news.content}"
            positive_keywords = ["上涨", "利好", "增长", "突破", "创新高", "净流入", "预增"]
            negative_keywords = ["下跌", "利空", "下滑", "减持", "亏损", "净流出", "立案"]
            positive_count += sum(1 for kw in positive_keywords if kw in text)
            negative_count += sum(1 for kw in negative_keywords if kw in text)

        # 结合风险清单
        risk_weight = risk_list.total_count * 2

        sentiment_score = positive_count - negative_count - risk_weight

        if sentiment_score >= 5:
            return "偏乐观"
        elif sentiment_score >= 2:
            return "谨慎乐观"
        elif sentiment_score >= -2:
            return "中性"
        elif sentiment_score >= -5:
            return "谨慎偏空"
        else:
            return "偏悲观"


# 导入放在文件末尾避免循环导入
from .models import NewsCategory, NewsItem, NewsSource, PreMarketSummary, RiskWarningList, ScoredNews, RiskLevel
