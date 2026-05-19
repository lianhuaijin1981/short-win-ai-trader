"""多源资讯采集器 — 实时获取重要资讯来源数据

支持的资讯来源:
1. 巨潮资讯网 (cninfo.com.cn) — 上市公司公告官方来源
2. 上交所官网 (sse.com.cn) — 上海证券交易所公告
3. 深交所官网 (szse.cn) — 深圳证券交易所公告
4. 财联社 (cls.cn) — 实时财经快讯
5. 同花顺 (10jqka.com.cn) — 财经资讯/个股资讯
6. 东方财富 (eastmoney.com) — 财经资讯/资金流向
7. 淘股吧 (taoguba.com.cn) — 短线投资者社区
8. 韭研公社 (jiuyangongshe.com) — 题材挖掘/研报
9. 雪球网 (xueqiu.com) — 投资者社区/热股榜
10. 开盘啦 (kaipanla.com) — 盘前资讯/竞价数据

每个来源都有对应的采集器类，支持:
- 实时快讯采集
- 公告采集
- 题材/热点采集
- 社区舆情采集
"""

import asyncio
import hashlib
import json
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import date, datetime, time as dtime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from ...core.logger import get_logger
from .models import NewsCategory, NewsItem, NewsSource

logger = get_logger("swat.m01.fetcher")


# ==================== 资讯来源定义 ====================

NEWS_SOURCES_CONFIG: Dict[str, Dict[str, Any]] = {
    "巨潮资讯": {
        "name": "巨潮资讯",
        "url": "http://www.cninfo.com.cn",
        "source_type": "官方公告",
        "credibility": 95.0,
        "categories": [NewsCategory.STOCK],
        "api_endpoints": {
            "announcements": "http://www.cninfo.com.cn/new/hisAnnouncement/query",
        },
        "fetch_interval": 300,  # 5分钟
    },
    "上交所": {
        "name": "上海证券交易所",
        "url": "http://www.sse.com.cn",
        "source_type": "官方公告",
        "credibility": 98.0,
        "categories": [NewsCategory.STOCK, NewsCategory.POLICY],
        "api_endpoints": {
            "announcements": "http://www.sse.com.cn/disclosure/listedinfo/announcement/",
        },
        "fetch_interval": 300,
    },
    "深交所": {
        "name": "深圳证券交易所",
        "url": "http://www.szse.cn",
        "source_type": "官方公告",
        "credibility": 98.0,
        "categories": [NewsCategory.STOCK, NewsCategory.POLICY],
        "api_endpoints": {
            "announcements": "http://www.szse.cn/disclosure/notice/general/",
        },
        "fetch_interval": 300,
    },
    "财联社": {
        "name": "财联社",
        "url": "https://www.cls.cn",
        "source_type": "财经媒体",
        "credibility": 85.0,
        "categories": [NewsCategory.POLICY, NewsCategory.THEME, NewsCategory.GLOBAL, NewsCategory.FUND],
        "api_endpoints": {
            "telegraph": "https://www.cls.cn/nodeapi/updateTelegraph",
            "depth": "https://www.cls.cn/nodeapi/updateDepth",
        },
        "fetch_interval": 60,  # 1分钟
    },
    "同花顺": {
        "name": "同花顺",
        "url": "https://www.10jqka.com.cn",
        "source_type": "财经媒体",
        "credibility": 80.0,
        "categories": [NewsCategory.STOCK, NewsCategory.THEME, NewsCategory.FUND],
        "api_endpoints": {
            "news": "https://news.10jqka.com.cn/tapp/news/push/stock",
            "concept": "https://data.10jqka.com.cn/datacentre/conceptboard",
        },
        "fetch_interval": 120,
    },
    "东方财富": {
        "name": "东方财富",
        "url": "https://www.eastmoney.com",
        "source_type": "财经媒体",
        "credibility": 82.0,
        "categories": [NewsCategory.STOCK, NewsCategory.FUND, NewsCategory.THEME],
        "api_endpoints": {
            "news": "https://np-listapi.eastmoney.com/comm/web/getNewsByTag",
            "fund_flow": "https://push2.eastmoney.com/api/qt/clist/get",
        },
        "fetch_interval": 120,
    },
    "淘股吧": {
        "name": "淘股吧",
        "url": "https://www.taoguba.com.cn",
        "source_type": "投资社区",
        "credibility": 60.0,
        "categories": [NewsCategory.SENTIMENT, NewsCategory.THEME],
        "api_endpoints": {
            "hot_topics": "https://www.taoguba.com.cn/api/hotTopic",
            "hot_stocks": "https://www.taoguba.com.cn/api/hotStock",
        },
        "fetch_interval": 300,
    },
    "韭研公社": {
        "name": "韭研公社",
        "url": "https://www.jiuyangongshe.com",
        "source_type": "研究社区",
        "credibility": 65.0,
        "categories": [NewsCategory.THEME, NewsCategory.STOCK],
        "api_endpoints": {
            "research": "https://www.jiuyangongshe.com/api/research",
            "theme": "https://www.jiuyangongshe.com/api/theme",
        },
        "fetch_interval": 300,
    },
    "雪球": {
        "name": "雪球",
        "url": "https://xueqiu.com",
        "source_type": "投资社区",
        "credibility": 62.0,
        "categories": [NewsCategory.SENTIMENT, NewsCategory.THEME],
        "api_endpoints": {
            "hot_stocks": "https://stock.xueqiu.com/hq/stock/realtime.json",
            "timeline": "https://xueqiu.com/statuses/hot/listV2.json",
        },
        "fetch_interval": 180,
    },
    "开盘啦": {
        "name": "开盘啦",
        "url": "https://www.kaipanla.com",
        "source_type": "盘前数据",
        "credibility": 70.0,
        "categories": [NewsCategory.SENTIMENT, NewsCategory.FUND],
        "api_endpoints": {
            "pre_market": "https://www.kaipanla.com/api/premarket",
            "auction": "https://www.kaipanla.com/api/auction",
        },
        "fetch_interval": 60,
    },
}


