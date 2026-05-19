"""交易笔记路由 — 当日复盘、次日计划、语音输入、评分决策

提供:
- /journal/notes — 交易笔记CRUD
- /journal/review — 当日复盘
- /journal/plan — 次日计划
- /journal/voice — 语音输入
- /journal/scoring — 标的评分
- /journal/performance — 绩效统计
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from api.core.config import APIConfig
from api.core.logger import get_logger
from api.models.responses import ApiResponse

logger = get_logger("swat.router.journal")
config = APIConfig()

router = APIRouter(prefix="/journal", tags=["TradeJournal"])

# 延迟初始化（避免循环导入）
_journal_manager = None
_voice_processor = None
_scoring_integration = None


def _get_journal_manager():
    """获取笔记管理器实例"""
    global _journal_manager
    if _journal_manager is None:
        from short_win_ai_trader.modules.m08_trade_journal import JournalManager
        _journal_manager = JournalManager()
    return _journal_manager


def _get_voice_processor():
    """获取语音处理器实例"""
    global _voice_processor
    if _voice_processor is None:
        from short_win_ai_trader.modules.m08_trade_journal.voice_processor import VoiceProcessor
        _voice_processor = VoiceProcessor()
    return _voice_processor


def _get_scoring_integration():
    """获取评分整合器实例"""
    global _scoring_integration
    if _scoring_integration is None:
        from short_win_ai_trader.modules.m08_trade_journal.scoring_integration import ScoringIntegration
        _scoring_integration = ScoringIntegration()
    return _scoring_integration


# ── 请求模型 ────────────────────────────────────────────


class PositionRequest(BaseModel):
    """持仓记录请求"""
    ticker: str = Field("", description="股票代码")
    stock_name: str = Field("", description="股票名称")
    sector: str = Field("", description="所属板块")
    entry_price: float = Field(0.0, description="入场价格")
    entry_time: str = Field("", description="入场时间")
    entry_reason: str = Field("", description="入场逻辑")
    entry_method: str = Field("", description="入场方式")
    exit_price: float = Field(0.0, description="出场价格")
    exit_time: str = Field("", description="出场时间")
    exit_reason: str = Field("", description="出场原因")
    position_size: float = Field(0.0, description="仓位比例%")
    profit_loss_pct: float = Field(0.0, description="盈亏幅度%")
    profit_loss_amount: float = Field(0.0, description="盈亏金额")
    result: str = Field("未结", description="交易结果")
    trade_logic: str = Field("", description="交易逻辑")
    tactic_used: str = Field("", description="使用战法")
    has_error: bool = Field(False, description="是否有失误")
    error_type: str = Field("", description="失误类型")
    error_summary: str = Field("", description="失误归因")
    notes: str = Field("", description="备注")


class ReviewRequest(BaseModel):
    """复盘请求"""
    positions: List[PositionRequest] = Field(default_factory=list, description="持仓记录")
    mindset_level: str = Field("一般", description="心态评级")
    mindset_summary: str = Field("", description="心态总结")
    rhythm_summary: str = Field("", description="节奏总结")
    discipline_summary: str = Field("", description="纪律总结")
    mindset_issues: List[str] = Field(default_factory=list, description="心态问题")
    rhythm_issues: List[str] = Field(default_factory=list, description="节奏问题")
    discipline_issues: List[str] = Field(default_factory=list, description="纪律问题")
    lessons_learned: List[str] = Field(default_factory=list, description="经验教训")
    improvements: List[str] = Field(default_factory=list, description="改进方向")
    overall_summary: str = Field("", description="整体总结")
    self_score: float = Field(0.0, ge=0, le=100, description="自我评分")


class WatchStockRequest(BaseModel):
    """观察标的请求"""
    ticker: str = Field("", description="股票代码")
    stock_name: str = Field("", description="股票名称")
    sector: str = Field("", description="所属板块")
    watch_reason: str = Field("", description="观察原因")
    expected_action: str = Field("", description="预期操作")
    key_price: float = Field(0.0, description="关键价位")
    trigger_condition: str = Field("", description="触发条件")
    priority: int = Field(0, ge=0, le=5, description="优先级")


class PlanRequest(BaseModel):
    """次日计划请求"""
    market_outlook: str = Field("震荡中性", description="大盘判断")
    market_reasoning: str = Field("", description="大盘判断思路")
    key_levels: str = Field("", description="关键价位")
    watch_stocks: List[WatchStockRequest] = Field(default_factory=list, description="观察标的")
    total_position_limit: float = Field(50.0, ge=0, le=100, description="总仓位上限%")
    single_stock_limit: float = Field(20.0, ge=0, le=50, description="单票仓位上限%")
    max_trades: int = Field(3, ge=1, le=10, description="最大交易笔数")
    position_plan: str = Field("", description="仓位管控计划")
    stop_loss_rule: str = Field("", description="止损纪律")
    take_profit_rule: str = Field("", description="止盈纪律")
    max_daily_loss: float = Field(3.0, ge=0, le=10, description="单日最大亏损%")
    risk_rules: List[str] = Field(default_factory=list, description="风控规则")
    risk_directions: List[str] = Field(default_factory=list, description="风险避雷方向")
    avoid_sectors: List[str] = Field(default_factory=list, description="规避板块")
    avoid_stocks: List[str] = Field(default_factory=list, description="规避个股")
    preferred_sectors: List[str] = Field(default_factory=list, description="重点关注板块")
    preferred_tactics: List[str] = Field(default_factory=list, description="首选战法")
    notes: str = Field("", description="备注")


class TradeNoteRequest(BaseModel):
    """交易笔记请求"""
    review: Optional[ReviewRequest] = Field(None, description="复盘数据")
    plan: Optional[PlanRequest] = Field(None, description="计划数据")
    source: str = Field("manual", description="来源")
    tags: List[str] = Field(default_factory=list, description="标签")
    note_date: Optional[str] = Field(None, description="笔记日期")


class ScoringRequest(BaseModel):
    """评分请求"""
    ticker: str = Field(..., description="股票代码")
    stock_name: str = Field("", description="股票名称")
    current_price: float = Field(0.0, description="当前价格")
    theme_data: Optional[Dict] = Field(None, description="题材数据")
    fund_data: Optional[Dict] = Field(None, description="资金数据")
    emotion_data: Optional[Dict] = Field(None, description="情绪数据")
    chip_data: Optional[Dict] = Field(None, description="筹码数据")
    technical_data: Optional[Dict] = Field(None, description="技术数据")
    dragon_data: Optional[Dict] = Field(None, description="龙头数据")
    news_data: Optional[Dict] = Field(None, description="资讯数据")
    current_position: float = Field(0.0, ge=0, le=1, description="当前仓位")


class VoiceTextRequest(BaseModel):
    """语音文本请求（用于直接提交文本模拟语音）"""
    text: str = Field(..., min_length=1, description="输入文本")
    note_date: Optional[str] = Field(None, description="日期")


# ── 路由: 笔记CRUD ──────────────────────────────────────


@router.post("/notes", response_model=Dict)
async def create_note(request: TradeNoteRequest):
    """创建交易笔记
    
    创建包含当日复盘和/或次日计划的交易笔记。
    """
    logger.info(f"POST /journal/notes source={request.source}")
    
    try:
        manager = _get_journal_manager()
        
        # 转换复盘数据
        review_data = None
        if request.review:
            review_data = {
                "positions": [p.model_dump() for p in request.review.positions],
                "mindset_level": request.review.mindset_level,
                "mindset_summary": request.review.mindset_summary,
                "rhythm_summary": request.review.rhythm_summary,
                "discipline_summary": request.review.discipline_summary,
                "mindset_issues": request.review.mindset_issues,
                "rhythm_issues": request.review.rhythm_issues,
                "discipline_issues": request.review.discipline_issues,
                "lessons_learned": request.review.lessons_learned,
                "improvements": request.review.improvements,
                "overall_summary": request.review.overall_summary,
                "self_score": request.review.self_score,
            }
        
        # 转换计划数据
        plan_data = None
        if request.plan:
            plan_data = {
                "market_outlook": request.plan.market_outlook,
                "market_reasoning": request.plan.market_reasoning,
                "key_levels": request.plan.key_levels,
                "watch_stocks": [ws.model_dump() for ws in request.plan.watch_stocks],
                "total_position_limit": request.plan.total_position_limit,
                "single_stock_limit": request.plan.single_stock_limit,
                "max_trades": request.plan.max_trades,
                "position_plan": request.plan.position_plan,
                "stop_loss_rule": request.plan.stop_loss_rule,
                "take_profit_rule": request.plan.take_profit_rule,
                "max_daily_loss": request.plan.max_daily_loss,
                "risk_rules": request.plan.risk_rules,
                "risk_directions": request.plan.risk_directions,
                "avoid_sectors": request.plan.avoid_sectors,
                "avoid_stocks": request.plan.avoid_stocks,
                "preferred_sectors": request.plan.preferred_sectors,
                "preferred_tactics": request.plan.preferred_tactics,
                "notes": request.plan.notes,
            }
        
        note = manager.create_note(
            review_data=review_data,
            plan_data=plan_data,
            source=request.source,
            tags=request.tags,
            note_date=request.note_date,
        )
        
        return {
            "code": 200,
            "message": "交易笔记创建成功",
            "data": {
                "note_id": note.id,
                "date": note.date.isoformat() if note.date else None,
                "source": note.source,
                "tags": note.tags,
                "has_review": note.review is not None,
                "has_plan": note.next_day_plan is not None,
                "created_at": note.created_at.isoformat() if note.created_at else None,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"创建交易笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建交易笔记失败: {str(e)}")


@router.get("/notes", response_model=Dict)
async def list_notes(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    source: Optional[str] = Query(None, description="来源过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取笔记列表
    
    支持按日期、标签、来源过滤，支持分页。
    """
    logger.info(f"GET /journal/notes limit={limit} offset={offset}")
    
    try:
        manager = _get_journal_manager()
        notes = manager.list_notes(
            start_date=start_date,
            end_date=end_date,
            tag=tag,
            source=source,
            limit=limit,
            offset=offset,
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "notes": notes,
                "total": len(notes),
                "limit": limit,
                "offset": offset,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取笔记列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取笔记列表失败: {str(e)}")


@router.get("/notes/{note_id}", response_model=Dict)
async def get_note(note_id: str):
    """获取指定笔记详情"""
    logger.info(f"GET /journal/notes/{note_id}")
    
    try:
        manager = _get_journal_manager()
        note = manager.get_note(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        # 转换为字典
        from short_win_ai_trader.modules.m08_trade_journal.journal_manager import DateTimeEncoder
        import json
        note_dict = json.loads(json.dumps(note, cls=DateTimeEncoder, ensure_ascii=False))
        
        return {
            "code": 200,
            "message": "success",
            "data": note_dict,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取笔记失败: {str(e)}")


@router.put("/notes/{note_id}", response_model=Dict)
async def update_note(note_id: str, request: TradeNoteRequest):
    """更新笔记"""
    logger.info(f"PUT /journal/notes/{note_id}")
    
    try:
        manager = _get_journal_manager()
        
        review_data = None
        if request.review:
            review_data = {
                "positions": [p.model_dump() for p in request.review.positions],
                "mindset_level": request.review.mindset_level,
                "mindset_summary": request.review.mindset_summary,
                "rhythm_summary": request.review.rhythm_summary,
                "discipline_summary": request.review.discipline_summary,
                "mindset_issues": request.review.mindset_issues,
                "rhythm_issues": request.review.rhythm_issues,
                "discipline_issues": request.review.discipline_issues,
                "lessons_learned": request.review.lessons_learned,
                "improvements": request.review.improvements,
                "overall_summary": request.review.overall_summary,
                "self_score": request.review.self_score,
            }
        
        plan_data = None
        if request.plan:
            plan_data = {
                "market_outlook": request.plan.market_outlook,
                "market_reasoning": request.plan.market_reasoning,
                "key_levels": request.plan.key_levels,
                "watch_stocks": [ws.model_dump() for ws in request.plan.watch_stocks],
                "total_position_limit": request.plan.total_position_limit,
                "single_stock_limit": request.plan.single_stock_limit,
                "max_trades": request.plan.max_trades,
                "position_plan": request.plan.position_plan,
                "stop_loss_rule": request.plan.stop_loss_rule,
                "take_profit_rule": request.plan.take_profit_rule,
                "max_daily_loss": request.plan.max_daily_loss,
                "risk_rules": request.plan.risk_rules,
                "risk_directions": request.plan.risk_directions,
                "avoid_sectors": request.plan.avoid_sectors,
                "avoid_stocks": request.plan.avoid_stocks,
                "preferred_sectors": request.plan.preferred_sectors,
                "preferred_tactics": request.plan.preferred_tactics,
                "notes": request.plan.notes,
            }
        
        note = manager.update_note(
            note_id=note_id,
            review_data=review_data,
            plan_data=plan_data,
            tags=request.tags,
        )
        
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        return {
            "code": 200,
            "message": "笔记更新成功",
            "data": {
                "note_id": note.id,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新笔记失败: {str(e)}")


@router.delete("/notes/{note_id}", response_model=Dict)
async def delete_note(note_id: str):
    """删除笔记"""
    logger.info(f"DELETE /journal/notes/{note_id}")
    
    try:
        manager = _get_journal_manager()
        success = manager.delete_note(note_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        return {
            "code": 200,
            "message": "笔记删除成功",
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除笔记失败: {str(e)}")


# ── 路由: 笔记分析 ──────────────────────────────────────


@router.get("/notes/{note_id}/analysis", response_model=Dict)
async def analyze_note(note_id: str):
    """分析笔记"""
    logger.info(f"GET /journal/notes/{note_id}/analysis")
    
    try:
        manager = _get_journal_manager()
        analysis = manager.analyze_note(note_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="笔记不存在或无复盘数据")
        
        return {
            "code": 200,
            "message": "success",
            "data": analysis,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析笔记失败: {str(e)}")


@router.get("/notes/{note_id}/plan-suggestions", response_model=Dict)
async def get_plan_suggestions(
    note_id: str,
    market_data: Optional[str] = Query(None, description="市场数据JSON"),
):
    """获取次日计划建议"""
    logger.info(f"GET /journal/notes/{note_id}/plan-suggestions")
    
    try:
        import json
        manager = _get_journal_manager()
        
        market_dict = None
        if market_data:
            market_dict = json.loads(market_data)
        
        suggestions = manager.get_plan_suggestions(note_id, market_dict)
        
        if not suggestions:
            raise HTTPException(status_code=404, detail="笔记不存在或无复盘数据")
        
        return {
            "code": 200,
            "message": "success",
            "data": suggestions,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取计划建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取计划建议失败: {str(e)}")


# ── 路由: 绩效统计 ──────────────────────────────────────


@router.get("/performance", response_model=Dict)
async def get_performance(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
):
    """获取交易绩效统计"""
    logger.info(f"GET /journal/performance days={days}")
    
    try:
        manager = _get_journal_manager()
        performance = manager.get_performance(days)
        
        return {
            "code": 200,
            "message": "success",
            "data": performance,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取绩效统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取绩效统计失败: {str(e)}")


# ── 路由: 语音输入 ──────────────────────────────────────


@router.post("/voice/upload", response_model=Dict)
async def upload_voice(
    file: UploadFile = File(..., description="音频文件"),
    note_date: Optional[str] = Query(None, description="日期"),
):
    """上传语音文件"""
    logger.info(f"POST /journal/voice/upload file={file.filename}")
    
    try:
        processor = _get_voice_processor()
        
        # 读取音频数据
        audio_data = await file.read()
        
        # 创建语音笔记
        voice_note = processor.create_voice_note(
            audio_data=audio_data,
            audio_format=file.filename.split(".")[-1] if "." in file.filename else "wav",
            duration_seconds=len(audio_data) / 16000,  # 简单估算
            note_date=date.fromisoformat(note_date) if note_date else None,
        )
        
        # 异步处理
        processed = processor.process_voice_note(voice_note.id)
        
        return {
            "code": 200,
            "message": "语音上传成功",
            "data": {
                "voice_note_id": voice_note.id,
                "status": processed.status if processed else "pending",
                "transcript": processed.transcript if processed else "",
                "parsed_type": processed.parsed_type if processed else "",
                "parsed_data": processed.parsed_data if processed else None,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"上传语音失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传语音失败: {str(e)}")


@router.post("/voice/text", response_model=Dict)
async def submit_voice_text(request: VoiceTextRequest):
    """直接提交文本（模拟语音转文字）"""
    logger.info(f"POST /journal/voice/text text_len={len(request.text)}")
    
    try:
        processor = _get_voice_processor()
        result = processor.process_text_directly(
            text=request.text,
            note_date=date.fromisoformat(request.note_date) if request.note_date else None,
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": result,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"处理文本失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理文本失败: {str(e)}")


@router.post("/voice/{voice_note_id}/convert", response_model=Dict)
async def convert_voice_to_note(voice_note_id: str):
    """将语音笔记转换为交易笔记"""
    logger.info(f"POST /journal/voice/{voice_note_id}/convert")
    
    try:
        processor = _get_voice_processor()
        manager = _get_journal_manager()
        
        voice_note = processor.get_voice_note(voice_note_id)
        if not voice_note:
            raise HTTPException(status_code=404, detail="语音笔记不存在")
        
        if voice_note.status != "completed":
            raise HTTPException(status_code=400, detail="语音笔记尚未处理完成")
        
        if not voice_note.parsed_data:
            raise HTTPException(status_code=400, detail="语音笔记无解析数据")
        
        # 创建交易笔记
        note = manager.create_note(
            review_data=voice_note.parsed_data.get("review"),
            plan_data=voice_note.parsed_data.get("plan"),
            source="voice",
            voice_note_id=voice_note_id,
            note_date=voice_note.date.isoformat() if voice_note.date else None,
        )
        
        return {
            "code": 200,
            "message": "转换成功",
            "data": {
                "note_id": note.id,
                "voice_note_id": voice_note_id,
                "parsed_type": voice_note.parsed_type,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转换语音笔记失败: {e}")
        raise HTTPException(status_code=500, detail=f"转换语音笔记失败: {str(e)}")


@router.get("/voice/notes", response_model=Dict)
async def list_voice_notes(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """获取语音笔记列表"""
    logger.info(f"GET /journal/voice/notes limit={limit}")
    
    try:
        processor = _get_voice_processor()
        notes = processor.list_voice_notes(limit)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "voice_notes": notes,
                "total": len(notes),
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取语音笔记列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取语音笔记列表失败: {str(e)}")


# ── 路由: 评分决策 ──────────────────────────────────────


@router.post("/scoring/evaluate", response_model=Dict)
async def evaluate_stock(request: ScoringRequest):
    """评估标的评分"""
    logger.info(f"POST /journal/scoring/evaluate ticker={request.ticker}")
    
    try:
        scoring = _get_scoring_integration()
        
        result = await scoring.score_stock(
            ticker=request.ticker,
            stock_name=request.stock_name,
            current_price=request.current_price,
            theme_data=request.theme_data,
            fund_data=request.fund_data,
            emotion_data=request.emotion_data,
            chip_data=request.chip_data,
            technical_data=request.technical_data,
            dragon_data=request.dragon_data,
            news_data=request.news_data,
            current_position=request.current_position,
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": result.ticker,
                "stock_name": result.stock_name,
                "current_price": result.current_price,
                "total_score": result.total_score,
                "rating": result.rating,
                "risk_level": result.risk_level,
                "dimension_scores": result.dimension_scores,
                "risk_reward_ratio": result.risk_reward_ratio,
                "entry_price": result.entry_price,
                "stop_loss": result.stop_loss,
                "take_profit": result.take_profit,
                "action": result.action,
                "position_pct": result.position_pct,
                "entry_type": result.entry_type,
                "entry_zone": result.entry_zone,
                "stop_loss_strategy": result.stop_loss_strategy,
                "take_profit_strategy": result.take_profit_strategy,
                "risk_warnings": result.risk_warnings,
                "emotion_check": result.emotion_check,
                "summary": result.summary,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"标的评分失败: {e}")
        raise HTTPException(status_code=500, detail=f"标的评分失败: {str(e)}")


@router.get("/scoring/history/{ticker}", response_model=Dict)
async def get_score_history(
    ticker: str,
    days: int = Query(30, ge=1, le=365, description="历史天数"),
):
    """获取标的评分历史"""
    logger.info(f"GET /journal/scoring/history/{ticker}")
    
    try:
        scoring = _get_scoring_integration()
        history = scoring.get_score_history(ticker, days)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "ticker": ticker,
                "history": history,
                "total": len(history),
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取评分历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分历史失败: {str(e)}")


@router.get("/scoring/statistics", response_model=Dict)
async def get_score_statistics():
    """获取评分统计"""
    logger.info("GET /journal/scoring/statistics")
    
    try:
        scoring = _get_scoring_integration()
        stats = scoring.get_score_statistics()
        
        return {
            "code": 200,
            "message": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取评分统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分统计失败: {str(e)}")