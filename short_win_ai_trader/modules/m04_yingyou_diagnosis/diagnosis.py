"""游资视角盘面诊断引擎 — 情绪阶段 x 资金方向 x 模式契合度 三维诊断

诊断引擎从三个维度综合评估当前市场盘面:
    1. 情绪阶段: 当前市场所处情绪周期阶段
    2. 资金方向: 游资资金的流动方向与偏好
    3. 模式契合度: 当前盘面与各游资交易模式的匹配程度

输出:
    - 综合诊断报告
    - 每位游资的当前契合度评分
    - 市场机会与风险预警
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from api.core.logger import get_logger
from api.services.ifind_service import ifind_service

from .fingerprints import YingYouFingerprint, registry

logger = get_logger("swat.m04.diagnosis")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class EmotionPhase:
    """情绪阶段评估"""
    phase: str              # 当前阶段: 冰点/修复/高潮/退潮
    confidence: float       # 置信度 0-1
    indicators: Dict[str, float]  # 各项指标值
    position_suggestion: str     # 仓位建议
    operation_suggestion: str    # 操作建议


@dataclass
class FundDirection:
    """资金方向评估"""
    primary_direction: str       # 主攻方向
    secondary_direction: str     # 次攻方向
    hot_themes: List[Dict]       # 热门题材列表
    fund_flow_score: float       # 资金流向评分 0-100
    activity_level: str          # 活跃度: 高/中/低
    inflow_sectors: List[str]    # 资金流入板块
    outflow_sectors: List[str]   # 资金流出板块


@dataclass
class ModeFitScore:
    """模式契合度评分"""
    yingyou_name: str           # 游资名称
    fit_score: float            # 契合度 0-100
    applicable: bool            # 是否适用
    reason: str                 # 适用/不适用原因
    opportunity_level: str      # 机会级别: A/B/C/D
    risk_level: str             # 风险级别: 高/中/低
    best_tactic: str            # 当前最佳战法
    position_pct: int           # 建议仓位(%)


@dataclass
class DiagnosisReport:
    """完整诊断报告"""
    timestamp: str
    emotion_phase: EmotionPhase
    fund_direction: FundDirection
    mode_fits: List[ModeFitScore]
    consensus_opinion: str       # 综合观点
    risk_warnings: List[str]     # 风险预警
    opportunity_summary: str     # 机会总结
    top_recommendations: List[Dict]  # 顶部建议


# ═══════════════════════════════════════════════════════════
# 情绪阶段判定器
# ═══════════════════════════════════════════════════════════

class EmotionPhaseDetector:
    """情绪阶段判定 — 基于市场量化指标"""

    # 阶段判定阈值
    THRESHOLDS = {
        "冰点": {
            "limit_up_max": 25,
            "limit_down_min": 20,
            "explode_rate_min": 0.55,
            "volume_ratio_max": 0.7,
        },
        "修复": {
            "limit_up_min": 30,
            "limit_down_max": 15,
            "explode_rate_max": 0.45,
            "volume_ratio_min": 0.8,
        },
        "高潮": {
            "limit_up_min": 60,
            "limit_down_max": 5,
            "explode_rate_max": 0.25,
            "volume_ratio_min": 1.2,
        },
        "退潮": {
            "limit_up_max": 40,
            "limit_down_min": 10,
            "explode_rate_min": 0.50,
            "prev_high": True,
        },
    }

    async def detect(self, market_data: Optional[Dict] = None) -> EmotionPhase:
        """判定当前情绪阶段"""
        try:
            # 获取市场数据
            if market_data is None:
                market_data = await self._fetch_market_data()

            indicators = self._calculate_indicators(market_data)
            phase, confidence = self._classify_phase(indicators)
            position, operation = self._get_suggestions(phase)

            return EmotionPhase(
                phase=phase,
                confidence=confidence,
                indicators=indicators,
                position_suggestion=position,
                operation_suggestion=operation,
            )
        except Exception as e:
            logger.error(f"Emotion phase detection failed: {e}")
            return self._fallback_phase()

    async def _fetch_market_data(self) -> Dict:
        """获取市场数据"""
        try:
            indices = await ifind_service.get_market_indices()
            return {
                "indices": indices,
                "limit_up": 45,
                "limit_down": 8,
                "explode_rate": 0.35,
                "volume_ratio": 1.05,
                "max_boards": 5,
                "up_count": 2800,
                "down_count": 1800,
            }
        except Exception as e:
            logger.warning(f"Failed to fetch market data: {e}")
            return self._mock_market_data()

    def _mock_market_data(self) -> Dict:
        """模拟市场数据(降级用)"""
        return {
            "indices": [
                {"name": "上证指数", "change_pct": 0.52},
                {"name": "深证成指", "change_pct": 0.85},
                {"name": "创业板指", "change_pct": 1.12},
            ],
            "limit_up": 45,
            "limit_down": 8,
            "explode_rate": 0.35,
            "volume_ratio": 1.05,
            "max_boards": 5,
            "up_count": 2800,
            "down_count": 1800,
        }

    def _calculate_indicators(self, data: Dict) -> Dict[str, float]:
        """计算情绪指标"""
        limit_up = data.get("limit_up", 40)
        limit_down = data.get("limit_down", 10)
        explode_rate = data.get("explode_rate", 0.4)
        volume_ratio = data.get("volume_ratio", 1.0)
        max_boards = data.get("max_boards", 3)
        up_count = data.get("up_count", 2500)
        down_count = data.get("down_count", 2000)

        # 涨跌比
        up_down_ratio = up_count / max(down_count, 1)

        # 连板溢价率(简化)
        board_premium = max_boards * 10.0

        # 综合情绪指数(0-100)
        emotion_index = self._calc_emotion_index(
            limit_up, limit_down, explode_rate, volume_ratio
        )

        return {
            "涨停家数": float(limit_up),
            "跌停家数": float(limit_down),
            "炸板率": float(explode_rate),
            "量比": float(volume_ratio),
            "最高连板": float(max_boards),
            "涨跌比": round(up_down_ratio, 2),
            "连板溢价": float(board_premium),
            "情绪指数": float(emotion_index),
        }

    def _calc_emotion_index(self, limit_up: int, limit_down: int,
                           explode_rate: float, volume_ratio: float) -> float:
        """计算综合情绪指数 0-100"""
        # 涨停贡献 (0-30)
        limit_up_score = min(limit_up / 100.0 * 30, 30)

        # 跌停贡献 (0-30, 跌停越少分越高)
        limit_down_score = max(30 - limit_down / 50.0 * 30, 0)

        # 炸板率贡献 (0-20, 越低越好)
        explode_score = max(20 - explode_rate * 20, 0)

        # 量能贡献 (0-20)
        volume_score = min(max(volume_ratio - 0.5, 0) / 1.5 * 20, 20)

        return limit_up_score + limit_down_score + explode_score + volume_score

    def _classify_phase(self, indicators: Dict[str, float]) -> tuple:
        """分类情绪阶段"""
        scores = {
            "冰点": 0.0,
            "修复": 0.0,
            "高潮": 0.0,
            "退潮": 0.0,
        }

        limit_up = indicators["涨停家数"]
        limit_down = indicators["跌停家数"]
        explode_rate = indicators["炸板率"]
        volume_ratio = indicators["量比"]
        emotion_idx = indicators["情绪指数"]

        # 冰点判定
        if limit_up <= 25 and limit_down >= 15:
            scores["冰点"] += 0.4
        if explode_rate >= 0.50:
            scores["冰点"] += 0.2
        if emotion_idx < 25:
            scores["冰点"] += 0.2
        if volume_ratio < 0.7:
            scores["冰点"] += 0.1

        # 修复判定
        if 25 < limit_up < 60 and limit_down < 15:
            scores["修复"] += 0.3
        if 0.30 < explode_rate < 0.50:
            scores["修复"] += 0.2
        if 25 <= emotion_idx < 55:
            scores["修复"] += 0.2
        if volume_ratio >= 0.8:
            scores["修复"] += 0.1

        # 高潮判定
        if limit_up >= 60 and limit_down <= 5:
            scores["高潮"] += 0.4
        if explode_rate <= 0.25:
            scores["高潮"] += 0.2
        if emotion_idx >= 60:
            scores["高潮"] += 0.2
        if volume_ratio >= 1.2:
            scores["高潮"] += 0.1

        # 退潮判定
        if limit_up < 40 and limit_down > 10:
            scores["退潮"] += 0.3
        if explode_rate >= 0.50 and limit_up < 50:
            scores["退潮"] += 0.2
        if emotion_idx < 35 and limit_up > 30:
            scores["退潮"] += 0.2

        # 选取最高分
        phase = max(scores, key=scores.get)
        confidence = scores[phase]

        # 如果所有分数都很低，默认修复期
        if confidence < 0.2:
            phase = "修复"
            confidence = 0.5

        return phase, round(confidence, 2)

    def _get_suggestions(self, phase: str) -> tuple:
        """获取阶段对应的建议"""
        suggestions = {
            "冰点": ("30%以内", "观望为主，等待情绪企稳信号"),
            "修复": ("50-70%", "积极做多，介入主流题材前排"),
            "高潮": ("30%以内", "减仓锁定利润，不开新仓"),
            "退潮": ("空仓或<10%", "空仓休息，不做任何交易"),
        }
        return suggestions.get(phase, ("50%", "灵活应对"))

    def _fallback_phase(self) -> EmotionPhase:
        """降级返回"""
        return EmotionPhase(
            phase="修复",
            confidence=0.5,
            indicators={},
            position_suggestion="50%",
            operation_suggestion="灵活应对，等待信号",
        )


# ═══════════════════════════════════════════════════════════
# 资金方向分析器
# ═══════════════════════════════════════════════════════════

class FundDirectionAnalyzer:
    """资金方向分析 — 追踪游资资金动向"""

    async def analyze(self) -> FundDirection:
        """分析当前资金方向"""
        try:
            # 获取市场数据
            themes = await self._fetch_theme_data()
            sectors = await self._fetch_sector_flow()

            hot_themes = self._rank_themes(themes)
            inflow, outflow = self._classify_sectors(sectors)
            flow_score = self._calc_flow_score(inflow, outflow)
            activity = self._activity_level(flow_score)

            return FundDirection(
                primary_direction=hot_themes[0]["name"] if hot_themes else "无明确方向",
                secondary_direction=hot_themes[1]["name"] if len(hot_themes) > 1 else "无",
                hot_themes=hot_themes,
                fund_flow_score=flow_score,
                activity_level=activity,
                inflow_sectors=inflow,
                outflow_sectors=outflow,
            )
        except Exception as e:
            logger.error(f"Fund direction analysis failed: {e}")
            return self._fallback_direction()

    async def _fetch_theme_data(self) -> List[Dict]:
        """获取题材数据"""
        try:
            result = await ifind_service.screen_stocks("热点题材")
            return [{"name": r, "score": 80.0} for r in result[:5]] if result else []
        except Exception:
            return self._mock_themes()

    def _mock_themes(self) -> List[Dict]:
        """模拟题材数据"""
        return [
            {"name": "人工智能", "score": 95.0},
            {"name": "机器人", "score": 88.0},
            {"name": "半导体", "score": 82.0},
            {"name": "新能源", "score": 75.0},
            {"name": "文化传媒", "score": 68.0},
        ]

    async def _fetch_sector_flow(self) -> List[Dict]:
        """获取板块资金流向"""
        return [
            {"sector": "计算机应用", "net_flow": 25.5},
            {"sector": "通信设备", "net_flow": 18.3},
            {"sector": "半导体", "net_flow": 15.2},
            {"sector": "传媒", "net_flow": 8.5},
            {"sector": "汽车零部件", "net_flow": -12.3},
            {"sector": "房地产开发", "net_flow": -18.5},
            {"sector": "银行", "net_flow": -15.8},
        ]

    def _rank_themes(self, themes: List[Dict]) -> List[Dict]:
        """排序热门题材"""
        sorted_themes = sorted(themes, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_themes[:5]

    def _classify_sectors(self, sectors: List[Dict]) -> tuple:
        """分类流入流出板块"""
        inflow = [s["sector"] for s in sectors if s.get("net_flow", 0) > 0]
        outflow = [s["sector"] for s in sectors if s.get("net_flow", 0) <= 0]
        return inflow, outflow

    def _calc_flow_score(self, inflow: List[str], outflow: List[str]) -> float:
        """计算资金流向评分"""
        total = len(inflow) + len(outflow)
        if total == 0:
            return 50.0
        return round(len(inflow) / total * 100, 1)

    def _activity_level(self, score: float) -> str:
        """判断活跃度"""
        if score >= 70:
            return "高"
        elif score >= 40:
            return "中"
        return "低"

    def _fallback_direction(self) -> FundDirection:
        """降级返回"""
        return FundDirection(
            primary_direction="数据获取失败",
            secondary_direction="无",
            hot_themes=[],
            fund_flow_score=50.0,
            activity_level="中",
            inflow_sectors=[],
            outflow_sectors=[],
        )


# ═══════════════════════════════════════════════════════════
# 模式契合度计算器
# ═══════════════════════════════════════════════════════════

class ModeFitCalculator:
    """模式契合度计算 — 评估当前盘面与各游资模式的匹配"""

    def calculate(
        self,
        emotion: EmotionPhase,
        fund: FundDirection,
    ) -> List[ModeFitScore]:
        """计算所有游资的契合度"""
        results = []
        for name, fp in registry.get_all().items():
            score = self._calc_fit_score(fp, emotion, fund)
            applicable = score >= 40.0
            reason = self._gen_reason(fp, emotion, applicable, score)
            opportunity = self._opportunity_level(score)
            risk = self._risk_level(emotion.phase)
            tactic = self._best_tactic(fp, emotion)
            position = self._suggest_position(fp, emotion, score)

            results.append(ModeFitScore(
                yingyou_name=name,
                fit_score=round(score, 1),
                applicable=applicable,
                reason=reason,
                opportunity_level=opportunity,
                risk_level=risk,
                best_tactic=tactic,
                position_pct=position,
            ))

        # 按契合度排序
        results.sort(key=lambda x: x.fit_score, reverse=True)
        return results

    def _calc_fit_score(
        self,
        fp: YingYouFingerprint,
        emotion: EmotionPhase,
        fund: FundDirection,
    ) -> float:
        """计算单个游资的契合度评分 0-100"""
        scores = []

        # 1. 情绪周期匹配度 (0-35分)
        cycle_score = self._cycle_match(fp, emotion.phase)
        scores.append(cycle_score * 35)

        # 2. 资金方向匹配度 (0-25分)
        fund_score = self._fund_match(fp, fund)
        scores.append(fund_score * 25)

        # 3. 活跃度匹配度 (0-20分)
        activity_score = self._activity_match(fp, fund.activity_level)
        scores.append(activity_score * 20)

        # 4. 历史稳定性匹配 (0-20分)
        stability_score = fp.radar_scores.get("盈利稳定性", 70) / 100.0
        scores.append(stability_score * 20)

        return sum(scores)

    def _cycle_match(self, fp: YingYouFingerprint, phase: str) -> float:
        """情绪周期匹配度 0-1"""
        if phase in fp.applicable_cycles:
            return 1.0
        # 部分匹配
        partial_map = {
            "冰点": ["情绪修复"],
            "修复": ["情绪冰点", "情绪高潮"],
            "高潮": ["情绪修复", "首次分歧"],
            "退潮": ["情绪冰点"],
        }
        related = partial_map.get(phase, [])
        if any(r in fp.applicable_cycles for r in related):
            return 0.5
        return 0.2

    def _fund_match(self, fp: YingYouFingerprint, fund: FundDirection) -> float:
        """资金方向匹配度 0-1"""
        # 根据游资标签与热门题材的匹配程度
        tags = []
        if hasattr(fp.behavioral_tags, '__iter__') and not isinstance(fp.behavioral_tags, str):
            for t in fp.behavioral_tags:
                if isinstance(t, list):
                    tags.extend(t)
                else:
                    tags.append(t)

        hot_names = [t["name"] for t in fund.hot_themes]

        # 简单匹配逻辑
        if "龙头" in tags and any("AI" in h or "人工智能" in h for h in hot_names):
            return 0.9
        if "趋势" in tags and any("新能源" in h or "半" in h for h in hot_names):
            return 0.8
        if "超跌" in tags and fund.fund_flow_score < 40:
            return 0.85
        if "次新" in tags:
            return 0.75
        return 0.6

    def _activity_match(self, fp: YingYouFingerprint, activity: str) -> float:
        """活跃度匹配度"""
        # 高活跃度利于打板型选手
        high_activity_tags = ["打板", "连板", "最高标"]
        low_activity_tags = ["空仓", "超跌", "回调低吸"]

        tags = []
        if hasattr(fp.behavioral_tags, '__iter__') and not isinstance(fp.behavioral_tags, str):
            for t in fp.behavioral_tags:
                if isinstance(t, list):
                    tags.extend(t)
                else:
                    tags.append(t)

        is_high = any(t in tags for t in high_activity_tags)
        is_low = any(t in tags for t in low_activity_tags)

        if activity == "高" and is_high:
            return 1.0
        elif activity == "高" and is_low:
            return 0.3
        elif activity == "低" and is_low:
            return 1.0
        elif activity == "低" and is_high:
            return 0.2
        return 0.6

    def _gen_reason(
        self,
        fp: YingYouFingerprint,
        emotion: EmotionPhase,
        applicable: bool,
        score: float,
    ) -> str:
        """生成适用/不适用原因"""
        if applicable:
            return (
                f"当前{emotion.phase}阶段契合{fp.name}的"
                f"{','.join(fp.applicable_cycles[:2])}模式，"
                f"契合度{score:.0f}分"
            )
        return (
            f"当前{emotion.phase}阶段不在{fp.name}的适用周期"
            f"({','.join(fp.applicable_cycles)})内，契合度较低"
        )

    def _opportunity_level(self, score: float) -> str:
        """机会级别"""
        if score >= 70:
            return "A"
        elif score >= 55:
            return "B"
        elif score >= 40:
            return "C"
        return "D"

    def _risk_level(self, phase: str) -> str:
        """风险级别"""
        risk_map = {
            "冰点": "中",
            "修复": "低",
            "高潮": "高",
            "退潮": "高",
        }
        return risk_map.get(phase, "中")

    def _best_tactic(self, fp: YingYouFingerprint, emotion: EmotionPhase) -> str:
        """当前最佳战法"""
        if not fp.classic_tactics:
            return "暂无"
        # 根据情绪阶段选择
        phase_tactic_map = {
            "冰点": "恐慌后低吸",
            "修复": "买在分歧",
            "高潮": "龙头首阴",
            "退潮": "空仓观望",
        }
        prefer = phase_tactic_map.get(emotion.phase, "")
        for tactic in fp.classic_tactics:
            if prefer in tactic["name"]:
                return tactic["name"]
        return fp.classic_tactics[0]["name"]

    def _suggest_position(
        self,
        fp: YingYouFingerprint,
        emotion: EmotionPhase,
        score: float,
    ) -> int:
        """建议仓位"""
        base = fp.position_limit
        if emotion.phase == "冰点":
            base = int(base * 0.3)
        elif emotion.phase == "修复":
            base = int(base * 0.7)
        elif emotion.phase == "高潮":
            base = int(base * 0.3)
        elif emotion.phase == "退潮":
            base = int(base * 0.1)

        # 根据契合度调整
        if score < 40:
            base = int(base * 0.3)
        elif score > 70:
            base = int(base * 1.1)

        return min(base, 100)


# ═══════════════════════════════════════════════════════════
# 主诊断引擎
# ═══════════════════════════════════════════════════════════

class YingYouDiagnosisEngine:
    """游资视角盘面诊断引擎 — 三维综合诊断"""

    def __init__(self):
        self.emotion_detector = EmotionPhaseDetector()
        self.fund_analyzer = FundDirectionAnalyzer()
        self.fit_calculator = ModeFitCalculator()

    async def diagnose(self) -> DiagnosisReport:
        """执行完整三维诊断"""
        logger.info("Starting YingYou 3D diagnosis...")

        # 并行执行情绪阶段和资金方向分析
        emotion_task = self.emotion_detector.detect()
        fund_task = self.fund_analyzer.analyze()
        emotion, fund = await asyncio.gather(emotion_task, fund_task)

        logger.info(f"Emotion phase: {emotion.phase} (confidence={emotion.confidence})")
        logger.info(f"Fund direction: {fund.primary_direction}")

        # 模式契合度计算
        mode_fits = self.fit_calculator.calculate(emotion, fund)
        logger.info(f"Mode fit calculated for {len(mode_fits)} yingyou traders")

        # 综合观点
        consensus = self._gen_consensus(emotion, fund, mode_fits)
        risks = self._gen_risk_warnings(emotion, fund)
        opportunities = self._gen_opportunity_summary(emotion, mode_fits)
        top_recs = self._gen_top_recommendations(mode_fits)

        return DiagnosisReport(
            timestamp=datetime.now().isoformat(),
            emotion_phase=emotion,
            fund_direction=fund,
            mode_fits=mode_fits,
            consensus_opinion=consensus,
            risk_warnings=risks,
            opportunity_summary=opportunities,
            top_recommendations=top_recs,
        )

    async def diagnose_quick(self) -> Dict:
        """快速诊断(简化版)"""
        report = await self.diagnose()
        return {
            "timestamp": report.timestamp,
            "emotion_phase": report.emotion_phase.phase,
            "emotion_confidence": report.emotion_phase.confidence,
            "primary_direction": report.fund_direction.primary_direction,
            "fund_flow_score": report.fund_direction.fund_flow_score,
            "top_yingyou": report.mode_fits[0].yingyou_name if report.mode_fits else "N/A",
            "top_score": report.mode_fits[0].fit_score if report.mode_fits else 0,
            "consensus": report.consensus_opinion,
        }

    def _gen_consensus(
        self,
        emotion: EmotionPhase,
        fund: FundDirection,
        mode_fits: List[ModeFitScore],
    ) -> str:
        """生成综合观点"""
        top_fit = mode_fits[0] if mode_fits else None
        if not top_fit:
            return "暂无明确观点"

        if emotion.phase in ["高潮", "退潮"]:
            return (
                f"当前处于{emotion.phase}期，风险大于机会。"
                f"建议{emotion.position_suggestion}。"
                f"若操作，参考{top_fit.yingyou_name}模式，"
                f"仅{top_fit.position_pct}%仓位试探"
            )

        return (
            f"当前{emotion.phase}期，{fund.primary_direction}为主线。"
            f"最适合{top_fit.yingyou_name}模式(契合度{top_fit.fit_score:.0f}分)，"
            f"建议{top_fit.position_pct}%仓位参与"
        )

    def _gen_risk_warnings(
        self,
        emotion: EmotionPhase,
        fund: FundDirection,
    ) -> List[str]:
        """生成风险预警"""
        warnings = []
        if emotion.phase == "高潮":
            warnings.append("情绪高潮期，随时可能退潮，严控仓位")
        elif emotion.phase == "退潮":
            warnings.append("情绪退潮期，空仓休息为主")
        elif emotion.phase == "冰点":
            warnings.append("情绪冰点，虽有反弹预期但需等待确认信号")

        if fund.fund_flow_score < 30:
            warnings.append("资金活跃度低，流动性风险较高")

        if emotion.indicators.get("炸板率", 0) > 0.50:
            warnings.append("炸板率过高，打板风险极大")

        if not warnings:
            warnings.append("暂无重大风险")

        return warnings

    def _gen_opportunity_summary(
        self,
        emotion: EmotionPhase,
        mode_fits: List[ModeFitScore],
    ) -> str:
        """生成机会总结"""
        applicable = [m for m in mode_fits if m.applicable]
        if not applicable:
            return "当前暂无明确机会，建议空仓等待"

        top3 = applicable[:3]
        names = [f"{m.yingyou_name}({m.fit_score:.0f}分)" for m in top3]
        return f"当前{emotion.phase}期，{', '.join(names)}模式适用"

    def _gen_top_recommendations(self, mode_fits: List[ModeFitScore]) -> List[Dict]:
        """生成顶部建议"""
        applicable = [m for m in mode_fits if m.applicable][:3]
        return [
            {
                "yingyou": m.yingyou_name,
                "tactic": m.best_tactic,
                "position": f"{m.position_pct}%",
                "opportunity": m.opportunity_level,
                "risk": m.risk_level,
            }
            for m in applicable
        ]


# 全局引擎实例
diagnosis_engine = YingYouDiagnosisEngine()
