"""风险预警检测器 — 三级风险预警系统

自动从采集的资讯中识别风险信号，生成三级避雷清单:
- 绝对禁入(FORBIDDEN): 存在重大利空/黑天鹅事件，严禁买入
- 高度谨慎(HIGH): 存在明显利空/不确定性，需高度警惕
- 轻度警示(LOW): 存在潜在风险/瑕疵，需关注

风险检测维度:
- 个股公告风险: 减持、退市、立案、业绩暴雷等
- 政策监管风险: 行业政策收紧、监管处罚等
- 市场情绪风险: 恐慌情绪、系统性风险等
- 资金面风险: 大额解禁、大股东质押等
- 外围环境风险: 地缘政治、全球市场动荡等
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Set, Tuple

from ...core.logger import get_logger

from .models import NewsCategory, NewsItem, RiskLevel, RiskWarning, RiskWarningList

logger = get_logger("swat.m01.risk_detector")


@dataclass
class RiskRule:
    """风险检测规则定义"""
    name: str = ""                   # 规则名称
    level: RiskLevel = RiskLevel.LOW # 风险等级
    keywords: List[str] = field(default_factory=list)  # 触发关键词
    category_scope: List[NewsCategory] = field(default_factory=list)  # 适用资讯分类
    description_template: str = ""   # 风险描述模板
    advice_template: str = ""        # 建议模板


class RiskDetector:
    """风险预警检测器
    
    基于规则引擎 + 关键词匹配，从资讯中自动识别风险信号。
    
    Attributes:
        rules: 风险检测规则列表
        ticker_blacklist: 长期黑名单（可配置）
    """

    # ==================== 预定义风险规则库 ====================

    DEFAULT_RULES: List[RiskRule] = [
        # === 绝对禁入级 (FORBIDDEN) ===
        RiskRule(
            name="退市风险警示",
            level=RiskLevel.FORBIDDEN,
            keywords=["退市", "终止上市", "ST", "*ST", "退市风险警示", "强制退市"],
            category_scope=[NewsCategory.STOCK, NewsCategory.POLICY],
            description_template="个股触发退市风险: {detail}",
            advice_template="绝对禁入，已持仓立即清仓",
        ),
        RiskRule(
            name="立案调查",
            level=RiskLevel.FORBIDDEN,
            keywords=["立案调查", "被调查", "涉嫌违法违规", "监管立案"],
            category_scope=[NewsCategory.STOCK, NewsCategory.POLICY],
            description_template="公司被立案调查: {detail}",
            advice_template="绝对禁入，存在重大不确定性",
        ),
        RiskRule(
            name="业绩暴雷",
            level=RiskLevel.FORBIDDEN,
            keywords=["业绩预亏", "巨亏", "亏损超", "业绩大变脸", "商誉减值", "大幅亏损"],
            category_scope=[NewsCategory.STOCK],
            description_template="业绩大幅亏损: {detail}",
            advice_template="绝对禁入，基本面严重恶化",
        ),
        RiskRule(
            name="债务违约",
            level=RiskLevel.FORBIDDEN,
            keywords=["债务违约", "债券违约", "无法清偿", "破产重整", "债务逾期"],
            category_scope=[NewsCategory.STOCK, NewsCategory.FUND],
            description_template="发生债务违约: {detail}",
            advice_template="绝对禁入，财务风险极高",
        ),
        RiskRule(
            name="实控人风险",
            level=RiskLevel.FORBIDDEN,
            keywords=["实控人被留置", "实控人被采取强制措施", "董事长被留置", "实控人失联"],
            category_scope=[NewsCategory.STOCK, NewsCategory.SENTIMENT],
            description_template="实控人/董事长出现重大风险: {detail}",
            advice_template="绝对禁入，公司治理出现严重问题",
        ),
        RiskRule(
            name="大额减持",
            level=RiskLevel.FORBIDDEN,
            keywords=["清仓式减持", "减持不超总股本6%", "减持不超总股本5%", "控股股东减持"],
            category_scope=[NewsCategory.STOCK],
            description_template="大额减持计划: {detail}",
            advice_template="绝对禁入，筹码供给压力巨大",
        ),
        RiskRule(
            name="黑天鹅事件",
            level=RiskLevel.FORBIDDEN,
            keywords=["黑天鹅", "重大安全事故", "环境污染", "产品召回", "数据泄露", "重大诉讼"],
            category_scope=[NewsCategory.STOCK, NewsCategory.THEME, NewsCategory.SENTIMENT],
            description_template="黑天鹅事件: {detail}",
            advice_template="绝对禁入，事件影响不可预测",
        ),

        # === 高度谨慎级 (HIGH) ===
        RiskRule(
            name="一般减持",
            level=RiskLevel.HIGH,
            keywords=["减持", "减持计划", "拟减持", "减持股份"],
            category_scope=[NewsCategory.STOCK],
            description_template="股东减持计划: {detail}",
            advice_template="高度谨慎，关注减持进展和实际影响",
        ),
        RiskRule(
            name="业绩不及预期",
            level=RiskLevel.HIGH,
            keywords=["不及预期", "业绩下滑", "营收下降", "净利润下降", "毛利率下降"],
            category_scope=[NewsCategory.STOCK],
            description_template="业绩不及预期: {detail}",
            advice_template="高度谨慎，基本面存在压力",
        ),
        RiskRule(
            name="政策利空",
            level=RiskLevel.HIGH,
            keywords=["政策收紧", "监管加强", "限制", "禁止", "叫停", "整顿", "限价"],
            category_scope=[NewsCategory.POLICY],
            description_template="政策面利空: {detail}",
            advice_template="高度谨慎，政策风险可能影响行业估值",
        ),
        RiskRule(
            name="解禁压力",
            level=RiskLevel.HIGH,
            keywords=["限售股解禁", "解禁", "首发原股东限售", "定向增发解禁"],
            category_scope=[NewsCategory.STOCK, NewsCategory.FUND],
            description_template="限售股即将解禁: {detail}",
            advice_template="高度谨慎，解禁可能造成抛压",
        ),
        RiskRule(
            name="质押风险",
            level=RiskLevel.HIGH,
            keywords=["质押比例过高", "触及平仓线", "补充质押", "质押违约"],
            category_scope=[NewsCategory.STOCK],
            description_template="股权质押风险: {detail}",
            advice_template="高度谨慎，质押平仓风险可能导致闪崩",
        ),
        RiskRule(
            name="高管变动",
            level=RiskLevel.HIGH,
            keywords=["总经理辞职", "财务总监辞职", "核心技术人员离职", "董事会集体辞职"],
            category_scope=[NewsCategory.STOCK],
            description_template="核心高管变动: {detail}",
            advice_template="高度谨慎，核心团队稳定性存疑",
        ),
        RiskRule(
            name="行业利空",
            level=RiskLevel.HIGH,
            keywords=["行业景气度下行", "价格战", "产能过剩", "需求萎缩", "原材料大涨"],
            category_scope=[NewsCategory.THEME, NewsCategory.POLICY],
            description_template="行业层面利空: {detail}",
            advice_template="高度谨慎，行业景气度可能持续下行",
        ),

        # === 轻度警示级 (LOW) ===
        RiskRule(
            name="一般性利空",
            level=RiskLevel.LOW,
            keywords=["利空", "风险", "警示", "关注函", "问询函"],
            category_scope=[NewsCategory.STOCK, NewsCategory.POLICY, NewsCategory.THEME],
            description_template="一般性利空/关注事项: {detail}",
            advice_template="轻度警示，关注后续发展",
        ),
        RiskRule(
            name="股权质押",
            level=RiskLevel.LOW,
            keywords=["股权质押", "股东质押"],
            category_scope=[NewsCategory.STOCK],
            description_template="股东进行股权质押: {detail}",
            advice_template="轻度警示，关注质押比例变化",
        ),
        RiskRule(
            name="关联交易",
            level=RiskLevel.LOW,
            keywords=["关联交易", "对外担保", "资金占用"],
            category_scope=[NewsCategory.STOCK],
            description_template="关联交易/担保事项: {detail}",
            advice_template="轻度警示，关注交易公允性和规模",
        ),
        RiskRule(
            name="舆情负面",
            level=RiskLevel.LOW,
            keywords=["投诉", "维权", "举报", "负面报道", "争议"],
            category_scope=[NewsCategory.SENTIMENT],
            description_template="负面舆情: {detail}",
            advice_template="轻度警示，关注舆情发酵程度",
        ),
    ]

    def __init__(self, custom_rules: Optional[List[RiskRule]] = None):
        """初始化风险检测器
        
        Args:
            custom_rules: 自定义风险规则，默认使用内置规则库
        """
        self.rules = custom_rules or self.DEFAULT_RULES

        # 长期黑名单（个股代码）
        self.ticker_blacklist: Set[str] = set()

        logger.info(f"风险检测器初始化完成，规则数: {len(self.rules)}")

    def detect(self, news_items: List[NewsItem], trade_date: Optional[date] = None) -> RiskWarningList:
        """从资讯列表中检测风险信号
        
        Args:
            news_items: 采集的资讯列表
            trade_date: 交易日
            
        Returns:
            RiskWarningList 完整避雷清单
        """
        trade_date = trade_date or date.today()
        result = RiskWarningList(trade_date=trade_date)

        for news in news_items:
            matched_warnings = self._detect_single(news)
            for warning in matched_warnings:
                # 按等级分类
                if warning.level == RiskLevel.FORBIDDEN:
                    result.forbidden.append(warning)
                elif warning.level == RiskLevel.HIGH:
                    result.high_risk.append(warning)
                elif warning.level == RiskLevel.LOW:
                    result.low_risk.append(warning)

        # 生成系统性风险总结
        result.system_risk_summary = self._generate_system_risk_summary(result)

        logger.info(
            "风险检测完成",
            trade_date=trade_date.isoformat(),
            forbidden=len(result.forbidden),
            high_risk=len(result.high_risk),
            low_risk=len(result.low_risk),
        )

        return result

    def detect_from_text(
        self,
        text: str,
        ticker: str = "",
        stock_name: str = "",
        trade_date: Optional[date] = None,
    ) -> List[RiskWarning]:
        """从文本中直接检测风险（用于外部公告/新闻文本）
        
        Args:
            text: 待检测文本
            ticker: 关联股票代码
            stock_name: 股票名称
            trade_date: 交易日
            
        Returns:
            List[RiskWarning] 检测到的风险列表
        """
        trade_date = trade_date or date.today()
        warnings: List[RiskWarning] = []

        for rule in self.rules:
            matched_keywords = [kw for kw in rule.keywords if kw in text]
            if matched_keywords:
                detail = ", ".join(matched_keywords[:3])
                warning = RiskWarning(
                    level=rule.level,
                    ticker=ticker,
                    stock_name=stock_name,
                    reason=rule.description_template.format(detail=detail),
                    trigger_source=f"文本检测: {matched_keywords[0]}",
                    advice=rule.advice_template,
                )
                warnings.append(warning)

        return warnings

    def add_to_blacklist(self, ticker: str, reason: str = "") -> None:
        """添加个股到长期黑名单
        
        Args:
            ticker: 股票代码
            reason: 加入原因
        """
        self.ticker_blacklist.add(ticker)
        logger.info(f"个股加入黑名单: {ticker}, 原因: {reason}")

    def remove_from_blacklist(self, ticker: str) -> None:
        """从黑名单移除个股"""
        self.ticker_blacklist.discard(ticker)

    def is_blacklisted(self, ticker: str) -> bool:
        """检查个股是否在黑名单中"""
        return ticker in self.ticker_blacklist

    # ==================== 内部方法 ====================

    def _detect_single(self, news: NewsItem) -> List[RiskWarning]:
        """对单条资讯进行风险检测"""
        warnings: List[RiskWarning] = []
        text = f"{news.title} {news.content}"

        for rule in self.rules:
            # 检查分类范围匹配
            if rule.category_scope and news.category not in rule.category_scope:
                continue

            # 关键词匹配
            matched_keywords = [kw for kw in rule.keywords if kw in text]
            if matched_keywords:
                detail = ", ".join(matched_keywords[:3])

                # 为每个关联个股生成一条预警
                if news.related_tickers:
                    for ticker in news.related_tickers:
                        warning = RiskWarning(
                            level=rule.level,
                            ticker=ticker,
                            stock_name=news.related_themes[0] if news.related_themes else "",
                            reason=rule.description_template.format(detail=detail),
                            trigger_source=f"资讯[{news.id}]: {news.title[:30]}",
                            advice=rule.advice_template,
                        )
                        warnings.append(warning)
                else:
                    # 无关联个股，作为系统性风险
                    warning = RiskWarning(
                        level=rule.level,
                        ticker="",
                        stock_name="",
                        reason=rule.description_template.format(detail=detail),
                        trigger_source=f"资讯[{news.id}]: {news.title[:30]}",
                        advice=rule.advice_template,
                    )
                    warnings.append(warning)

        return warnings

    def _generate_system_risk_summary(self, risk_list: RiskWarningList) -> str:
        """生成系统性风险总结"""
        parts: List[str] = []

        if risk_list.forbidden:
            forbidden_count = len(set(r.ticker for r in risk_list.forbidden if r.ticker))
            parts.append(f"绝对禁入标的{forbidden_count}只")

        if risk_list.high_risk:
            high_count = len(set(r.ticker for r in risk_list.high_risk if r.ticker))
            parts.append(f"高度谨慎标的{high_count}只")

        if risk_list.low_risk:
            low_count = len(set(r.ticker for r in risk_list.low_risk if r.ticker))
            parts.append(f"轻度警示标的{low_count}只")

        if not parts:
            return "当日无显著风险信号"

        return f"风险扫描结果: {'; '.join(parts)}。建议严格执行仓位管理和止损纪律。"
