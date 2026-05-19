"""语音输入处理器 — 语音转文字与结构化解析

提供:
1. 语音录制与存储
2. 语音转文字（STT）
3. 文本结构化解析（识别复盘/计划内容）
4. 语音笔记管理
"""

import uuid
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from ...core.logger import get_logger
from .models import VoiceNote

logger = get_logger("swat.m08.voice_processor")


class VoiceProcessor:
    """语音输入处理器
    
    负责语音输入的接收、转写和结构化解析。
    支持语音创建复盘笔记和交易计划。
    """
    
    def __init__(self):
        """初始化语音处理器"""
        # 语音笔记存储
        self._voice_notes: Dict[str, VoiceNote] = {}
        
        # 关键词映射（用于解析语音内容）
        self._review_keywords = [
            "今天", "今日", "复盘", "交易", "买入", "卖出", "持仓",
            "盈利", "亏损", "涨停", "跌停", "打板", "低吸",
            "心态", "节奏", "纪律", "失误", "教训",
        ]
        
        self._plan_keywords = [
            "明天", "明日", "次日", "计划", "预判", "大盘",
            "仓位", "风控", "止损", "止盈", "观察", "跟踪",
            "重点关注", "规避", "避雷",
        ]
        
        self._position_keywords = [
            "买入", "卖出", "持仓", "加仓", "减仓", "清仓",
            "进场", "出场", "建仓", "平仓",
        ]
        
        self._mindset_keywords = {
            "优秀": ["心态很好", "状态很好", "很冷静", "很理性", "执行到位"],
            "良好": ["心态不错", "状态不错", "还可以", "比较好"],
            "一般": ["一般", "还行", "马马虎虎", "普普通通"],
            "较差": ["心态不好", "有点急", "有点慌", "没控制好"],
            "极差": ["心态崩了", "完全失控", "情绪化", "乱操作"],
        }
        
        logger.info("语音处理器初始化完成")
    
    # ==================== 语音处理 ====================
    
    def create_voice_note(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        duration_seconds: float = 0.0,
        note_date: Optional[date] = None,
    ) -> VoiceNote:
        """创建语音笔记
        
        Args:
            audio_data: 音频数据（二进制）
            audio_format: 音频格式
            duration_seconds: 录音时长
            note_date: 录音日期
            
        Returns:
            VoiceNote: 语音笔记对象
        """
        voice_note = VoiceNote(
            id=str(uuid.uuid4())[:12],
            date=note_date or date.today(),
            created_at=datetime.now(),
            audio_data=audio_data,
            audio_format=audio_format,
            duration_seconds=duration_seconds,
            status="pending",
        )
        
        self._voice_notes[voice_note.id] = voice_note
        logger.info(f"创建语音笔记: ID={voice_note.id}, 时长={duration_seconds}s")
        
        return voice_note
    
    def process_voice_note(self, voice_note_id: str) -> Optional[VoiceNote]:
        """处理语音笔记（转写+解析）
        
        Args:
            voice_note_id: 语音笔记ID
            
        Returns:
            处理后的VoiceNote或None
        """
        voice_note = self._voice_notes.get(voice_note_id)
        if not voice_note:
            logger.warning(f"语音笔记不存在: {voice_note_id}")
            return None
        
        try:
            voice_note.status = "processing"
            
            # Step 1: 语音转文字
            transcript = self._speech_to_text(voice_note)
            voice_note.transcript = transcript
            
            if not transcript:
                voice_note.status = "failed"
                voice_note.error_message = "语音转文字失败"
                return voice_note
            
            # Step 2: 解析内容类型
            parsed_type = self._detect_content_type(transcript)
            voice_note.parsed_type = parsed_type
            
            # Step 3: 结构化解析
            parsed_data = self._parse_transcript(transcript, parsed_type)
            voice_note.parsed_data = parsed_data
            
            voice_note.status = "completed"
            logger.info(f"语音笔记处理完成: ID={voice_note_id}, 类型={parsed_type}")
            
            return voice_note
            
        except Exception as e:
            voice_note.status = "failed"
            voice_note.error_message = str(e)
            logger.error(f"语音笔记处理失败: {e}")
            return voice_note
    
    def process_text_directly(self, text: str, note_date: Optional[date] = None) -> Dict:
        """直接处理文本输入（模拟语音转文字后的处理）
        
        Args:
            text: 输入文本
            note_date: 日期
            
        Returns:
            解析结果
        """
        parsed_type = self._detect_content_type(text)
        parsed_data = self._parse_transcript(text, parsed_type)
        
        return {
            "transcript": text,
            "parsed_type": parsed_type,
            "parsed_data": parsed_data,
        }
    
    # ==================== 语音转文字 ====================
    
    def _speech_to_text(self, voice_note: VoiceNote) -> str:
        """语音转文字
        
        注意: 这里是模拟实现，实际应调用语音识别API
        如: 百度语音、讯飞语音、Whisper等
        
        Args:
            voice_note: 语音笔记
            
        Returns:
            转写文本
        """
        # 模拟实现：实际项目中应替换为真实的STT调用
        # 这里返回模拟文本用于测试
        
        if voice_note.audio_data:
            # 可以根据音频特征生成不同的模拟文本
            logger.info(f"模拟语音转文字: {voice_note.duration_seconds}s音频")
            
            # 返回模拟文本
            return self._generate_mock_transcript(voice_note.duration_seconds)
        
        return ""
    
    def _generate_mock_transcript(self, duration: float) -> str:
        """生成模拟转写文本（用于测试）"""
        if duration < 10:
            return "今天买了中际旭创，盈利3个点，心态还可以。"
        elif duration < 30:
            return (
                "今天复盘：早上打板了中际旭创，封板很稳，盈利3个点。"
                "下午低吸了科大讯飞，尾盘拉升，盈利2个点。"
                "今天整体心态不错，执行到位，没有乱操作。"
                "明天计划：大盘看震荡偏多，重点关注AI板块，"
                "仓位控制在50%以内，单票不超过20%。"
            )
        else:
            return (
                "今天交易复盘：总共做了3笔交易。"
                "第一笔，早上9点35分打板中际旭创，CPO概念龙头，封单很强，盈利3.5%。"
                "第二笔，10点半低吸科大讯飞，AI应用端，尾盘拉升盈利2%。"
                "第三笔，下午追高买了歌尔股份，结果炸板了，亏损1.5%，这笔操作有问题，不该追高。"
                "今天整体盈利4%，心态良好，但第三笔追高是失误，需要反思。"
                "明天交易计划：大盘判断震荡偏多，上证支撑位3250，压力位3320。"
                "重点观察中际旭创能否连板，科大讯飞是否继续强势。"
                "仓位控制在50%以内，单票不超过20%，最多做3笔交易。"
                "止损纪律：固定止损-5%，逻辑止损无条件卖出。"
                "规避高位连板股，注意情绪退潮风险。"
            )
    
    # ==================== 内容解析 ====================
    
    def _detect_content_type(self, text: str) -> str:
        """检测文本内容类型
        
        Args:
            text: 输入文本
            
        Returns:
            内容类型: review/plan/mixed
        """
        review_score = sum(1 for kw in self._review_keywords if kw in text)
        plan_score = sum(1 for kw in self._plan_keywords if kw in text)
        
        if review_score > 0 and plan_score > 0:
            return "mixed"
        elif review_score > plan_score:
            return "review"
        elif plan_score > 0:
            return "plan"
        else:
            return "review"  # 默认作为复盘
    
    def _parse_transcript(self, text: str, content_type: str) -> Dict:
        """解析文本为结构化数据
        
        Args:
            text: 输入文本
            content_type: 内容类型
            
        Returns:
            结构化数据
        """
        result = {}
        
        if content_type in ("review", "mixed"):
            result["review"] = self._parse_review(text)
        
        if content_type in ("plan", "mixed"):
            result["plan"] = self._parse_plan(text)
        
        return result
    
    def _parse_review(self, text: str) -> Dict:
        """解析复盘内容
        
        Args:
            text: 输入文本
            
        Returns:
            复盘数据
        """
        review = {
            "positions": [],
            "mindset_level": "一般",
            "mindset_summary": "",
            "overall_summary": "",
            "lessons_learned": [],
            "improvements": [],
        }
        
        # 解析持仓交易
        positions = self._extract_positions(text)
        review["positions"] = positions
        
        # 解析心态
        mindset = self._extract_mindset(text)
        review["mindset_level"] = mindset
        
        # 解析盈亏
        pnl = self._extract_pnl(text)
        if pnl:
            review["overall_summary"] = f"整体{pnl}"
        
        # 解析失误
        errors = self._extract_errors(text)
        if errors:
            review["improvements"] = errors
        
        return review
    
    def _parse_plan(self, text: str) -> Dict:
        """解析计划内容
        
        Args:
            text: 输入文本
            
        Returns:
            计划数据
        """
        plan = {
            "market_outlook": "震荡中性",
            "market_reasoning": "",
            "key_levels": "",
            "watch_stocks": [],
            "total_position_limit": 50.0,
            "single_stock_limit": 20.0,
            "max_trades": 3,
            "stop_loss_rule": "",
            "risk_rules": [],
            "preferred_sectors": [],
            "avoid_sectors": [],
        }
        
        # 解析大盘判断
        outlook = self._extract_market_outlook(text)
        plan["market_outlook"] = outlook
        
        # 解析关键价位
        levels = self._extract_key_levels(text)
        if levels:
            plan["key_levels"] = levels
        
        # 解析观察标的
        watch_stocks = self._extract_watch_stocks(text)
        plan["watch_stocks"] = watch_stocks
        
        # 解析仓位
        position = self._extract_position_limit(text)
        if position:
            plan["total_position_limit"] = position
        
        # 解析板块
        sectors = self._extract_sectors(text)
        plan["preferred_sectors"] = sectors.get("preferred", [])
        plan["avoid_sectors"] = sectors.get("avoid", [])
        
        return plan
    
    # ==================== 信息提取 ====================
    
    def _extract_positions(self, text: str) -> List[Dict]:
        """从文本中提取持仓交易信息"""
        positions = []
        
        # 简单关键词匹配提取
        # 实际项目中应使用NLP模型进行更精确的提取
        
        sentences = text.replace("。", "。|").replace("，", "，|").split("|")
        
        current_position = {}
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 检测股票名称（简单匹配常见股票）
            stock_names = [
                "中际旭创", "科大讯飞", "歌尔股份", "比亚迪", "宁德时代",
                "贵州茅台", "平安银行", "北方华创", "新易盛", "瑞芯微",
            ]
            
            for name in stock_names:
                if name in sentence:
                    if current_position and current_position.get("stock_name"):
                        positions.append(current_position)
                    current_position = {"stock_name": name, "ticker": ""}
                    
                    # 检测操作
                    if "打板" in sentence or "买入" in sentence:
                        current_position["entry_method"] = "打板" if "打板" in sentence else "买入"
                    elif "低吸" in sentence:
                        current_position["entry_method"] = "低吸"
                    elif "卖出" in sentence or "清仓" in sentence:
                        current_position["exit_reason"] = sentence
                    
                    # 检测盈亏
                    if "盈利" in sentence:
                        current_position["result"] = "盈利"
                        # 提取百分比
                        import re
                        match = re.search(r'盈利(\d+\.?\d*)[%点]', sentence)
                        if match:
                            current_position["profit_loss_pct"] = float(match.group(1))
                    elif "亏损" in sentence:
                        current_position["result"] = "亏损"
                        import re
                        match = re.search(r'亏损(\d+\.?\d*)[%点]', sentence)
                        if match:
                            current_position["profit_loss_pct"] = -float(match.group(1))
                    
                    # 检测失误
                    if "失误" in sentence or "不该" in sentence or "有问题" in sentence:
                        current_position["has_error"] = True
                        current_position["error_summary"] = sentence
        
        if current_position and current_position.get("stock_name"):
            positions.append(current_position)
        
        return positions
    
    def _extract_mindset(self, text: str) -> str:
        """从文本中提取心态评级"""
        for level, keywords in self._mindset_keywords.items():
            for kw in keywords:
                if kw in text:
                    return level
        return "一般"
    
    def _extract_pnl(self, text: str) -> Optional[str]:
        """从文本中提取整体盈亏"""
        import re
        match = re.search(r'整体(盈利|亏损)(\d+\.?\d*)[%点]', text)
        if match:
            return f"{match.group(1)}{match.group(2)}%"
        return None
    
    def _extract_errors(self, text: str) -> List[str]:
        """从文本中提取失误/改进点"""
        errors = []
        error_keywords = ["失误", "不该", "有问题", "反思", "教训", "错误"]
        
        sentences = text.split("。")
        for sentence in sentences:
            for kw in error_keywords:
                if kw in sentence:
                    errors.append(sentence.strip())
                    break
        
        return errors
    
    def _extract_market_outlook(self, text: str) -> str:
        """从文本中提取大盘判断"""
        outlook_map = {
            "强势看多": ["强势", "看多", "大涨", "牛市"],
            "震荡偏多": ["震荡偏多", "偏多", "看好", "乐观"],
            "震荡中性": ["震荡", "中性", "不确定"],
            "震荡偏空": ["震荡偏空", "偏空", "谨慎", "看淡"],
            "弱势看空": ["弱势", "看空", "大跌", "熊市"],
        }
        
        for outlook, keywords in outlook_map.items():
            for kw in keywords:
                if kw in text:
                    return outlook
        
        return "震荡中性"
    
    def _extract_key_levels(self, text: str) -> str:
        """从文本中提取关键价位"""
        import re
        levels = []
        
        # 匹配支撑位
        match = re.search(r'支撑位?(\d{4})', text)
        if match:
            levels.append(f"支撑{match.group(1)}")
        
        # 匹配压力位
        match = re.search(r'压力位?(\d{4})', text)
        if match:
            levels.append(f"压力{match.group(1)}")
        
        return "，".join(levels) if levels else ""
    
    def _extract_watch_stocks(self, text: str) -> List[Dict]:
        """从文本中提取观察标的"""
        stocks = []
        stock_names = [
            "中际旭创", "科大讯飞", "歌尔股份", "比亚迪", "宁德时代",
            "贵州茅台", "平安银行", "北方华创", "新易盛", "瑞芯微",
        ]
        
        watch_keywords = ["观察", "关注", "跟踪", "重点", "留意"]
        
        for name in stock_names:
            if name in text:
                # 检查是否在观察语境中
                is_watch = any(kw in text for kw in watch_keywords)
                if is_watch or "明天" in text or "明日" in text:
                    stocks.append({
                        "stock_name": name,
                        "ticker": "",
                        "watch_reason": f"语音识别：关注{name}",
                        "priority": 1 if "重点" in text else 2,
                    })
        
        return stocks
    
    def _extract_position_limit(self, text: str) -> Optional[float]:
        """从文本中提取仓位限制"""
        import re
        match = re.search(r'仓位[控制]?在?(\d+)[%以]', text)
        if match:
            return float(match.group(1))
        return None
    
    def _extract_sectors(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取板块信息"""
        result = {"preferred": [], "avoid": []}
        
        sector_map = {
            "AI": ["AI", "人工智能", "AI板块"],
            "CPO": ["CPO", "光模块"],
            "半导体": ["半导体", "芯片"],
            "新能源": ["新能源", "锂电", "光伏"],
            "消费": ["消费", "白酒"],
        }
        
        # 重点关注板块
        preferred_keywords = ["重点关注", "关注", "看好", "重点"]
        for sector, keywords in sector_map.items():
            for kw in keywords:
                if kw in text:
                    # 检查是否在关注语境
                    if any(pk in text for pk in preferred_keywords):
                        if sector not in result["preferred"]:
                            result["preferred"].append(sector)
        
        # 规避板块
        avoid_keywords = ["规避", "回避", "避雷", "小心", "注意风险"]
        for sector, keywords in sector_map.items():
            for kw in keywords:
                if kw in text:
                    if any(ak in text for ak in avoid_keywords):
                        if sector not in result["avoid"]:
                            result["avoid"].append(sector)
        
        return result
    
    # ==================== 语音笔记管理 ====================
    
    def get_voice_note(self, voice_note_id: str) -> Optional[VoiceNote]:
        """获取语音笔记"""
        return self._voice_notes.get(voice_note_id)
    
    def list_voice_notes(self, limit: int = 20) -> List[Dict]:
        """列出语音笔记"""
        notes = sorted(
            self._voice_notes.values(),
            key=lambda x: x.created_at or datetime.min,
            reverse=True,
        )[:limit]
        
        return [
            {
                "id": n.id,
                "date": n.date.isoformat() if n.date else None,
                "duration_seconds": n.duration_seconds,
                "status": n.status,
                "parsed_type": n.parsed_type,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ]
    
    def delete_voice_note(self, voice_note_id: str) -> bool:
        """删除语音笔记"""
        if voice_note_id in self._voice_notes:
            del self._voice_notes[voice_note_id]
            return True
        return False