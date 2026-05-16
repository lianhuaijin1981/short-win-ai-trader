"""多战法共振选股引擎 — 双/三/多战法共振识别

核心逻辑:
  当一只股票同时匹配多个战法时，其上涨概率和持续性显著提升。
  本引擎识别并量化多战法共振效应:
  - 双战法共振: 同时匹配2套战法
  - 三战法共振: 同时匹配3套战法（强烈推荐）
  - 多战法共振: 同时匹配4套及以上（罕见信号）

共振评分体系:
  - 战法协同度: 匹配战法间的逻辑互补性
  - 信号强度: 各战法匹配分数加权
  - 时间窗口: 战法信号的时间集中度
  - 优先级: 共振级别 + 综合得分排序

Author: SWAT Engine
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.logger import get_logger
from ...data_platform.data_models import (
    ResonanceStock,
    TacticMatchResult,
)
from .tactics_library import get_tactic_by_name

logger = get_logger("swat.m05.resonance")


# ──────────────────────────────────────────────────────────
# 常量定义
# ──────────────────────────────────────────────────────────

# 共振级别阈值
RESONANCE_LEVELS = {
    "multi": {"min_tactics": 4, "label": "多战法共振", "priority": 1},
    "triple": {"min_tactics": 3, "label": "三战法共振", "priority": 2},
    "double": {"min_tactics": 2, "label": "双战法共振", "priority": 3},
}

# 战法协同矩阵 (协同系数 0.0-1.0)
# 定义哪些战法组合在一起具有更强的协同效应
TACTIC_SYNERGY_MATRIX: Dict[str, Dict[str, float]] = {
    "筹码峰战法": {
        "三倍量突破战法": 0.85,
        "缩量突破战法": 0.90,
        "平台突破战法": 0.80,
        "N字形战法": 0.75,
    },
    "三倍量突破战法": {
        "过左峰战法": 0.85,
        "平台突破战法": 0.90,
        "龙头情绪战法": 0.80,
        "一进二战法": 0.75,
    },
    "缩量突破战法": {
        "筹码峰战法": 0.90,
        "平台突破战法": 0.85,
        "N字形战法": 0.80,
        "分时承接战法": 0.70,
    },
    "过左峰战法": {
        "三倍量突破战法": 0.85,
        "龙头情绪战法": 0.80,
        "N字形战法": 0.75,
        "反核战法": 0.70,
    },
    "首阴战法": {
        "龙头情绪战法": 0.90,
        "分时承接战法": 0.75,
        "反核战法": 0.85,
    },
    "N字形战法": {
        "缩量突破战法": 0.80,
        "筹码峰战法": 0.75,
        "过左峰战法": 0.75,
        "龙头情绪战法": 0.85,
    },
    "喜鹊闹梅战法": {
        "三星探底战法": 0.90,
        "布林带战法": 0.75,
        "缩量尾盘先手战法": 0.70,
    },
    "平台突破战法": {
        "三倍量突破战法": 0.90,
        "缩量突破战法": 0.85,
        "筹码峰战法": 0.80,
        "布林带战法": 0.75,
    },
    "一进二战法": {
        "龙头情绪战法": 0.90,
        "分时承接战法": 0.70,
        "三倍量突破战法": 0.75,
    },
    "龙头情绪战法": {
        "首阴战法": 0.90,
        "N字形战法": 0.85,
        "一进二战法": 0.90,
        "过左峰战法": 0.80,
        "反核战法": 0.75,
    },
    "布林带战法": {
        "平台突破战法": 0.75,
        "喜鹊闹梅战法": 0.75,
        "三星探底战法": 0.70,
    },
    "分时承接战法": {
        "首阴战法": 0.75,
        "缩量尾盘先手战法": 0.80,
        "一进二战法": 0.70,
    },
    "三星探底战法": {
        "喜鹊闹梅战法": 0.90,
        "布林带战法": 0.70,
        "缩量尾盘先手战法": 0.75,
    },
    "反核战法": {
        "首阴战法": 0.85,
        "龙头情绪战法": 0.75,
        "过左峰战法": 0.70,
    },
    "缩量尾盘先手战法": {
        "分时承接战法": 0.80,
        "三星探底战法": 0.75,
        "喜鹊闹梅战法": 0.70,
    },
}

# 高协同战法组合（预定义的强力组合）
HIGH_SYNERGY_COMBOS: List[Dict] = [
    {
        "name": "突破三重奏",
        "tactics": ["三倍量突破战法", "平台突破战法", "过左峰战法"],
        "description": "量+形态+前高三重突破，主升信号极强",
        "bonus": 5.0,
    },
    {
        "name": "龙头低吸组合",
        "tactics": ["龙头情绪战法", "首阴战法", "分时承接战法"],
        "description": "龙头地位确认+首阴低吸+分时承接，精准择时",
        "bonus": 5.0,
    },
    {
        "name": "底部反转组合",
        "tactics": ["喜鹊闹梅战法", "三星探底战法", "布林带战法"],
        "description": "多重底部信号共振，反转确定性高",
        "bonus": 5.0,
    },
    {
        "name": "主力控盘组合",
        "tactics": ["筹码峰战法", "缩量突破战法", "N字形战法"],
        "description": "筹码锁定+缩量突破+二波启动，主力控盘度高",
        "bonus": 5.0,
    },
    {
        "name": "超短接力组合",
        "tactics": ["一进二战法", "龙头情绪战法", "三倍量突破战法"],
        "description": "连板接力+龙头+放量，适合情绪发酵期",
        "bonus": 5.0,
    },
]


# ──────────────────────────────────────────────────────────
# 共振分析引擎
# ──────────────────────────────────────────────────────────

class ResonanceEngine:
    """多战法共振选股引擎

    将多只个股的多战法匹配结果进行交叉分析，
    识别同一只股的战法共振现象，并给出量化评分。
    """

    def __init__(self):
        self.synergy_matrix = TACTIC_SYNERGY_MATRIX
        self.high_synergy_combos = HIGH_SYNERGY_COMBOS
        logger.info("战法共振引擎初始化完成")

    def analyze(self, tactic_results: Dict[str, List[TacticMatchResult]]) -> List[ResonanceStock]:
        """分析战法共振

        Args:
            tactic_results: 按战法名称分组的匹配结果字典
                {战法名: [TacticMatchResult, ...]}

        Returns:
            共振股票列表（按优先级和分数降序）
        """
        # 1. 按股票分组，收集每只股匹配的所有战法
        stock_tactics: Dict[str, Dict] = {}

        for tactic_name, results in tactic_results.items():
            for match in results:
                key = f"{match.ticker}_{match.stock_name}"
                if key not in stock_tactics:
                    stock_tactics[key] = {
                        "ticker": match.ticker,
                        "name": match.stock_name,
                        "matches": [],
                    }
                stock_tactics[key]["matches"].append(match)

        # 2. 筛选出匹配>=2个战法的股票
        resonance_list: List[ResonanceStock] = []
        for stock_data in stock_tactics.values():
            matches = stock_data["matches"]
            if len(matches) < 2:
                continue

            # 分析共振
            resonance = self._analyze_single_stock(
                stock_data["ticker"],
                stock_data["name"],
                matches,
            )
            if resonance:
                resonance_list.append(resonance)

        # 3. 按优先级和分数排序
        resonance_list.sort(key=lambda x: (x.priority, -self._get_resonance_score(x)))

        logger.info(f"共振分析完成: 发现{len(resonance_list)}只共振股")
        return resonance_list

    def _analyze_single_stock(self, ticker: str, name: str,
                              matches: List[TacticMatchResult]) -> Optional[ResonanceStock]:
        """分析单只股票的战法共振

        Args:
            ticker: 股票代码
            name: 股票名称
            matches: 该股匹配的战法列表

        Returns:
            ResonanceStock 或 None
        """
        tactic_names = [m.tactic_name for m in matches]
        tactic_count = len(tactic_names)

        # 确定共振级别
        level_info = self._get_resonance_level(tactic_count)

        # 计算协同度
        synergy_score = self._calc_synergy(tactic_names)

        # 计算加权分数
        weighted_score = self._calc_weighted_score(matches)

        # 检查是否命中高协同组合
        combo_bonus = self._check_high_synergy_combo(tactic_names)

        # 计算最终优先级
        final_score = weighted_score + synergy_score + combo_bonus["bonus"]
        priority = self._calc_priority(tactic_count, final_score)

        # 生成共振描述
        description = self._gen_resonance_description(
            tactic_names, level_info["label"], combo_bonus
        )

        return ResonanceStock(
            ticker=ticker,
            name=name,
            matched_tactics=tactic_names,
            resonance_level=level_info["label"],
            priority=priority,
        )

    def _get_resonance_level(self, tactic_count: int) -> Dict:
        """获取共振级别信息"""
        for level_key, level_info in RESONANCE_LEVELS.items():
            if tactic_count >= level_info["min_tactics"]:
                return level_info
        return {"label": "单战法", "priority": 9}

    def _calc_synergy(self, tactic_names: List[str]) -> float:
        """计算战法间的协同度得分 (0-15分)"""
        if len(tactic_names) < 2:
            return 0.0

        synergy_scores = []
        for i in range(len(tactic_names)):
            for j in range(i + 1, len(tactic_names)):
                t1, t2 = tactic_names[i], tactic_names[j]
                score = self.synergy_matrix.get(t1, {}).get(t2, 0.5)
                # 反向查找
                if score == 0.5:
                    score = self.synergy_matrix.get(t2, {}).get(t1, 0.5)
                synergy_scores.append(score)

        if not synergy_scores:
            return 0.0

        avg_synergy = sum(synergy_scores) / len(synergy_scores)
        # 协同度分: 平均分 * 10 + 组合数加分
        combo_bonus = min(5.0, len(synergy_scores) * 0.5)
        return round(avg_synergy * 10 + combo_bonus, 1)

    def _calc_weighted_score(self, matches: List[TacticMatchResult]) -> float:
        """计算加权综合分数 (基础分0-60)"""
        if not matches:
            return 0.0

        # 按匹配分数加权，高分战法权重更大
        sorted_matches = sorted(matches, key=lambda x: x.match_score, reverse=True)

        weights = [0.4, 0.3, 0.2, 0.1]
        total_weight = 0.0
        weighted_sum = 0.0

        for i, match in enumerate(sorted_matches[:4]):
            w = weights[i] if i < len(weights) else 0.05
            weighted_sum += match.match_score * w
            total_weight += w

        return round(weighted_sum / total_weight * 0.6, 1) if total_weight > 0 else 0.0

    def _check_high_synergy_combo(self, tactic_names: List[str]) -> Dict:
        """检查是否命中高协同预定义组合"""
        tactic_set = set(tactic_names)

        for combo in self.high_synergy_combos:
            combo_set = set(combo["tactics"])
            # 至少命中组合中的80%
            if len(combo_set & tactic_set) >= len(combo_set) * 0.8:
                return {
                    "matched": True,
                    "combo_name": combo["name"],
                    "description": combo["description"],
                    "bonus": combo["bonus"],
                }

        return {"matched": False, "combo_name": "", "description": "", "bonus": 0.0}

    def _calc_priority(self, tactic_count: int, final_score: float) -> int:
        """计算优先级 (数值越小越优先)"""
        base_priority = max(1, 10 - tactic_count * 2)
        score_adjustment = max(0, int((final_score - 60) / 10))
        return max(1, base_priority - score_adjustment)

    def _gen_resonance_description(self, tactic_names: List[str],
                                    level: str, combo: Dict) -> str:
        """生成共振描述"""
        parts = [f"{level}: 同时匹配 {', '.join(tactic_names)}"]
        if combo["matched"]:
            parts.append(f"命中强力组合「{combo['combo_name']}」: {combo['description']}")
        return "; ".join(parts)

    def _get_resonance_score(self, rs: ResonanceStock) -> float:
        """获取共振股票综合分数（用于排序）"""
        tactic_count = len(rs.matched_tactics)
        priority_bonus = max(0, 10 - rs.priority) * 5
        return tactic_count * 10 + priority_bonus


# ──────────────────────────────────────────────────────────
# 便捷函数
# ──────────────────────────────────────────────────────────

def find_resonance_stocks(tactic_results: Dict[str, List[TacticMatchResult]],
                           min_tactics: int = 2) -> List[ResonanceStock]:
    """从战法匹配结果中找出共振股票

    Args:
        tactic_results: 按战法名称分组的匹配结果
        min_tactics: 最少战法匹配数（默认2，即双战法共振）

    Returns:
        共振股票列表
    """
    engine = ResonanceEngine()
    all_resonance = engine.analyze(tactic_results)

    # 过滤
    filtered = [
        r for r in all_resonance
        if len(r.matched_tactics) >= min_tactics
    ]

    level_label = {2: "双战法", 3: "三战法", 4: "多战法"}.get(min_tactics, f"{min_tactics}战法")
    logger.info(f"{level_label}共振筛选: {len(filtered)}只股票")

    return filtered


def get_resonance_summary(resonance_stocks: List[ResonanceStock]) -> Dict[str, Any]:
    """获取共振分析摘要统计

    Args:
        resonance_stocks: 共振股票列表

    Returns:
        统计字典
    """
    if not resonance_stocks:
        return {
            "total": 0,
            "by_level": {},
            "top_stock": None,
            "most_common_combo": None,
        }

    # 按级别分组
    by_level: Dict[str, int] = {}
    for rs in resonance_stocks:
        level = rs.resonance_level
        by_level[level] = by_level.get(level, 0) + 1

    # 最优先的股票
    top_stock = resonance_stocks[0]

    return {
        "total": len(resonance_stocks),
        "by_level": by_level,
        "top_stock": {
            "ticker": top_stock.ticker,
            "name": top_stock.name,
            "tactics": top_stock.matched_tactics,
            "level": top_stock.resonance_level,
        },
    }


async def deep_resonance_analysis(stock_data: Dict[str, Any],
                                   market_env: Dict[str, Any],
                                   screener=None) -> Dict[str, Any]:
    """深度共振分析: 先筛选所有战法，再分析共振

    Args:
        stock_data: 个股数据
        market_env: 市场环境
        screener: 筛选引擎实例（可选）

    Returns:
        包含匹配战法列表和共振分析结果的字典
    """
    from .screener import multi_tactic_screen

    # 1. 多战法筛选
    matches = await multi_tactic_screen(stock_data, market_env)

    # 2. 构建tactic_results格式
    tactic_results: Dict[str, List[TacticMatchResult]] = {}
    for m in matches:
        if m.tactic_name not in tactic_results:
            tactic_results[m.tactic_name] = []
        tactic_results[m.tactic_name].append(m)

    # 3. 共振分析
    engine = ResonanceEngine()
    resonance = engine.analyze(tactic_results)

    # 4. 查找本股的共振结果
    ticker = stock_data.get("ticker", "")
    stock_resonance = [r for r in resonance if r.ticker == ticker]

    return {
        "ticker": ticker,
        "name": stock_data.get("name", ""),
        "matched_tactics_count": len(matches),
        "matched_tactics": [m.tactic_name for m in matches],
        "is_resonance": len(stock_resonance) > 0,
        "resonance": stock_resonance[0] if stock_resonance else None,
        "all_matches": matches,
    }
