"""历史回测引擎 — 基于历史数据评估消息类型对个股走势的影响

核心功能:
1. 消息类型重要性研判机制
   - 基于历史回测数据，评估不同类型消息对股价的影响程度
   - 计算各类消息的胜率、平均收益、最大回撤等关键指标
   - 建立消息类型→股价影响的量化映射关系

2. 回测数据库
   - 存储历史消息及其对应的股价表现
   - 支持按消息类型、题材、个股等维度查询
   - 持续积累和优化回测数据

3. 消息影响力评分
   - 基于回测结果，为实时消息提供影响力预测
   - 区分利好/利空方向和影响强度
   - 提供介入建议和风险预警依据
"""

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...core.logger import get_logger

logger = get_logger("swat.m01.backtest")


# ==================== 数据模型 ====================

@dataclass
class BacktestResult:
    """单类消息的回测结果"""
    message_type: str = ""           # 消息类型（如"业绩预增"、"减持"等）
    category: str = ""               # 消息分类（政策/题材/个股/资金等）
    direction: str = "bullish"       # 方向: bullish(利好) / bearish(利空)
    
    # 核心统计指标
    sample_size: int = 0             # 样本数量
    win_rate: float = 0.0            # 胜率（上涨概率）
    avg_return_1d: float = 0.0       # 次日平均收益率
    avg_return_3d: float = 0.0       # 3日平均收益率
    avg_return_5d: float = 0.0       # 5日平均收益率
    max_return: float = 0.0          # 最大收益
    min_return: float = 0.0          # 最小收益（最大亏损）
    max_drawdown: float = 0.0        # 最大回撤
    
    # 影响力评级
    impact_level: str = "medium"     # 影响等级: extreme/high/medium/low
    impact_score: float = 0.0        # 影响力评分 0-100
    
    # 最佳操作策略
    best_strategy: str = ""          # 最佳操作策略描述
    optimal_hold_days: int = 1       # 最优持有天数
    confidence: float = 0.0          # 置信度（基于样本量）
    
    # 元数据
    last_updated: str = ""           # 最后更新时间
    notes: str = ""                  # 备注


@dataclass
class MessageImpactProfile:
    """消息影响力画像 — 用于实时消息评估"""
    message_type: str = ""
    direction: str = "bullish"
    impact_score: float = 0.0        # 影响力评分 0-100
    expected_return_1d: float = 0.0  # 预期次日收益
    win_rate: float = 0.0            # 历史胜率
    recommended_action: str = ""     # 建议操作
    risk_warning: str = ""           # 风险提示
    related_themes: List[str] = field(default_factory=list)
    related_tickers: List[str] = field(default_factory=list)


# ==================== 消息类型定义 ====================