# ==================== 基础采集器 ====================

class BaseSourceFetcher(ABC):
    """资讯来源采集器基类"""
    
    def __init__(self, source_config: Dict[str, Any], use_mock: bool = True):
        """初始化采集器
        
        Args:
            source_config: 来源配置
            use_mock: 是否使用模拟数据
        """
        self.config = source_config
        self.source_name = source_config["name"]
        self.use_mock = use_mock
        self._last_fetch_time: Optional[datetime] = None
        self._cache: Dict[str, NewsItem] = {}
    
    @abstractmethod
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集资讯
        
        Args:
            trade_date: 交易日
            
        Returns:
            List[NewsItem] 资讯列表
        """
        pass
    
    def _create_news_item(
        self,
        title: str,
        content: str,
        category: NewsCategory,
        publish_time: Optional[datetime] = None,
        trade_date: Optional[date] = None,
        related_tickers: Optional[List[str]] = None,
        related_themes: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        url: str = "",
    ) -> NewsItem:
        """创建资讯条目"""
        source = NewsSource(
            name=self.source_name,
            url=self.config["url"],
            source_type=self.config["source_type"],
            credibility=self.config["credibility"],
        )
        
        return NewsItem(
            title=title,
            content=content,
            category=category,
            source=source,
            publish_time=publish_time or datetime.now(),
            trade_date=trade_date or date.today(),
            related_tickers=related_tickers or [],
            related_themes=related_themes or [],
            keywords=keywords or [],
            raw_metadata={"source_url": url},
        )
    
    def _should_fetch(self) -> bool:
        """检查是否需要重新采集"""
        if self.use_mock:
            return True
        
        if not self._last_fetch_time:
            return True
        
        interval = self.config.get("fetch_interval", 300)
        return (datetime.now() - self._last_fetch_time).total_seconds() >= interval
    
    async def _http_get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """发送HTTP GET请求
        
        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            
        Returns:
            响应JSON或None
        """
        if self.use_mock:
            return None
        
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        if headers:
            default_headers.update(headers)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=default_headers, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.warning(f"HTTP请求失败: {url}, status={resp.status}")
                        return None
        except Exception as e:
            logger.error(f"HTTP请求异常: {url}, error={e}")
            return None


# ==================== 各来源采集器实现 ====================

class CninfoFetcher(BaseSourceFetcher):
    """巨潮资讯采集器 — 上市公司公告"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["巨潮资讯"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集巨潮资讯公告"""
        trade_date = trade_date or date.today()
        
        if not self._should_fetch():
            return list(self._cache.values())
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        # 真实采集
        items = await self._fetch_real(trade_date)
        self._last_fetch_time = datetime.now()
        return items
    
    async def _fetch_real(self, trade_date: date) -> List[NewsItem]:
        """真实采集巨潮公告"""
        items: List[NewsItem] = []
        
        try:
            # 巨潮公告查询API
            url = self.config["api_endpoints"]["announcements"]
            params = {
                "pageNum": 1,
                "pageSize": 30,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": f"{trade_date.isoformat()}~{trade_date.isoformat()}",
            }
            
            data = await self._http_get(url, params)
            if data and data.get("announcements"):
                for ann in data["announcements"][:20]:
                    title = ann.get("announcementTitle", "")
                    sec_code = ann.get("secCode", "")
                    sec_name = ann.get("secName", "")
                    
                    # 判断公告类型
                    category, keywords = self._classify_announcement(title)
                    
                    item = self._create_news_item(
                        title=f"{sec_name}: {title}",
                        content=ann.get("adjunctUrl", ""),
                        category=category,
                        publish_time=datetime.fromtimestamp(ann.get("announcementTime", 0) / 1000),
                        trade_date=trade_date,
                        related_tickers=[f"{sec_code}.SZ" if sec_code.startswith("0") or sec_code.startswith("3") else f"{sec_code}.SH"] if sec_code else [],
                        related_themes=keywords,
                        keywords=keywords,
                    )
                    items.append(item)
        except Exception as e:
            logger.error(f"巨潮资讯采集失败: {e}")
        
        return items
    
    def _classify_announcement(self, title: str) -> Tuple[NewsCategory, List[str]]:
        """分类公告类型"""
        title_lower = title.lower()
        
        if any(kw in title_lower for kw in ["业绩", "利润", "营收", "预增", "预亏", "年报", "季报"]):
            return NewsCategory.STOCK, ["业绩公告"]
        elif any(kw in title_lower for kw in ["减持", "增持", "回购"]):
            return NewsCategory.STOCK, ["增减持"]
        elif any(kw in title_lower for kw in ["重组", "并购", "资产"]):
            return NewsCategory.STOCK, ["资产重组"]
        elif any(kw in title_lower for kw in ["中标", "合同", "协议"]):
            return NewsCategory.STOCK, ["重大合同"]
        elif any(kw in title_lower for kw in ["立案", "处罚", "监管"]):
            return NewsCategory.STOCK, ["监管处罚"]
        else:
            return NewsCategory.STOCK, ["公司公告"]
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟巨潮公告数据"""
        mock_announcements = [
            {
                "title": "宁德时代: 2025年一季度净利润同比增长180%",
                "content": "公司发布2025年一季度业绩预告，预计净利润100-110亿元，同比增长175%-200%",
                "category": NewsCategory.STOCK,
                "tickers": ["300750.SZ"],
                "themes": ["新能源", "业绩预增"],
                "keywords": ["业绩预增", "净利润", "宁德时代"],
            },
            {
                "title": "中际旭创: 签订重大供货合同",
                "content": "公司与海外客户签订光模块供货合同，合同金额约30亿元",
                "category": NewsCategory.STOCK,
                "tickers": ["300308.SZ"],
                "themes": ["光模块", "AI算力"],
                "keywords": ["重大合同", "光模块"],
            },
            {
                "title": "某半导体公司: 控股股东拟减持不超过3%",
                "content": "控股股东因个人资金需求，计划减持不超过公司总股本的3%",
                "category": NewsCategory.STOCK,
                "tickers": ["688981.SH"],
                "themes": ["半导体", "减持"],
                "keywords": ["减持", "控股股东"],
            },
            {
                "title": "某医药公司: 收到证监会立案告知书",
                "content": "因涉嫌信息披露违法违规，收到证监会立案告知书",
                "category": NewsCategory.STOCK,
                "tickers": ["600276.SH"],
                "themes": ["医药", "立案调查"],
                "keywords": ["立案调查", "信息披露"],
            },
        ]
        
        items = []
        for ann in mock_announcements:
            item = self._create_news_item(
                title=ann["title"],
                content=ann["content"],
                category=ann["category"],
                trade_date=trade_date,
                related_tickers=ann["tickers"],
                related_themes=ann["themes"],
                keywords=ann["keywords"],
            )
            items.append(item)
        
        return items


class CLSFetcher(BaseSourceFetcher):
    """财联社采集器 — 实时财经快讯"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["财联社"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集财联社快讯"""
        trade_date = trade_date or date.today()
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        items = await self._fetch_real(trade_date)
        self._last_fetch_time = datetime.now()
        return items
    
    async def _fetch_real(self, trade_date: date) -> List[NewsItem]:
        """真实采集财联社快讯"""
        items: List[NewsItem] = []
        
        try:
            url = self.config["api_endpoints"]["telegraph"]
            params = {"app=CailianpressWeb": "", "os=web": "", "sv=8.4.6": ""}
            
            data = await self._http_get(url, params)
            if data and data.get("data"):
                for tele in data["data"]["roll_data"][:30]:
                    title = tele.get("title", "")
                    content = tele.get("content", "")
                    ctime = tele.get("ctime", 0)
                    
                    # 分类
                    category = self._classify_telegraph(title + content)
                    
                    item = self._create_news_item(
                        title=title or content[:50],
                        content=content,
                        category=category,
                        publish_time=datetime.fromtimestamp(ctime) if ctime else datetime.now(),
                        trade_date=trade_date,
                        keywords=self._extract_keywords(title + content),
                    )
                    items.append(item)
        except Exception as e:
            logger.error(f"财联社采集失败: {e}")
        
        return items
    
    def _classify_telegraph(self, text: str) -> NewsCategory:
        """分类快讯"""
        if any(kw in text for kw in ["央行", "证监会", "国务院", "政策", "监管"]):
            return NewsCategory.POLICY
        elif any(kw in text for kw in ["美股", "港股", "外围", "美联储", "汇率"]):
            return NewsCategory.GLOBAL
        elif any(kw in text for kw in ["北向", "主力", "资金", "流入", "流出"]):
            return NewsCategory.FUND
        elif any(kw in text for kw in ["板块", "题材", "概念", "涨停"]):
            return NewsCategory.THEME
        else:
            return NewsCategory.SENTIMENT
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        patterns = [
            r"([A-Z]{2,}\d{6})",  # 股票代码
            r"([\u4e00-\u9fa5]{2,8}板块)",  # 板块名
            r"([\u4e00-\u9fa5]{2,6}涨停)",  # 涨停
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches[:3])
        return keywords[:5]
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟财联社快讯"""
        mock_telegraphs = [
            {
                "title": "【盘中突发】国务院发布促进人工智能产业发展指导意见",
                "content": "意见提出加快AI基础设施建设，支持大模型研发应用，推动AI与实体经济深度融合",
                "category": NewsCategory.POLICY,
                "themes": ["人工智能", "AI大模型", "政策支持"],
                "keywords": ["人工智能", "国务院", "政策支持"],
            },
            {
                "title": "北向资金午后加速流入，全天净流入超120亿元",
                "content": "北向资金午后加速流入A股，重点加仓新能源、半导体板块",
                "category": NewsCategory.FUND,
                "themes": ["北向资金", "外资"],
                "keywords": ["北向资金", "净流入"],
            },
            {
                "title": "半导体板块午后拉升，多股涨停",
                "content": "半导体板块午后集体拉升，中芯国际涨超8%，多只个股涨停",
                "category": NewsCategory.THEME,
                "themes": ["半导体", "国产替代"],
                "keywords": ["半导体", "涨停"],
            },
            {
                "title": "美股期货全线上涨，纳指期货涨超1%",
                "content": "美联储会议纪要偏鸽，美股期货全线上涨，科技股领涨",
                "category": NewsCategory.GLOBAL,
                "themes": ["美股", "美联储"],
                "keywords": ["美股", "期货", "上涨"],
            },
        ]
        
        items = []
        for tele in mock_telegraphs:
            item = self._create_news_item(
                title=tele["title"],
                content=tele["content"],
                category=tele["category"],
                trade_date=trade_date,
                related_themes=tele["themes"],
                keywords=tele["keywords"],
            )
            items.append(item)
        
        return items


class EastmoneyFetcher(BaseSourceFetcher):
    """东方财富采集器 — 财经资讯/资金流向"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["东方财富"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集东方财富资讯"""
        trade_date = trade_date or date.today()
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        items = await self._fetch_real(trade_date)
        self._last_fetch_time = datetime.now()
        return items
    
    async def _fetch_real(self, trade_date: date) -> List[NewsItem]:
        """真实采集东方财富资讯"""
        items: List[NewsItem] = []
        
        try:
            # 资金流向数据
            url = self.config["api_endpoints"]["fund_flow"]
            params = {
                "pn": "1",
                "pz": "20",
                "po": "1",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "fid": "f62",
                "fs": "m:90 t:2",
            }
            
            data = await self._http_get(url, params)
            if data and data.get("data") and data["data"].get("diff"):
                for stock in data["data"]["diff"][:10]:
                    name = stock.get("f14", "")
                    code = stock.get("f12", "")
                    main_net = stock.get("f62", 0)
                    
                    if abs(main_net) > 1e8:  # 主力净流入/流出超1亿
                        direction = "流入" if main_net > 0 else "流出"
                        item = self._create_news_item(
                            title=f"{name}: 主力资金{direction}{abs(main_net)/1e8:.1f}亿元",
                            content=f"主力资金{direction}{abs(main_net)/1e8:.1f}亿元",
                            category=NewsCategory.FUND,
                            trade_date=trade_date,
                            related_tickers=[f"{code}.SH" if code.startswith("6") else f"{code}.SZ"],
                            keywords=["主力资金", direction],
                        )
                        items.append(item)
        except Exception as e:
            logger.error(f"东方财富采集失败: {e}")
        
        return items
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟东方财富数据"""
        return [
            self._create_news_item(
                title="主力资金今日大幅流入半导体板块超80亿元",
                content="半导体板块获得主力资金集中流入，多只龙头股涨停",
                category=NewsCategory.FUND,
                trade_date=trade_date,
                related_themes=["半导体", "国产替代"],
                keywords=["主力资金", "半导体"],
            ),
            self._create_news_item(
                title="ETF资金持续流入沪深300ETF，规模突破千亿",
                content="沪深300ETF近一周净流入超150亿元",
                category=NewsCategory.FUND,
                trade_date=trade_date,
                related_themes=["ETF", "沪深300"],
                keywords=["ETF", "机构资金"],
            ),
        ]


class XueqiuFetcher(BaseSourceFetcher):
    """雪球采集器 — 投资者社区/热股榜"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["雪球"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集雪球热股/热议"""
        trade_date = trade_date or date.today()
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        items = await self._fetch_real(trade_date)
        self._last_fetch_time = datetime.now()
        return items
    
    async def _fetch_real(self, trade_date: date) -> List[NewsItem]:
        """真实采集雪球数据"""
        items: List[NewsItem] = []
        
        try:
            # 雪球热股榜
            url = "https://stock.xueqiu.com/hq/stock/realtime.json"
            params = {"type": "10", "size": "20"}
            
            headers = {
                "Cookie": "xq_a_token=test",  # 需要实际cookie
                "User-Agent": "Mozilla/5.0",
            }
            
            data = await self._http_get(url, params, headers)
            if data and data.get("data"):
                for stock in data["data"][:10]:
                    name = stock.get("name", "")
                    code = stock.get("symbol", "")
                    
                    item = self._create_news_item(
                        title=f"雪球热股: {name}",
                        content=f"{name}({code})登上雪球热股榜",
                        category=NewsCategory.SENTIMENT,
                        trade_date=trade_date,
                        related_tickers=[code],
                        keywords=["雪球热股", name],
                    )
                    items.append(item)
        except Exception as e:
            logger.error(f"雪球采集失败: {e}")
        
        return items
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟雪球数据"""
        return [
            self._create_news_item(
                title="雪球热搜: AI算力、低空经济成最热讨论板块",
                content="AI算力和低空经济板块成为今日雪球热股榜前两位",
                category=NewsCategory.SENTIMENT,
                trade_date=trade_date,
                related_themes=["AI算力", "低空经济"],
                keywords=["雪球", "热搜"],
            ),
            self._create_news_item(
                title="雪球热股: 宁德时代讨论量突破5万条",
                content="宁德时代业绩预增引发热议，讨论量突破5万条",
                category=NewsCategory.SENTIMENT,
                trade_date=trade_date,
                related_tickers=["300750.SZ"],
                related_themes=["新能源", "业绩预增"],
                keywords=["雪球热股", "宁德时代"],
            ),
        ]


class TaogubaFetcher(BaseSourceFetcher):
    """淘股吧采集器 — 短线投资者社区"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["淘股吧"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集淘股吧热门话题"""
        trade_date = trade_date or date.today()
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        return []
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟淘股吧数据"""
        return [
            self._create_news_item(
                title="淘股吧热议: 半导体国产替代逻辑持续发酵",
                content="淘股吧多位大V看好半导体国产替代逻辑，认为板块仍有空间",
                category=NewsCategory.SENTIMENT,
                trade_date=trade_date,
                related_themes=["半导体", "国产替代"],
                keywords=["淘股吧", "半导体"],
            ),
        ]


class KaiPanLaFetcher(BaseSourceFetcher):
    """开盘啦采集器 — 盘前资讯/竞价数据"""
    
    def __init__(self, use_mock: bool = True):
        super().__init__(NEWS_SOURCES_CONFIG["开盘啦"], use_mock)
    
    async def fetch(self, trade_date: Optional[date] = None) -> List[NewsItem]:
        """采集开盘啦盘前数据"""
        trade_date = trade_date or date.today()
        
        if self.use_mock:
            return self._fetch_mock(trade_date)
        
        return []
    
    def _fetch_mock(self, trade_date: date) -> List[NewsItem]:
        """模拟开盘啦数据"""
        return [
            self._create_news_item(
                title="盘前竞价: 半导体板块多股高开超5%",
                content="集合竞价阶段，半导体板块多只个股高开超5%，资金抢筹明显",
                category=NewsCategory.SENTIMENT,
                trade_date=trade_date,
                related_themes=["半导体", "竞价"],
                keywords=["竞价", "高开"],
            ),
        ]


# ==================== 多源采集管理器 ====================

class MultiSourceFetcher:
    """多源资讯采集管理器
    
    管理所有资讯来源的采集器，支持并行采集和结果聚合。
    """
    
    def __init__(self, use_mock: bool = True):
        """初始化多源采集管理器
        
        Args:
            use_mock: 是否使用模拟数据
        """
        self.use_mock = use_mock
        self.fetchers: Dict[str, BaseSourceFetcher] = {}
        
        # 初始化所有采集器
        self._init_fetchers()
        
        logger.info(f"多源采集管理器初始化完成，来源数: {len(self.fetchers)}")
    
    def _init_fetchers(self) -> None:
        """初始化所有采集器"""
        self.fetchers = {
            "巨潮资讯": CninfoFetcher(self.use_mock),
            "财联社": CLSFetcher(self.use_mock),
            "东方财富": EastmoneyFetcher(self.use_mock),
            "雪球": XueqiuFetcher(self.use_mock),
            "淘股吧": TaogubaFetcher(self.use_mock),
            "开盘啦": KaiPanLaFetcher(self.use_mock),
        }
    
    async def fetch_all(
        self,
        trade_date: Optional[date] = None,
        sources: Optional[List[str]] = None,
    ) -> List[NewsItem]:
        """并行采集所有来源的资讯
        
        Args:
            trade_date: 交易日
            sources: 指定采集的来源列表（默认全部）
            
        Returns:
            List[NewsItem] 所有资讯列表
        """
        trade_date = trade_date or date.today()
        
        # 确定要采集的来源
        target_sources = sources or list(self.fetchers.keys())
        
        logger.info(f"开始多源资讯采集: {target_sources}")
        
        # 并行采集
        tasks = []
        for source_name in target_sources:
            fetcher = self.fetchers.get(source_name)
            if fetcher:
                tasks.append(self._safe_fetch(fetcher, trade_date, source_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 聚合结果
        all_items: List[NewsItem] = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
        
        # 去重
        all_items = self._deduplicate(all_items)
        
        logger.info(f"多源采集完成: 共{len(all_items)}条资讯")
        return all_items
    
    async def _safe_fetch(
        self,
        fetcher: BaseSourceFetcher,
        trade_date: date,
        source_name: str,
    ) -> List[NewsItem]:
        """安全采集（捕获异常）"""
        try:
            items = await fetcher.fetch(trade_date)
            logger.info(f"{source_name}采集完成: {len(items)}条")
            return items
        except Exception as e:
            logger.error(f"{source_name}采集失败: {e}")
            return []
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """去重资讯"""
        seen = set()
        unique_items = []
        
        for item in items:
            # 基于标题相似度去重
            title_hash = hashlib.md5(item.title[:30].encode()).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique_items.append(item)
        
        return unique_items
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有来源的状态"""
        status = {}
        for name, fetcher in self.fetchers.items():
            status[name] = {
                "enabled": True,
                "use_mock": fetcher.use_mock,
                "last_fetch": fetcher._last_fetch_time.isoformat() if fetcher._last_fetch_time else None,
                "credibility": fetcher.config["credibility"],
                "categories": [c.value for c in fetcher.config["categories"]],
            }
        return status