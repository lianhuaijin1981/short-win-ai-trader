"""维度评分器 — 评分决策核心组件

为超短选手提供多维度标的评分:
- 题材强度评分: 题材级别、持续性、板块效应、政策催化
- 资金匹配评分: 主力净流入、量价配合、封单强度、龙虎榜
- 情绪周期评分: 周期匹配度、赚钱效应、连板高度、炸板率
- 筹码结构评分: 集中度、套牢盘、底部锁定、筹码峰形态
- 技术形态评分: 均线系统、突破形态、量能配合、MACD/KDJ
- 龙头地位评分: 身位优势、辨识度、带动性、抗跌性
- 资讯催化评分: 催化级别、时效性、市场反馈、持续性

每个维度0-100分，综合加权得出总分。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.logger import get_logger

logger = get_logger("swat.m06.dimension_scorers")


# ── 数据类 ──────────────────────────────────────────────

@dataclass
class DimensionScore:
    """单维度评分结果"""
    dimension: str = ""             # 维度名称
    score: float = 0.0              # 评分(0-100)
    weight: float = 0.0             # 权重
    weighted_score: float = 0.0     # 加权分
    details: Dict = field(default_factory=dict)  # 评分明细
    assessment: str = ""            # 评估结论


@dataclass
class ThemeStrengthScore:
    """题材强度评分明细"""
    theme_level: float = 0.0        # 题材级别(0-100)
    sustainability: float = 0.0     # 持续性(0-100)
    sector_effect: float = 0.0      # 板块效应(0-100)
    policy_catalyst: float = 0.0    # 政策催化(0-100)
    theme_purity: float = 0.0       # 题材纯正度(0-100)


@dataclass
class FundMatchScore:
    """资金匹配评分明细"""
    main_inflow: float = 0.0        # 主力净流入(0-100)
    volume_price: float = 0.0       # 量价配合(0-100)
    seal_strength: float = 0.0      # 封单强度(0-100)
    dragon_bond: float = 0.0        # 龙虎榜质量(0-100)
    big_order: float = 0.0          # 大单净流入(0-100)


@dataclass
class EmotionCycleScore:
    """情绪周期评分明细"""
    cycle_match: float = 0.0        # 周期匹配度(0-100)
    profit_effect: float = 0.0      # 赚钱效应(0-100)
    board_height: float = 0.0       # 连板高度(0-100)
    explode_rate: float = 0.0       # 炸板率(反向)(0-100)
    limit_up_count: float = 0.0     # 涨停数量(0-100)


@dataclass
class ChipStructureScore:
    """筹码结构评分明细"""
    concentration: float = 0.0      # 筹码集中度(0-100)
    trapped_ratio: float = 0.0      # 套牢盘比例(反向)(0-100)
    bottom_lock: float = 0.0        # 底部锁定度(0-100)
    peak_shape: float = 0.0         # 筹码峰形态(0-100)
    turnover_rate: float = 0.0      # 换手率合理性(0-100)


@dataclass
class TechnicalScore:
    """技术形态评分明细"""
    ma_system: float = 0.0          # 均线系统(0-100)
    breakout: float = 0.0           # 突破形态(0-100)
    volume_match: float = 0.0       # 量能配合(0-100)
    macd: float = 0.0               # MACD指标(0-100)
    kdj: float = 0.0                # KDJ指标(0-100)


@dataclass
class DragonStatusScore:
    """龙头地位评分明细"""
    position_advantage: float = 0.0  # 身位优势(0-100)
    recognition: float = 0.0         # 辨识度(0-100)
    driving_power: float = 0.0       # 带动性(0-100)
    anti_fall: float = 0.0           # 抗跌性(0-100)
    board_count: float = 0.0         # 连板数(0-100)


@dataclass
class NewsCatalystScore:
    """资讯催化评分明细"""
    catalyst_level: float = 0.0     # 催化级别(0-100)
    timeliness: float = 0.0         # 时效性(0-100)
    market_feedback: float = 0.0    # 市场反馈(0-100)
    sustainability: float = 0.0     # 持续性(0-100)


# ── 维度权重配置 ─────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "theme_strength": 0.20,     # 题材强度: 20%
    "fund_match": 0.18,         # 资金匹配: 18%
    "emotion_cycle": 0.17,      # 情绪周期: 17%
    "chip_structure": 0.12,     # 筹码结构: 12%
    "technical": 0.15,          # 技术形态: 15%
    "dragon_status": 0.10,      # 龙头地位: 10%
    "news_catalyst": 0.08,      # 资讯催化: 8%
}


# ── 题材强度评分器 ───────────────────────────────────────

class ThemeStrengthScorer:
    """题材强度评分器
    
    评估标的所属题材的强度和持续性。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 题材数据
                - theme_level: 题材级别(国家级/部委级/地方级/企业级)
                - sustainability: 题材持续性(新题材/发酵中/高潮/退潮)
                - sector_limit_up: 板块涨停数
                - sector_avg_change: 板块平均涨幅
                - policy_support: 是否有政策支持
                - theme_purity: 题材纯正度(核心/边缘)
        
        Returns:
            DimensionScore: 评分结果
        """
        # 题材级别评分
        theme_level_map = {
            "国家级": 95, "部委级": 80, "地方级": 60, "企业级": 40, "概念炒作": 30
        }
        theme_level = theme_level_map.get(data.get("theme_level", "概念炒作"), 40)
        
        # 持续性评分
        sustainability_map = {
            "新题材": 90, "发酵中": 85, "高潮": 60, "退潮": 25, "反复活跃": 75
        }
        sustainability = sustainability_map.get(data.get("sustainability", "新题材"), 60)
        
        # 板块效应评分
        sector_limit_up = data.get("sector_limit_up", 0)
        sector_avg_change = data.get("sector_avg_change", 0)
        sector_effect = min(100, sector_limit_up * 10 + max(0, sector_avg_change * 5))
        
        # 政策催化评分
        policy_support = data.get("policy_support", False)
        policy_catalyst = 85 if policy_support else 40
        
        # 题材纯正度
        purity_map = {"核心": 90, "正宗": 75, "边缘": 40, "蹭热点": 20}
        theme_purity = purity_map.get(data.get("theme_purity", "边缘"), 40)
        
        # 综合评分
        score = (
            theme_level * 0.30 +
            sustainability * 0.25 +
            sector_effect * 0.20 +
            policy_catalyst * 0.10 +
            theme_purity * 0.15
        )
        score = round(max(0, min(100, score)), 1)
        
        # 评估结论
        if score >= 80:
            assessment = "题材强度极高，主线明确，可持续参与"
        elif score >= 65:
            assessment = "题材强度较好，有一定持续性"
        elif score >= 50:
            assessment = "题材强度一般，注意快进快出"
        else:
            assessment = "题材强度弱，缺乏持续性，谨慎参与"
        
        return DimensionScore(
            dimension="题材强度",
            score=score,
            weight=DIMENSION_WEIGHTS["theme_strength"],
            weighted_score=round(score * DIMENSION_WEIGHTS["theme_strength"], 1),
            details={
                "题材级别": theme_level,
                "持续性": sustainability,
                "板块效应": round(sector_effect, 1),
                "政策催化": policy_catalyst,
                "题材纯正度": theme_purity,
            },
            assessment=assessment,
        )


# ── 资金匹配评分器 ───────────────────────────────────────

class FundMatchScorer:
    """资金匹配评分器
    
    评估资金流向和量价配合情况。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 资金数据
                - main_net_inflow: 主力净流入(万元)
                - main_inflow_ratio: 主力净流入占比(%)
                - volume_ratio: 量比
                - change_pct: 涨幅(%)
                - seal_amount: 封单金额(万元)
                - dragon_bond_quality: 龙虎榜质量(机构/游资/散户)
                - big_order_ratio: 大单占比(%)
        
        Returns:
            DimensionScore: 评分结果
        """
        # 主力净流入评分
        main_inflow = data.get("main_net_inflow", 0)
        main_inflow_ratio = data.get("main_inflow_ratio", 0)
        if main_inflow > 5000:
            main_inflow_score = 95
        elif main_inflow > 2000:
            main_inflow_score = 80
        elif main_inflow > 500:
            main_inflow_score = 65
        elif main_inflow > 0:
            main_inflow_score = 50
        else:
            main_inflow_score = max(20, 50 + main_inflow_ratio * 2)
        
        # 量价配合评分
        volume_ratio = data.get("volume_ratio", 1.0)
        change_pct = data.get("change_pct", 0)
        if change_pct > 0 and volume_ratio > 1.5:
            volume_price = min(100, 60 + volume_ratio * 8 + change_pct * 2)
        elif change_pct > 0 and volume_ratio < 1:
            volume_price = 45  # 缩量上涨，持续性存疑
        elif change_pct < 0 and volume_ratio > 2:
            volume_price = 25  # 放量下跌，危险
        else:
            volume_price = 50
        
        # 封单强度评分
        seal_amount = data.get("seal_amount", 0)
        if seal_amount > 10000:
            seal_strength = 95
        elif seal_amount > 5000:
            seal_strength = 80
        elif seal_amount > 1000:
            seal_strength = 65
        elif seal_amount > 0:
            seal_strength = 50
        else:
            seal_strength = 40
        
        # 龙虎榜质量评分
        bond_quality_map = {
            "机构+顶级游资": 95, "机构": 85, "顶级游资": 80,
            "一般游资": 60, "散户": 30, "无": 40
        }
        dragon_bond = bond_quality_map.get(data.get("dragon_bond_quality", "无"), 40)
        
        # 大单净流入评分
        big_order_ratio = data.get("big_order_ratio", 0)
        big_order = min(100, max(0, 50 + big_order_ratio * 3))
        
        # 综合评分
        score = (
            main_inflow_score * 0.30 +
            volume_price * 0.25 +
            seal_strength * 0.20 +
            dragon_bond * 0.15 +
            big_order * 0.10
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = "资金面极强，主力大幅流入，量价配合良好"
        elif score >= 65:
            assessment = "资金面较好，有一定主力参与"
        elif score >= 50:
            assessment = "资金面一般，主力参与度不高"
        else:
            assessment = "资金面弱，主力流出或缺乏关注"
        
        return DimensionScore(
            dimension="资金匹配",
            score=score,
            weight=DIMENSION_WEIGHTS["fund_match"],
            weighted_score=round(score * DIMENSION_WEIGHTS["fund_match"], 1),
            details={
                "主力净流入": round(main_inflow_score, 1),
                "量价配合": round(volume_price, 1),
                "封单强度": seal_strength,
                "龙虎榜质量": dragon_bond,
                "大单占比": round(big_order, 1),
            },
            assessment=assessment,
        )


# ── 情绪周期评分器 ───────────────────────────────────────

class EmotionCycleScorer:
    """情绪周期评分器
    
    评估当前市场情绪周期与标的的匹配度。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 情绪数据
                - current_cycle: 当前情绪周期(启动/发酵/高潮/分歧/退潮/混沌)
                - stock_cycle_position: 标的在周期中的位置
                - profit_effect: 赚钱效应(好/一般/差)
                - max_board_height: 最高连板数
                - explode_rate: 炸板率(%)
                - limit_up_count: 涨停数
                - limit_down_count: 跌停数
        
        Returns:
            DimensionScore: 评分结果
        """
        # 周期匹配度评分
        current_cycle = data.get("current_cycle", "混沌")
        stock_position = data.get("stock_cycle_position", "跟风")
        
        # 不同周期适合不同类型标的
        cycle_match_matrix = {
            "启动": {"先锋": 95, "龙头": 85, "跟风": 50, "补涨": 40},
            "发酵": {"龙头": 95, "先锋": 80, "补涨": 70, "跟风": 45},
            "高潮": {"龙头": 90, "补涨": 75, "先锋": 60, "跟风": 30},
            "分歧": {"龙头": 80, "中军": 75, "先锋": 50, "跟风": 20},
            "退潮": {"龙头": 40, "中军": 35, "先锋": 25, "跟风": 10},
            "混沌": {"先锋": 60, "龙头": 50, "跟风": 30, "补涨": 35},
        }
        cycle_match = cycle_match_matrix.get(current_cycle, {}).get(stock_position, 40)
        
        # 赚钱效应评分
        profit_map = {"极好": 95, "好": 80, "一般": 55, "差": 30, "极差": 15}
        profit_effect = profit_map.get(data.get("profit_effect", "一般"), 55)
        
        # 连板高度评分
        max_board = data.get("max_board_height", 0)
        if max_board >= 7:
            board_height = 90
        elif max_board >= 5:
            board_height = 80
        elif max_board >= 3:
            board_height = 65
        elif max_board >= 2:
            board_height = 50
        else:
            board_height = 30
        
        # 炸板率评分(反向)
        explode_rate = data.get("explode_rate", 0)
        if explode_rate < 20:
            explode_score = 90
        elif explode_rate < 35:
            explode_score = 70
        elif explode_rate < 50:
            explode_score = 50
        else:
            explode_score = max(10, 100 - explode_rate)
        
        # 涨停数量评分
        limit_up_count = data.get("limit_up_count", 0)
        if limit_up_count >= 50:
            limit_up_score = 90
        elif limit_up_count >= 30:
            limit_up_score = 75
        elif limit_up_count >= 15:
            limit_up_score = 60
        elif limit_up_count >= 5:
            limit_up_score = 45
        else:
            limit_up_score = 25
        
        # 综合评分
        score = (
            cycle_match * 0.30 +
            profit_effect * 0.25 +
            board_height * 0.15 +
            explode_score * 0.15 +
            limit_up_score * 0.15
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = f"情绪周期{current_cycle}，赚钱效应好，适合积极操作"
        elif score >= 60:
            assessment = f"情绪周期{current_cycle}，赚钱效应一般，谨慎操作"
        elif score >= 40:
            assessment = f"情绪周期{current_cycle}，赚钱效应差，控制仓位"
        else:
            assessment = f"情绪周期{current_cycle}，赚钱效应极差，管住手"
        
        return DimensionScore(
            dimension="情绪周期",
            score=score,
            weight=DIMENSION_WEIGHTS["emotion_cycle"],
            weighted_score=round(score * DIMENSION_WEIGHTS["emotion_cycle"], 1),
            details={
                "周期匹配度": cycle_match,
                "赚钱效应": profit_effect,
                "连板高度": board_height,
                "炸板率": round(explode_score, 1),
                "涨停数量": limit_up_score,
            },
            assessment=assessment,
        )


# ── 筹码结构评分器 ───────────────────────────────────────

class ChipStructureScorer:
    """筹码结构评分器
    
    评估筹码分布和结构质量。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 筹码数据
                - chip_concentration: 筹码集中度(%)
                - trapped_ratio: 套牢盘比例(%)
                - bottom_lock_ratio: 底部锁定比例(%)
                - peak_type: 筹码峰类型(单峰/双峰/多峰/分散)
                - turnover_rate: 换手率(%)
                - avg_cost_distance: 距平均成本距离(%)
        
        Returns:
            DimensionScore: 评分结果
        """
        # 筹码集中度评分
        concentration = data.get("chip_concentration", 50)
        if concentration >= 70:
            concentration_score = 90
        elif concentration >= 50:
            concentration_score = 75
        elif concentration >= 30:
            concentration_score = 55
        else:
            concentration_score = 35
        
        # 套牢盘比例评分(反向)
        trapped_ratio = data.get("trapped_ratio", 50)
        if trapped_ratio < 10:
            trapped_score = 95
        elif trapped_ratio < 25:
            trapped_score = 80
        elif trapped_ratio < 40:
            trapped_score = 60
        elif trapped_ratio < 60:
            trapped_score = 40
        else:
            trapped_score = max(10, 100 - trapped_ratio)
        
        # 底部锁定度评分
        bottom_lock = data.get("bottom_lock_ratio", 30)
        if bottom_lock >= 50:
            bottom_lock_score = 90
        elif bottom_lock >= 30:
            bottom_lock_score = 70
        elif bottom_lock >= 15:
            bottom_lock_score = 55
        else:
            bottom_lock_score = 40
        
        # 筹码峰形态评分
        peak_map = {"单峰密集": 90, "双峰": 65, "多峰": 45, "分散": 25}
        peak_shape = peak_map.get(data.get("peak_type", "分散"), 30)
        
        # 换手率合理性评分
        turnover = data.get("turnover_rate", 5)
        if 5 <= turnover <= 15:
            turnover_score = 85  # 健康换手
        elif 3 <= turnover < 5 or 15 < turnover <= 25:
            turnover_score = 65  # 可接受
        elif turnover < 3:
            turnover_score = 45  # 换手不足
        else:
            turnover_score = max(15, 100 - turnover * 2)  # 换手过高
        
        # 综合评分
        score = (
            concentration_score * 0.25 +
            trapped_score * 0.25 +
            bottom_lock_score * 0.20 +
            peak_shape * 0.15 +
            turnover_score * 0.15
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = "筹码结构优良，集中度高，套牢盘少"
        elif score >= 60:
            assessment = "筹码结构较好，有一定集中度"
        elif score >= 40:
            assessment = "筹码结构一般，存在一定套牢压力"
        else:
            assessment = "筹码结构差，套牢盘多，筹码分散"
        
        return DimensionScore(
            dimension="筹码结构",
            score=score,
            weight=DIMENSION_WEIGHTS["chip_structure"],
            weighted_score=round(score * DIMENSION_WEIGHTS["chip_structure"], 1),
            details={
                "筹码集中度": concentration_score,
                "套牢盘": trapped_score,
                "底部锁定": bottom_lock_score,
                "筹码峰形态": peak_shape,
                "换手率": turnover_score,
            },
            assessment=assessment,
        )


# ── 技术形态评分器 ───────────────────────────────────────

class TechnicalScorer:
    """技术形态评分器
    
    评估技术面形态和指标。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 技术数据
                - ma_arrangement: 均线排列(多头/粘合/空头)
                - price_ma5_distance: 股价距5日线距离(%)
                - breakout_type: 突破类型(平台突破/前高突破/无突破)
                - volume_ratio: 量比
                - macd_status: MACD状态(金叉/红柱放大/死叉/绿柱)
                - kdj_status: KDJ状态(金叉/超买/死叉/超卖)
                - support_price: 支撑位
                - resistance_price: 阻力位
                - current_price: 当前价
        
        Returns:
            DimensionScore: 评分结果
        """
        # 均线系统评分
        ma_map = {"多头排列": 90, "多头初期": 80, "粘合": 55, "空头初期": 35, "空头排列": 20}
        ma_system = ma_map.get(data.get("ma_arrangement", "粘合"), 50)
        
        # 股价与5日线距离
        ma5_distance = data.get("price_ma5_distance", 0)
        if 0 < ma5_distance <= 3:
            ma_system = min(100, ma_system + 10)  # 沿5日线上涨加分
        elif ma5_distance > 5:
            ma_system = max(10, ma_system - 15)  # 远离5日线扣分
        
        # 突破形态评分
        breakout_map = {
            "平台突破": 90, "前高突破": 85, "颈线突破": 80,
            "趋势线突破": 70, "无突破": 40, "假突破": 20
        }
        breakout = breakout_map.get(data.get("breakout_type", "无突破"), 40)
        
        # 量能配合评分
        volume_ratio = data.get("volume_ratio", 1.0)
        breakout_type = data.get("breakout_type", "无突破")
        if breakout_type != "无突破" and volume_ratio >= 2:
            volume_match = 90  # 突破放量
        elif breakout_type != "无突破" and volume_ratio >= 1.5:
            volume_match = 75
        elif volume_ratio >= 1:
            volume_match = 60
        else:
            volume_match = 40
        
        # MACD评分
        macd_map = {
            "金叉+红柱放大": 90, "金叉": 75, "红柱缩短": 55,
            "死叉": 30, "绿柱放大": 20, "绿柱缩短": 45
        }
        macd = macd_map.get(data.get("macd_status", "金叉"), 50)
        
        # KDJ评分
        kdj_map = {
            "金叉": 80, "金叉+超卖回升": 90, "超买": 50,
            "死叉": 30, "死叉+超买回落": 20, "超卖": 60
        }
        kdj = kdj_map.get(data.get("kdj_status", "金叉"), 50)
        
        # 综合评分
        score = (
            ma_system * 0.25 +
            breakout * 0.25 +
            volume_match * 0.20 +
            macd * 0.15 +
            kdj * 0.15
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = "技术形态强势，均线多头，突破有效"
        elif score >= 60:
            assessment = "技术形态较好，有一定上涨动能"
        elif score >= 40:
            assessment = "技术形态一般，需等待确认信号"
        else:
            assessment = "技术形态弱势，不建议介入"
        
        return DimensionScore(
            dimension="技术形态",
            score=score,
            weight=DIMENSION_WEIGHTS["technical"],
            weighted_score=round(score * DIMENSION_WEIGHTS["technical"], 1),
            details={
                "均线系统": ma_system,
                "突破形态": breakout,
                "量能配合": volume_match,
                "MACD": macd,
                "KDJ": kdj,
            },
            assessment=assessment,
        )


# ── 龙头地位评分器 ───────────────────────────────────────

class DragonStatusScorer:
    """龙头地位评分器
    
    评估标的在板块/市场中的龙头地位。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 龙头数据
                - dragon_type: 龙头类型(市场总龙/分支龙头/先锋龙/中军/跟风)
                - board_count: 连板数
                - sector_rank: 板块内排名
                - driving_effect: 带动效应(强/中/弱)
                - anti_fall_ability: 抗跌能力(强/中/弱)
                - recognition: 市场辨识度(高/中/低)
        
        Returns:
            DimensionScore: 评分结果
        """
        # 身位优势评分
        dragon_map = {
            "市场总龙": 95, "分支龙头": 80, "先锋龙": 75,
            "板块中军": 60, "补涨龙": 55, "跟风": 30
        }
        position_advantage = dragon_map.get(data.get("dragon_type", "跟风"), 30)
        
        # 辨识度评分
        recognition_map = {"极高": 95, "高": 80, "中": 55, "低": 30}
        recognition = recognition_map.get(data.get("recognition", "中"), 50)
        
        # 带动性评分
        driving_map = {"极强": 95, "强": 80, "中": 55, "弱": 30}
        driving_power = driving_map.get(data.get("driving_effect", "中"), 50)
        
        # 抗跌性评分
        anti_fall_map = {"极强": 90, "强": 75, "中": 55, "弱": 30}
        anti_fall = anti_fall_map.get(data.get("anti_fall_ability", "中"), 50)
        
        # 连板数评分
        board_count = data.get("board_count", 0)
        if board_count >= 5:
            board_score = 95
        elif board_count >= 3:
            board_score = 80
        elif board_count >= 2:
            board_score = 60
        elif board_count == 1:
            board_score = 45
        else:
            board_score = 25
        
        # 综合评分
        score = (
            position_advantage * 0.30 +
            recognition * 0.20 +
            driving_power * 0.20 +
            anti_fall * 0.15 +
            board_score * 0.15
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = "龙头地位明确，身位优势明显，带动性强"
        elif score >= 60:
            assessment = "有一定龙头特征，但地位不够稳固"
        elif score >= 40:
            assessment = "龙头特征不明显，偏跟风属性"
        else:
            assessment = "纯跟风标的，无龙头地位"
        
        return DimensionScore(
            dimension="龙头地位",
            score=score,
            weight=DIMENSION_WEIGHTS["dragon_status"],
            weighted_score=round(score * DIMENSION_WEIGHTS["dragon_status"], 1),
            details={
                "身位优势": position_advantage,
                "辨识度": recognition,
                "带动性": driving_power,
                "抗跌性": anti_fall,
                "连板数": board_score,
            },
            assessment=assessment,
        )


# ── 资讯催化评分器 ───────────────────────────────────────

class NewsCatalystScorer:
    """资讯催化评分器
    
    评估资讯/催化对标的的影响。
    """
    
    def score(self, data: Dict) -> DimensionScore:
        """评分
        
        Args:
            data: 资讯数据
                - catalyst_level: 催化级别(重大/重要/一般/微弱)
                - timeliness: 时效性(当日/近日/过期)
                - market_feedback: 市场反馈(积极/中性/消极)
                - sustainability: 持续性(长期/中期/短期/一次性)
                - news_count: 相关新闻数量
        
        Returns:
            DimensionScore: 评分结果
        """
        # 催化级别评分
        level_map = {"重大": 95, "重要": 80, "一般": 55, "微弱": 30}
        catalyst_level = level_map.get(data.get("catalyst_level", "一般"), 50)
        
        # 时效性评分
        time_map = {"当日": 95, "近日": 75, "本周": 55, "过期": 20}
        timeliness = time_map.get(data.get("timeliness", "近日"), 60)
        
        # 市场反馈评分
        feedback_map = {"积极": 85, "中性": 55, "消极": 25}
        market_feedback = feedback_map.get(data.get("market_feedback", "中性"), 50)
        
        # 持续性评分
        sustain_map = {"长期": 90, "中期": 75, "短期": 55, "一次性": 30}
        sustainability = sustain_map.get(data.get("sustainability", "短期"), 50)
        
        # 综合评分
        score = (
            catalyst_level * 0.35 +
            timeliness * 0.25 +
            market_feedback * 0.20 +
            sustainability * 0.20
        )
        score = round(max(0, min(100, score)), 1)
        
        if score >= 80:
            assessment = "催化强劲，时效性好，市场反馈积极"
        elif score >= 60:
            assessment = "有一定催化，但力度有限"
        elif score >= 40:
            assessment = "催化较弱，市场关注度不高"
        else:
            assessment = "缺乏有效催化"
        
        return DimensionScore(
            dimension="资讯催化",
            score=score,
            weight=DIMENSION_WEIGHTS["news_catalyst"],
            weighted_score=round(score * DIMENSION_WEIGHTS["news_catalyst"], 1),
            details={
                "催化级别": catalyst_level,
                "时效性": timeliness,
                "市场反馈": market_feedback,
                "持续性": sustainability,
            },
            assessment=assessment,
        )