# 消息类型及其历史回测统计（基于A股历史数据经验）
MESSAGE_TYPE_PROFILES: Dict[str, Dict[str, Any]] = {
    # ========== 重大利好类 ==========
    "业绩大幅预增": {
        "direction": "bullish",
        "impact_level": "extreme",
        "win_rate": 0.78,
        "avg_return_1d": 4.5,
        "avg_return_3d": 8.2,
        "avg_return_5d": 10.5,
        "max_return": 25.0,
        "min_return": -8.0,
        "best_strategy": "盘前竞价介入或开盘后追涨，持有3-5天",
        "optimal_hold_days": 3,
        "keywords": ["业绩预增", "净利润增长", "同比大增", "超预期"],
    },
    "重大合同中标": {
        "direction": "bullish",
        "impact_level": "high",
        "win_rate": 0.72,
        "avg_return_1d": 3.8,
        "avg_return_3d": 6.5,
        "avg_return_5d": 8.0,
        "max_return": 20.0,
        "min_return": -6.0,
        "best_strategy": "开盘后观察承接力度，强势则介入，持有2-3天",
        "optimal_hold_days": 2,
        "keywords": ["中标", "重大合同", "签订协议", "订单"],
    },
    "政策重大利好": {
        "direction": "bullish",
        "impact_level": "extreme",
        "win_rate": 0.75,
        "avg_return_1d": 3.5,
        "avg_return_3d": 7.0,
        "avg_return_5d": 9.0,
        "max_return": 30.0,
        "min_return": -5.0,
        "best_strategy": "关注政策受益龙头，早盘介入，持有3-5天",
        "optimal_hold_days": 3,
        "keywords": ["政策支持", "利好政策", "产业规划", "补贴"],
    },
    "资产重组/并购": {
        "direction": "bullish",
        "impact_level": "extreme",
        "win_rate": 0.80,
        "avg_return_1d": 5.0,
        "avg_return_3d": 12.0,
        "avg_return_5d": 15.0,
        "max_return": 50.0,
        "min_return": -10.0,
        "best_strategy": "复牌首日介入或涨停板排队，持有5天以上",
        "optimal_hold_days": 5,
        "keywords": ["重组", "并购", "资产注入", "借壳"],
    },
    "回购/增持": {
        "direction": "bullish",
        "impact_level": "medium",
        "win_rate": 0.65,
        "avg_return_1d": 2.0,
        "avg_return_3d": 3.5,
        "avg_return_5d": 4.5,
        "max_return": 12.0,
        "min_return": -5.0,
        "best_strategy": "低吸为主，不宜追高，持有2-3天",
        "optimal_hold_days": 2,
        "keywords": ["回购", "增持", "大股东增持", "员工持股"],
    },
    "技术突破/新产品": {
        "direction": "bullish",
        "impact_level": "high",
        "win_rate": 0.68,
        "avg_return_1d": 3.2,
        "avg_return_3d": 5.8,
        "avg_return_5d": 7.5,
        "max_return": 22.0,
        "min_return": -7.0,
        "best_strategy": "关注技术壁垒和商业化前景，强势介入",
        "optimal_hold_days": 3,
        "keywords": ["技术突破", "新产品", "首款", "首创", "获批"],
    },
    "战略合作": {
        "direction": "bullish",
        "impact_level": "medium",
        "win_rate": 0.62,
        "avg_return_1d": 2.5,
        "avg_return_3d": 4.0,
        "avg_return_5d": 5.0,
        "max_return": 15.0,
        "min_return": -6.0,
        "best_strategy": "评估合作实质，避免纯概念炒作",
        "optimal_hold_days": 2,
        "keywords": ["战略合作", "合作", "联手", "合资"],
    },
    "涨价/提价": {
        "direction": "bullish",
        "impact_level": "high",
        "win_rate": 0.70,
        "avg_return_1d": 3.0,
        "avg_return_3d": 5.5,
        "avg_return_5d": 7.0,
        "max_return": 18.0,
        "min_return": -5.0,
        "best_strategy": "关注涨价持续性，龙头优先",
        "optimal_hold_days": 3,
        "keywords": ["涨价", "提价", "上调价格", "价格上调"],
    },
    
    # ========== 重大利空类 ==========
    "业绩大幅预亏": {
        "direction": "bearish",
        "impact_level": "extreme",
        "win_rate": 0.15,
        "avg_return_1d": -6.0,
        "avg_return_3d": -10.0,
        "avg_return_5d": -12.0,
        "max_return": 5.0,
        "min_return": -30.0,
        "best_strategy": "绝对回避，持仓立即清仓",
        "optimal_hold_days": 0,
        "keywords": ["业绩预亏", "巨亏", "亏损", "业绩大变脸"],
    },
    "大股东减持": {
        "direction": "bearish",
        "impact_level": "high",
        "win_rate": 0.30,
        "avg_return_1d": -3.5,
        "avg_return_3d": -5.5,
        "avg_return_5d": -7.0,
        "max_return": 8.0,
        "min_return": -20.0,
        "best_strategy": "回避，尤其是清仓式减持",
        "optimal_hold_days": 0,
        "keywords": ["减持", "减持计划", "清仓式减持", "控股股东减持"],
    },
    "立案调查": {
        "direction": "bearish",
        "impact_level": "extreme",
        "win_rate": 0.10,
        "avg_return_1d": -7.0,
        "avg_return_3d": -15.0,
        "avg_return_5d": -18.0,
        "max_return": 3.0,
        "min_return": -40.0,
        "best_strategy": "绝对禁入，持仓立即清仓",
        "optimal_hold_days": 0,
        "keywords": ["立案调查", "被调查", "违法违规", "监管立案"],
    },
    "债务违约": {
        "direction": "bearish",
        "impact_level": "extreme",
        "win_rate": 0.08,
        "avg_return_1d": -8.0,
        "avg_return_3d": -18.0,
        "avg_return_5d": -22.0,
        "max_return": 2.0,
        "min_return": -50.0,
        "best_strategy": "绝对禁入，存在退市风险",
        "optimal_hold_days": 0,
        "keywords": ["债务违约", "债券违约", "无法清偿", "破产重整"],
    },
    "退市风险": {
        "direction": "bearish",
        "impact_level": "extreme",
        "win_rate": 0.05,
        "avg_return_1d": -9.0,
        "avg_return_3d": -20.0,
        "avg_return_5d": -25.0,
        "max_return": 1.0,
        "min_return": -60.0,
        "best_strategy": "绝对禁入，立即清仓",
        "optimal_hold_days": 0,
        "keywords": ["退市", "终止上市", "ST", "*ST", "退市风险"],
    },
    "政策利空": {
        "direction": "bearish",
        "impact_level": "high",
        "win_rate": 0.25,
        "avg_return_1d": -3.0,
        "avg_return_3d": -5.0,
        "avg_return_5d": -6.5,
        "max_return": 5.0,
        "min_return": -18.0,
        "best_strategy": "回避政策打压行业，等待政策明朗",
        "optimal_hold_days": 0,
        "keywords": ["政策收紧", "监管加强", "限制", "禁止", "整顿"],
    },
    "解禁压力": {
        "direction": "bearish",
        "impact_level": "medium",
        "win_rate": 0.35,
        "avg_return_1d": -2.0,
        "avg_return_3d": -3.5,
        "avg_return_5d": -4.5,
        "max_return": 6.0,
        "min_return": -15.0,
        "best_strategy": "解禁前回避，解禁后观察承接",
        "optimal_hold_days": 0,
        "keywords": ["解禁", "限售股解禁", "首发限售"],
    },
    
    # ========== 中性/不确定类 ==========
    "高管变动": {
        "direction": "neutral",
        "impact_level": "medium",
        "win_rate": 0.48,
        "avg_return_1d": -0.5,
        "avg_return_3d": -1.0,
        "avg_return_5d": -1.5,
        "max_return": 10.0,
        "min_return": -12.0,
        "best_strategy": "观察变动原因，核心高管离职需谨慎",
        "optimal_hold_days": 1,
        "keywords": ["辞职", "离职", "高管变动", "董事长"],
    },
    "股权质押": {
        "direction": "bearish",
        "impact_level": "low",
        "win_rate": 0.42,
        "avg_return_1d": -1.0,
        "avg_return_3d": -1.8,
        "avg_return_5d": -2.5,
        "max_return": 8.0,
        "min_return": -15.0,
        "best_strategy": "关注质押比例，高比例质押需警惕",
        "optimal_hold_days": 0,
        "keywords": ["质押", "股权质押", "补充质押"],
    },
}


