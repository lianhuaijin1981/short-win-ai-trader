"""评分决策整合 — 将m06评分引擎整合到交易笔记模块

提供:
1. 标的评分决策（复用m06评分引擎）
2. 观察标的评分更新
3. 交易计划中的评分建议
4. 评分历史记录
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from ...core.logger import get_logger
from ..m06_scoring_decision.scoring_engine import ScoringEngine
from ..m06_scoring_decision.dimension_scorers import DIMENSION_WEIGHTS
from .models import (
    ScoringRequest,
    ScoringResult,
    WatchStock,
)

logger = get_logger("swat.m08.scoring_integration")


class ScoringIntegration:
    """评分决策整合器
    
    将m06评分引擎的功能整合到交易笔记模块中，
    为观察标的和交易计划提供评分决策支持。
    """
    
    def __init__(self):
        """初始化评分整合器"""
        self.scoring_engine = ScoringEngine()
        
        # 评分历史缓存
        self._score_history: Dict[str, List[Dict]] = {}
        
        logger.info("评分决策整合器初始化完成")
    
    # ==================== 标的评分 ====================
    
    async def score_stock(
        self,
        ticker: str,
        stock_name: str,
        current_price: float,
        theme_data: Optional[Dict] = None,
        fund_data: Optional[Dict] = None,
        emotion_data: Optional[Dict] = None,
        chip_data: Optional[Dict] = None,
        technical_data: Optional[Dict] = None,
        dragon_data: Optional[Dict] = None,
        news_data: Optional[Dict] = None,
        current_position: float = 0.0,
    ) -> ScoringResult:
        """对标的进行评分
        
        Args:
            ticker: 股票代码
            stock_name: 股票名称
            current_price: 当前价格
            theme_data: 题材数据
            fund_data: 资金数据
            emotion_data: 情绪数据
            chip_data: 筹码数据
            technical_data: 技术数据
            dragon_data: 龙头数据
            news_data: 资讯数据
            current_position: 当前仓位
            
        Returns:
            ScoringResult: 评分结果
        """
        try:
            # 调用m06评分引擎
            report = await self.scoring_engine.evaluate_stock(
                ticker=ticker,
                stock_name=stock_name,
                current_price=current_price,
                theme_data=theme_data,
                fund_data=fund_data,
                emotion_data=emotion_data,
                chip_data=chip_data,
                technical_data=technical_data,
                dragon_data=dragon_data,
                news_data=news_data,
                current_position=current_position,
            )
            
            # 转换为ScoringResult
            result = ScoringResult(
                ticker=ticker,
                stock_name=stock_name,
                current_price=current_price,
                total_score=report.total_score,
                rating=report.rating.value,
                risk_level=report.risk_level.value,
                dimension_scores=[
                    {
                        "dimension": ds.dimension,
                        "score": ds.score,
                        "weight": ds.weight,
                        "weighted_score": ds.weighted_score,
                    }
                    for ds in report.dimension_scores
                ],
                risk_reward_ratio=report.risk_reward.ratio if report.risk_reward else 0.0,
                entry_price=report.risk_reward.entry_price if report.risk_reward else 0.0,
                stop_loss=report.risk_reward.stop_loss_price if report.risk_reward else 0.0,
                take_profit=report.risk_reward.take_profit_price if report.risk_reward else 0.0,
                action=report.advice.action.value if report.advice else "",
                position_pct=report.advice.position_pct if report.advice else 0.0,
                entry_type=report.advice.entry_type if report.advice else "",
                entry_zone=report.advice.entry_zone if report.advice else "",
                stop_loss_strategy=report.advice.stop_loss if report.advice else "",
                take_profit_strategy=report.advice.take_profit if report.advice else "",
                risk_warnings=report.advice.risk_warnings if report.advice else [],
                emotion_check=report.advice.emotion_check if report.advice else "",
                summary=report.summary_text,
            )
            
            # 记录评分历史
            self._record_score(ticker, result)
            
            logger.info(f"标的评分完成: {stock_name}({ticker}) = {report.total_score}分")
            return result
            
        except Exception as e:
            logger.error(f"标的评分失败: {e}")
            return ScoringResult(
                ticker=ticker,
                stock_name=stock_name,
                current_price=current_price,
                summary=f"评分失败: {str(e)}",
            )
    
    # ==================== 观察标的评分 ====================
    
    async def score_watch_stocks(
        self,
        watch_stocks: List[WatchStock],
        market_data: Optional[Dict] = None,
    ) -> List[WatchStock]:
        """批量评分观察标的
        
        Args:
            watch_stocks: 观察标的列表
            market_data: 市场数据（用于情绪周期等）
            
        Returns:
            更新评分后的观察标的列表
        """
        updated_stocks = []
        
        for stock in watch_stocks:
            if not stock.ticker:
                updated_stocks.append(stock)
                continue
            
            try:
                # 构建评分请求数据
                emotion_data = market_data if market_data else {}
                
                result = await self.score_stock(
                    ticker=stock.ticker,
                    stock_name=stock.stock_name,
                    current_price=stock.key_price if stock.key_price > 0 else 0.0,
                    emotion_data=emotion_data,
                )
                
                # 更新评分信息
                stock.score = result.total_score
                stock.rating = result.rating
                stock.risk_level = result.risk_level
                stock.advice = result.action
                
                updated_stocks.append(stock)
                
            except Exception as e:
                logger.warning(f"观察标的评分失败 {stock.stock_name}: {e}")
                updated_stocks.append(stock)
        
        # 按评分降序排列
        updated_stocks.sort(key=lambda s: s.score, reverse=True)
        
        # 更新优先级
        for i, stock in enumerate(updated_stocks):
            stock.priority = i + 1
        
        return updated_stocks
    
    # ==================== 评分历史 ====================
    
    def get_score_history(
        self,
        ticker: str,
        days: int = 30,
    ) -> List[Dict]:
        """获取标的评分历史
        
        Args:
            ticker: 股票代码
            days: 历史天数
            
        Returns:
            评分历史列表
        """
        history = self._score_history.get(ticker, [])
        
        # 过滤日期
        if history:
            cutoff = date.today()
            from datetime import timedelta
            cutoff = cutoff - timedelta(days=days)
            history = [h for h in history if h.get("date", "") >= cutoff.isoformat()]
        
        return history
    
    def get_all_score_history(self, limit: int = 50) -> Dict[str, List[Dict]]:
        """获取所有标的的评分历史
        
        Args:
            limit: 每个标的返回的最大记录数
            
        Returns:
            所有标的的评分历史
        """
        result = {}
        for ticker, history in self._score_history.items():
            result[ticker] = history[-limit:] if history else []
        return result
    
    # ==================== 评分统计 ====================
    
    def get_score_statistics(self) -> Dict:
        """获取评分统计信息
        
        Returns:
            评分统计
        """
        total_scores = 0
        total_stocks = len(self._score_history)
        
        for ticker, history in self._score_history.items():
            total_scores += len(history)
        
        # 最近评分
        recent_scores = []
        for ticker, history in self._score_history.items():
            if history:
                recent_scores.append(history[-1])
        
        # 按评分排序
        recent_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return {
            "total_stocks": total_stocks,
            "total_scores": total_scores,
            "recent_top_scores": recent_scores[:10],
            "avg_score": (
                sum(s.get("score", 0) for s in recent_scores) / len(recent_scores)
                if recent_scores else 0
            ),
        }
    
    # ==================== 交易计划评分建议 ====================
    
    def generate_plan_scoring_advice(
        self,
        watch_stocks: List[WatchStock],
        market_outlook: str = "震荡中性",
    ) -> Dict:
        """基于评分生成交易计划建议
        
        Args:
            watch_stocks: 观察标的列表（已评分）
            market_outlook: 大盘判断
            
        Returns:
            交易计划建议
        """
        advice = {
            "recommended_stocks": [],
            "caution_stocks": [],
            "avoid_stocks": [],
            "position_advice": "",
            "tactic_advice": "",
            "risk_warnings": [],
        }
        
        # 分类标的
        for stock in watch_stocks:
            if stock.score >= 75:
                advice["recommended_stocks"].append({
                    "ticker": stock.ticker,
                    "name": stock.stock_name,
                    "score": stock.score,
                    "rating": stock.rating,
                    "advice": stock.advice,
                })
            elif stock.score >= 55:
                advice["caution_stocks"].append({
                    "ticker": stock.ticker,
                    "name": stock.stock_name,
                    "score": stock.score,
                    "rating": stock.rating,
                    "advice": stock.advice,
                })
            else:
                advice["avoid_stocks"].append({
                    "ticker": stock.ticker,
                    "name": stock.stock_name,
                    "score": stock.score,
                    "rating": stock.rating,
                    "reason": "评分过低，建议规避",
                })
        
        # 仓位建议
        high_score_count = len(advice["recommended_stocks"])
        if high_score_count >= 3:
            advice["position_advice"] = "优质标的较多，可适当提高仓位至50-60%"
        elif high_score_count >= 1:
            advice["position_advice"] = "有优质标的，建议仓位30-50%"
        else:
            advice["position_advice"] = "缺乏优质标的，建议轻仓或空仓观望"
        
        # 战法建议
        if market_outlook in ("强势看多", "震荡偏多"):
            advice["tactic_advice"] = "市场偏强，可积极打板/接力"
        elif market_outlook == "震荡中性":
            advice["tactic_advice"] = "震荡市，建议低吸为主，控制仓位"
        else:
            advice["tactic_advice"] = "市场偏弱，建议空仓或极小仓位试错"
        
        # 风险提示
        if len(advice["avoid_stocks"]) > len(advice["recommended_stocks"]):
            advice["risk_warnings"].append("低分标的较多，整体风险偏高")
        
        low_avg = (
            sum(s["score"] for s in advice.get("caution_stocks", [])) /
            len(advice.get("caution_stocks", [1]))
            if advice.get("caution_stocks") else 0
        )
        if low_avg < 60:
            advice["risk_warnings"].append("观察标的整体评分偏低，需谨慎")
        
        return advice
    
    # ==================== 内部方法 ====================
    
    def _record_score(self, ticker: str, result: ScoringResult) -> None:
        """记录评分历史"""
        if ticker not in self._score_history:
            self._score_history[ticker] = []
        
        self._score_history[ticker].append({
            "date": date.today().isoformat(),
            "time": datetime.now().strftime("%H:%M:%S"),
            "score": result.total_score,
            "rating": result.rating,
            "risk_level": result.risk_level,
            "price": result.current_price,
            "action": result.action,
        })
        
        # 限制历史记录数量
        if len(self._score_history[ticker]) > 100:
            self._score_history[ticker] = self._score_history[ticker][-100:]