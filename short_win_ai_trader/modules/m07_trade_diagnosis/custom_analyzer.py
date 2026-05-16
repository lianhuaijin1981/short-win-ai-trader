"""自定义标的全维度研判 — 整合前6模块数据"""

from typing import Dict, List, Optional

from ...core.logger import get_logger
from ...data_platform.data_models import CustomStockAnalysis, TradePlan

logger = get_logger("swat.custom_analyzer")


class CustomAnalyzer:
    """自定义标的分析器
    
    用户提交任意个股代码，系统整合前6大模块:
    - 资讯模块: 催化/利空
    - 情绪模块: 情绪阶段/题材周期
    - 看盘模块: 盘面定位/梯队联动
    - 游资模块: 模式匹配/认可度
    - 战法模块: 战法贴合/形态验证
    - 评分模块: 综合得分/RR/仓位/交易计划
    """

    def analyze(
        self,
        ticker: str,
        stock_name: str,
        modules_data: Dict,
        user_style: Optional[str] = None,
    ) -> CustomStockAnalysis:
        """自定义标的全维度研判"""
        logger.info(f"全维度研判: {ticker} {stock_name}")

        # 从modules_data提取各模块输出
        emotion = modules_data.get("emotion", {})
        watch = modules_data.get("watch", {})
        yingyou = modules_data.get("yingyou", {})
        tactics = modules_data.get("tactics", {})
        scoring = modules_data.get("scoring", {})

        # 综合评分
        total_score = scoring.get("total_score", 0)
        rating = scoring.get("rating", "未评估")

        # 成功逻辑
        success_logic = []
        if scoring.get("dimension_scores"):
            for ds in scoring["dimension_scores"]:
                if ds.get("score", 0) >= 70:
                    success_logic.append(f"【{ds['dimension']}】得分{ds['score']:.0f}，表现优秀")

        # 资讯催化
        if modules_data.get("news"):
            news_level = modules_data["news"].get("level", "")
            if news_level in ["S", "A"]:
                success_logic.append(f"【资讯】存在{news_level}级催化资讯，具备上涨催化剂")

        # 游资匹配
        if yingyou:
            top_match = yingyou.get("top_match")
            if top_match and top_match.get("score", 0) >= 80:
                success_logic.append(
                    f"【游资】匹配{top_match['name']}模式({top_match['score']:.0f}分)，"
                    f"多游资认可"
                )

        # 战法共振
        if tactics:
            matched = tactics.get("matched_tactics", [])
            if len(matched) >= 2:
                success_logic.append(f"【战法】{len(matched)}套战法共振({', '.join(matched)})，形态强势")

        # 风险败点
        risk_points = []
        if scoring.get("dimension_scores"):
            for ds in scoring["dimension_scores"]:
                if ds.get("score", 0) < 50:
                    risk_points.append(f"【{ds['dimension']}】得分仅{ds['score']:.0f}，存在明显短板")

        # 情绪风险
        emotion_cycle = emotion.get("current_cycle", "")
        if emotion_cycle in ["退潮期", "分歧期"]:
            risk_points.append(f"【情绪】当前处于{emotion_cycle}，大势不利，容错率低")

        # 位置风险
        if scoring.get("is_high_position"):
            risk_points.append("【位置】处于高位，追高风险大，一旦回调空间有限")

        # 筹码风险
        if scoring.get("chip_risk"):
            risk_points.append("【筹码】上方套牢盘重或底部筹码松动，上涨承压")

        # 交易计划
        trade_plan = modules_data.get("trade_plan")

        # 风格适配建议
        if user_style:
            if user_style in ["龙头接力型"] and "龙头" in str(success_logic):
                style_advice = "符合您的龙头接力风格，可正常参与"
            elif user_style in ["分歧低吸型"] and any("低吸" in s for s in success_logic):
                style_advice = "符合您的低吸风格，可在分歧时介入"
            else:
                style_advice = f"与您{user_style}风格不完全匹配，建议轻仓试错或观望"
        else:
            style_advice = "建议根据个人风格判断是否参与"

        # 最终建议
        if total_score >= 80:
            style_advice = "高评分标的，" + style_advice
        elif total_score < 60:
            style_advice = "低评分标的，建议直接放弃 — " + "; ".join(risk_points[:2])

        return CustomStockAnalysis(
            ticker=ticker,
            name=stock_name,
            comprehensive_score=total_score,
            rating=rating,
            emotion_cycle=emotion_cycle,
            theme_position=emotion.get("theme_position", ""),
            anchor_position=watch.get("anchor_position", ""),
            yingyou_matches=[yingyou] if yingyou else [],
            tactic_matches=[{"tactics": tactics.get("matched_tactics", [])}] if tactics else [],
            success_logic=success_logic,
            risk_points=risk_points,
            trade_plan=trade_plan,
            style_advice=style_advice,
        )