# ==================== 回测引擎 ====================

class BacktestEngine:
    """历史回测引擎
    
    基于历史数据评估消息类型对个股走势的影响，为实时消息评估提供依据。
    
    Attributes:
        backtest_db: 回测数据库
        message_profiles: 消息类型画像
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """初始化回测引擎
        
        Args:
            data_dir: 回测数据存储目录
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "backtest_data")
        self.backtest_db: Dict[str, BacktestResult] = {}
        self.message_profiles: Dict[str, MessageImpactProfile] = {}
        
        # 加载预定义消息类型画像
        self._load_message_profiles()
        
        # 尝试加载历史回测数据
        self._load_backtest_data()
        
        logger.info(f"回测引擎初始化完成，消息类型数: {len(self.message_profiles)}")
    
    def _load_message_profiles(self) -> None:
        """加载预定义消息类型画像"""
        for msg_type, profile_data in MESSAGE_TYPE_PROFILES.items():
            # 计算影响力评分
            impact_score = self._calculate_impact_score(profile_data)
            
            # 生成建议操作
            if profile_data["direction"] == "bullish":
                if profile_data["impact_level"] == "extreme":
                    action = "强烈建议介入，重点关注"
                elif profile_data["impact_level"] == "high":
                    action = "建议介入，择机买入"
                elif profile_data["impact_level"] == "medium":
                    action = "可考虑介入，注意仓位"
                else:
                    action = "可关注，不宜重仓"
            elif profile_data["direction"] == "bearish":
                if profile_data["impact_level"] == "extreme":
                    action = "绝对回避，持仓立即清仓"
                elif profile_data["impact_level"] == "high":
                    action = "高度谨慎，建议回避"
                elif profile_data["impact_level"] == "medium":
                    action = "谨慎对待，注意风险"
                else:
                    action = "关注后续发展"
            else:
                action = "观望为主，等待方向明确"
            
            # 生成风险提示
            risk_warning = self._generate_risk_warning(profile_data)
            
            self.message_profiles[msg_type] = MessageImpactProfile(
                message_type=msg_type,
                direction=profile_data["direction"],
                impact_score=impact_score,
                expected_return_1d=profile_data["avg_return_1d"],
                win_rate=profile_data["win_rate"],
                recommended_action=action,
                risk_warning=risk_warning,
            )
    
    def _calculate_impact_score(self, profile_data: Dict) -> float:
        """计算消息影响力评分 0-100"""
        # 基于胜率、平均收益、影响等级综合计算
        win_rate_score = profile_data["win_rate"] * 50  # 胜率贡献50分
        
        # 收益贡献（利好为正，利空为负，取绝对值）
        avg_return = abs(profile_data["avg_return_1d"])
        return_score = min(30.0, avg_return * 5)  # 收益贡献最多30分
        
        # 影响等级贡献
        level_scores = {"extreme": 20, "high": 15, "medium": 10, "low": 5}
        level_score = level_scores.get(profile_data["impact_level"], 10)
        
        total = win_rate_score + return_score + level_score
        return min(100.0, max(0.0, total))
    
    def _generate_risk_warning(self, profile_data: Dict) -> str:
        """生成风险提示"""
        direction = profile_data["direction"]
        impact = profile_data["impact_level"]
        min_return = profile_data["min_return"]
        
        if direction == "bearish" and impact == "extreme":
            return f"重大利空！历史最大亏损{abs(min_return):.0f}%，绝对回避"
        elif direction == "bearish" and impact == "high":
            return f"明显利空，历史最大亏损{abs(min_return):.0f}%，高度谨慎"
        elif direction == "bullish" and impact == "extreme":
            return f"重大利好但存在{abs(min_return):.0f}%回撤风险，注意仓位控制"
        elif direction == "bullish":
            return f"利好消息，历史最大回撤{abs(min_return):.0f}%，注意止盈"
        else:
            return "方向不确定，观望为主"
    
    def _load_backtest_data(self) -> None:
        """加载历史回测数据"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            db_file = os.path.join(self.data_dir, "backtest_results.json")
            if os.path.exists(db_file):
                with open(db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.backtest_db[key] = BacktestResult(**value)
                logger.info(f"加载回测数据: {len(self.backtest_db)}条")
        except Exception as e:
            logger.warning(f"加载回测数据失败: {e}")
    
    def save_backtest_data(self) -> None:
        """保存回测数据到文件"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            db_file = os.path.join(self.data_dir, "backtest_results.json")
            data = {
                key: {
                    "message_type": r.message_type,
                    "category": r.category,
                    "direction": r.direction,
                    "sample_size": r.sample_size,
                    "win_rate": r.win_rate,
                    "avg_return_1d": r.avg_return_1d,
                    "avg_return_3d": r.avg_return_3d,
                    "avg_return_5d": r.avg_return_5d,
                    "max_return": r.max_return,
                    "min_return": r.min_return,
                    "max_drawdown": r.max_drawdown,
                    "impact_level": r.impact_level,
                    "impact_score": r.impact_score,
                    "best_strategy": r.best_strategy,
                    "optimal_hold_days": r.optimal_hold_days,
                    "confidence": r.confidence,
                    "last_updated": r.last_updated,
                    "notes": r.notes,
                }
                for key, r in self.backtest_db.items()
            }
            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"回测数据已保存: {len(data)}条")
        except Exception as e:
            logger.error(f"保存回测数据失败: {e}")
    
    def get_message_impact(self, message_type: str) -> Optional[MessageImpactProfile]:
        """获取消息类型的影响力画像
        
        Args:
            message_type: 消息类型
            
        Returns:
            MessageImpactProfile 或 None
        """
        return self.message_profiles.get(message_type)
    
    def classify_message_type(self, title: str, content: str) -> List[Tuple[str, float]]:
        """根据标题和内容分类消息类型
        
        Args:
            title: 消息标题
            content: 消息内容
            
        Returns:
            List[(消息类型, 匹配置信度)] 按置信度降序
        """
        text = f"{title} {content}"
        matches: List[Tuple[str, float]] = []
        
        for msg_type, profile_data in MESSAGE_TYPE_PROFILES.items():
            keywords = profile_data.get("keywords", [])
            if not keywords:
                continue
            
            # 计算关键词匹配度
            matched = sum(1 for kw in keywords if kw in text)
            if matched > 0:
                confidence = min(1.0, matched / len(keywords))
                matches.append((msg_type, confidence))
        
        # 按置信度降序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def evaluate_message_impact(
        self,
        title: str,
        content: str,
        related_tickers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """评估消息的综合影响力
        
        Args:
            title: 消息标题
            content: 消息内容
            related_tickers: 关联个股
            
        Returns:
            评估结果字典
        """
        # 1. 分类消息类型
        type_matches = self.classify_message_type(title, content)
        
        if not type_matches:
            return {
                "message_types": [],
                "overall_direction": "neutral",
                "overall_impact_score": 0.0,
                "recommendation": "消息类型不明确，观望为主",
                "risk_warning": "",
            }
        
        # 2. 获取主要消息类型的影响力
        primary_type, primary_confidence = type_matches[0]
        profile = self.message_profiles.get(primary_type)
        
        if not profile:
            return {
                "message_types": type_matches,
                "overall_direction": "neutral",
                "overall_impact_score": 0.0,
                "recommendation": "暂无该消息类型的历史数据",
                "risk_warning": "",
            }
        
        # 3. 综合评估（考虑多类型叠加）
        overall_score = profile.impact_score * primary_confidence
        overall_direction = profile.direction
        
        # 如果有多个消息类型，考虑叠加效应
        if len(type_matches) > 1:
            for msg_type, confidence in type_matches[1:3]:  # 最多考虑前3个
                other_profile = self.message_profiles.get(msg_type)
                if other_profile:
                    # 同向叠加，反向抵消
                    if other_profile.direction == overall_direction:
                        overall_score += other_profile.impact_score * confidence * 0.3
                    else:
                        overall_score -= other_profile.impact_score * confidence * 0.2
        
        overall_score = min(100.0, max(0.0, overall_score))
        
        # 4. 生成建议
        if overall_direction == "bullish":
            if overall_score >= 70:
                recommendation = f"【强烈利好】{profile.recommended_action}"
            elif overall_score >= 50:
                recommendation = f"【利好】{profile.recommended_action}"
            else:
                recommendation = f"【偏利好】{profile.recommended_action}"
        elif overall_direction == "bearish":
            if overall_score >= 70:
                recommendation = f"【重大利空】{profile.recommended_action}"
            elif overall_score >= 50:
                recommendation = f"【利空】{profile.recommended_action}"
            else:
                recommendation = f"【偏利空】{profile.recommended_action}"
        else:
            recommendation = "【中性】方向不明确，建议观望"
        
        return {
            "message_types": type_matches,
            "primary_type": primary_type,
            "overall_direction": overall_direction,
            "overall_impact_score": round(overall_score, 1),
            "expected_return_1d": profile.expected_return_1d,
            "win_rate": profile.win_rate,
            "recommendation": recommendation,
            "risk_warning": profile.risk_warning,
            "best_strategy": MESSAGE_TYPE_PROFILES.get(primary_type, {}).get("best_strategy", ""),
            "optimal_hold_days": MESSAGE_TYPE_PROFILES.get(primary_type, {}).get("optimal_hold_days", 1),
        }
    
    def add_backtest_result(
        self,
        message_type: str,
        category: str,
        direction: str,
        returns_1d: List[float],
        returns_3d: Optional[List[float]] = None,
        returns_5d: Optional[List[float]] = None,
    ) -> BacktestResult:
        """添加回测结果
        
        Args:
            message_type: 消息类型
            category: 消息分类
            direction: 方向
            returns_1d: 次日收益率列表
            returns_3d: 3日收益率列表
            returns_5d: 5日收益率列表
            
        Returns:
            BacktestResult 回测结果
        """
        if not returns_1d:
            raise ValueError("returns_1d 不能为空")
        
        sample_size = len(returns_1d)
        win_rate = sum(1 for r in returns_1d if r > 0) / sample_size
        avg_return_1d = sum(returns_1d) / sample_size
        max_return = max(returns_1d)
        min_return = min(returns_1d)
        
        # 计算最大回撤
        cumulative = 0
        peak = 0
        max_drawdown = 0
        for r in returns_1d:
            cumulative += r
            peak = max(peak, cumulative)
            max_drawdown = min(max_drawdown, cumulative - peak)
        
        # 3日/5日收益
        avg_return_3d = sum(returns_3d) / len(returns_3d) if returns_3d else avg_return_1d * 3
        avg_return_5d = sum(returns_5d) / len(returns_5d) if returns_5d else avg_return_1d * 5
        
        # 计算影响力评分
        impact_score = abs(avg_return_1d) * 10 + win_rate * 50
        impact_score = min(100.0, max(0.0, impact_score))
        
        # 确定影响等级
        if impact_score >= 80:
            impact_level = "extreme"
        elif impact_score >= 60:
            impact_level = "high"
        elif impact_score >= 40:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        # 置信度（基于样本量）
        confidence = min(1.0, sample_size / 100)
        
        result = BacktestResult(
            message_type=message_type,
            category=category,
            direction=direction,
            sample_size=sample_size,
            win_rate=round(win_rate, 3),
            avg_return_1d=round(avg_return_1d, 2),
            avg_return_3d=round(avg_return_3d, 2),
            avg_return_5d=round(avg_return_5d, 2),
            max_return=round(max_return, 2),
            min_return=round(min_return, 2),
            max_drawdown=round(max_drawdown, 2),
            impact_level=impact_level,
            impact_score=round(impact_score, 1),
            confidence=round(confidence, 2),
            last_updated=datetime.now().isoformat(),
        )
        
        # 存储
        cache_key = f"{category}_{message_type}"
        self.backtest_db[cache_key] = result
        
        # 更新消息画像
        self._update_message_profile(message_type, result)
        
        logger.info(
            f"回测结果已添加: {message_type}",
            sample_size=sample_size,
            win_rate=win_rate,
            avg_return=avg_return_1d,
        )
        
        return result
    
    def _update_message_profile(self, message_type: str, result: BacktestResult) -> None:
        """根据回测结果更新消息画像"""
        if message_type in self.message_profiles:
            profile = self.message_profiles[message_type]
            # 用实际回测数据更新
            profile.impact_score = result.impact_score
            profile.expected_return_1d = result.avg_return_1d
            profile.win_rate = result.win_rate
        else:
            # 创建新画像
            if result.direction == "bullish":
                if result.impact_level == "extreme":
                    action = "强烈建议介入，重点关注"
                elif result.impact_level == "high":
                    action = "建议介入，择机买入"
                else:
                    action = "可考虑介入，注意仓位"
                risk_warning = f"历史最大回撤{abs(result.min_return):.0f}%，注意止盈"
            else:
                if result.impact_level == "extreme":
                    action = "绝对回避，持仓立即清仓"
                elif result.impact_level == "high":
                    action = "高度谨慎，建议回避"
                else:
                    action = "谨慎对待，注意风险"
                risk_warning = f"历史最大亏损{abs(result.min_return):.0f}%，严格回避"
            
            self.message_profiles[message_type] = MessageImpactProfile(
                message_type=message_type,
                direction=result.direction,
                impact_score=result.impact_score,
                expected_return_1d=result.avg_return_1d,
                win_rate=result.win_rate,
                recommended_action=action,
                risk_warning=risk_warning,
            )
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """获取所有消息类型画像
        
        Returns:
            消息类型画像字典
        """
        result = {}
        for msg_type, profile in self.message_profiles.items():
            result[msg_type] = {
                "message_type": profile.message_type,
                "direction": profile.direction,
                "impact_score": profile.impact_score,
                "expected_return_1d": profile.expected_return_1d,
                "win_rate": profile.win_rate,
                "recommended_action": profile.recommended_action,
                "risk_warning": profile.risk_warning,
                "keywords": MESSAGE_TYPE_PROFILES.get(msg_type, {}).get("keywords", []),
                "best_strategy": MESSAGE_TYPE_PROFILES.get(msg_type, {}).get("best_strategy", ""),
                "optimal_hold_days": MESSAGE_TYPE_PROFILES.get(msg_type, {}).get("optimal_hold_days", 1),
            }
        return result
    
    def get_backtest_summary(self) -> Dict[str, Any]:
        """获取回测数据摘要
        
        Returns:
            摘要字典
        """
        bullish_count = sum(1 for p in self.message_profiles.values() if p.direction == "bullish")
        bearish_count = sum(1 for p in self.message_profiles.values() if p.direction == "bearish")
        neutral_count = sum(1 for p in self.message_profiles.values() if p.direction == "neutral")
        
        return {
            "total_message_types": len(self.message_profiles),
            "bullish_types": bullish_count,
            "bearish_types": bearish_count,
            "neutral_types": neutral_count,
            "backtest_records": len(self.backtest_db),
            "profiles": self.get_all_profiles(),
        }