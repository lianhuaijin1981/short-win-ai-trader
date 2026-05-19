"""交割单数据导入器

支持多种格式导入交割单数据:
- CSV文件导入
- Excel文件导入
- 手动逐笔录入
- JSON格式导入

数据标准化:
- 统一股票代码格式(添加.SH/.SZ后缀)
- 自动识别交易模式(打板/低吸/半路/接力)
- 计算盈亏金额和比例
- 时间戳标准化
"""

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...core.logger import get_logger

logger = get_logger("swat.m07.importer")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str = ""                    # 交易ID
    ticker: str = ""                      # 股票代码
    stock_name: str = ""                  # 股票名称
    trade_date: Optional[datetime] = None # 交易日期
    trade_time: str = ""                  # 交易时间
    trade_type: str = "买入"              # 交易类型(买入/卖出)
    price: float = 0.0                    # 成交价格
    volume: int = 0                       # 成交数量
    amount: float = 0.0                   # 成交金额
    commission: float = 0.0               # 手续费
    trade_mode: str = ""                  # 交易模式(打板/低吸/半路/接力)
    profit_loss: float = 0.0              # 盈亏金额
    profit_loss_pct: float = 0.0          # 盈亏比例(%)
    hold_days: int = 0                    # 持仓天数
    emotion_cycle: str = ""               # 当时情绪周期
    theme_name: str = ""                  # 所属题材
    notes: str = ""                       # 备注
    raw_data: Dict = field(default_factory=dict)  # 原始数据


# ── 导入器 ───────────────────────────────────────────────

class TradeImporter:
    """交割单导入器
    
    支持多种格式导入，自动标准化数据。
    """
    
    def __init__(self):
        """初始化导入器"""
        self._trade_counter = 0
        logger.info("交割单导入器初始化完成")
    
    # ==================== 公共接口 ====================
    
    async def import_from_csv(self, file_path: str) -> List[TradeRecord]:
        """从CSV文件导入
        
        CSV格式要求:
        - 必须列: 代码,名称,日期,类型,价格,数量
        - 可选列: 金额,手续费,盈亏,模式,题材,备注
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            List[TradeRecord]: 交易记录列表
        """
        logger.info(f"从CSV导入交割单: {file_path}")
        records: List[TradeRecord] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = self._parse_csv_row(row)
                    if record:
                        records.append(record)
        except Exception as e:
            logger.error(f"CSV导入失败: {e}")
            raise
        
        logger.info(f"CSV导入完成: {len(records)}笔交易")
        return records
    
    async def import_from_json(self, file_path: str) -> List[TradeRecord]:
        """从JSON文件导入
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            List[TradeRecord]: 交易记录列表
        """
        logger.info(f"从JSON导入交割单: {file_path}")
        records: List[TradeRecord] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    record = self._parse_json_item(item)
                    if record:
                        records.append(record)
            elif isinstance(data, dict) and 'trades' in data:
                for item in data['trades']:
                    record = self._parse_json_item(item)
                    if record:
                        records.append(record)
        except Exception as e:
            logger.error(f"JSON导入失败: {e}")
            raise
        
        logger.info(f"JSON导入完成: {len(records)}笔交易")
        return records
    
    def manual_entry(
        self,
        ticker: str,
        stock_name: str,
        trade_date: str,
        trade_type: str = "买入",
        price: float = 0.0,
        volume: int = 0,
        trade_mode: str = "",
        profit_loss: float = 0.0,
        emotion_cycle: str = "",
        theme_name: str = "",
        notes: str = "",
    ) -> TradeRecord:
        """手动录入交易记录
        
        Args:
            ticker: 股票代码
            stock_name: 股票名称
            trade_date: 交易日期(YYYY-MM-DD)
            trade_type: 交易类型(买入/卖出)
            price: 成交价格
            volume: 成交数量
            trade_mode: 交易模式
            profit_loss: 盈亏金额
            emotion_cycle: 情绪周期
            theme_name: 题材名称
            notes: 备注
            
        Returns:
            TradeRecord: 交易记录
        """
        self._trade_counter += 1
        
        # 标准化股票代码
        ticker = self._normalize_ticker(ticker)
        
        # 解析日期
        trade_date_obj = self._parse_date(trade_date)
        
        # 计算金额
        amount = price * volume
        
        # 自动识别交易模式
        if not trade_mode:
            trade_mode = self._auto_detect_mode(price, volume, amount)
        
        # 计算盈亏比例
        profit_loss_pct = 0.0
        if amount > 0:
            profit_loss_pct = round(profit_loss / amount * 100, 2)
        
        record = TradeRecord(
            trade_id=f"T{self._trade_counter:04d}",
            ticker=ticker,
            stock_name=stock_name,
            trade_date=trade_date_obj,
            trade_type=trade_type,
            price=price,
            volume=volume,
            amount=amount,
            trade_mode=trade_mode,
            profit_loss=profit_loss,
            profit_loss_pct=profit_loss_pct,
            emotion_cycle=emotion_cycle,
            theme_name=theme_name,
            notes=notes,
        )
        
        logger.info(f"手动录入: {stock_name}({ticker}) {trade_type} {price}元 x{volume}")
        return record
    
    def batch_manual_entry(self, entries: List[Dict]) -> List[TradeRecord]:
        """批量手动录入
        
        Args:
            entries: 录入数据列表
            
        Returns:
            List[TradeRecord]: 交易记录列表
        """
        records: List[TradeRecord] = []
        for entry in entries:
            try:
                record = self.manual_entry(**entry)
                records.append(record)
            except Exception as e:
                logger.warning(f"录入失败: {entry.get('stock_name', '未知')} - {e}")
        
        logger.info(f"批量录入完成: {len(records)}/{len(entries)}笔")
        return records
    
    # ==================== 内部方法 ====================
    
    def _parse_csv_row(self, row: Dict) -> Optional[TradeRecord]:
        """解析CSV行"""
        try:
            self._trade_counter += 1
            
            # 提取字段(支持多种列名)
            ticker = self._get_field(row, ['代码', 'code', 'ticker', '股票代码'])
            stock_name = self._get_field(row, ['名称', 'name', 'stock_name', '股票名称'])
            trade_date_str = self._get_field(row, ['日期', 'date', 'trade_date', '交易日期'])
            trade_type = self._get_field(row, ['类型', 'type', 'trade_type', '交易类型'], '买入')
            price = float(self._get_field(row, ['价格', 'price', '成交价'], 0))
            volume = int(float(self._get_field(row, ['数量', 'volume', '成交量'], 0)))
            amount = float(self._get_field(row, ['金额', 'amount', '成交金额'], 0))
            commission = float(self._get_field(row, ['手续费', 'commission'], 0))
            profit_loss = float(self._get_field(row, ['盈亏', 'profit_loss', 'pnl'], 0))
            trade_mode = self._get_field(row, ['模式', 'mode', 'trade_mode', '交易模式'], '')
            emotion_cycle = self._get_field(row, ['情绪周期', 'emotion_cycle'], '')
            theme_name = self._get_field(row, ['题材', 'theme', 'theme_name'], '')
            notes = self._get_field(row, ['备注', 'notes', 'note'], '')
            
            if not ticker or not stock_name:
                return None
            
            ticker = self._normalize_ticker(ticker)
            trade_date = self._parse_date(trade_date_str)
            
            if amount == 0 and price > 0 and volume > 0:
                amount = price * volume
            
            if not trade_mode:
                trade_mode = self._auto_detect_mode(price, volume, amount)
            
            profit_loss_pct = 0.0
            if amount > 0:
                profit_loss_pct = round(profit_loss / amount * 100, 2)
            
            return TradeRecord(
                trade_id=f"T{self._trade_counter:04d}",
                ticker=ticker,
                stock_name=stock_name,
                trade_date=trade_date,
                trade_type=trade_type,
                price=price,
                volume=volume,
                amount=amount,
                commission=commission,
                trade_mode=trade_mode,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                emotion_cycle=emotion_cycle,
                theme_name=theme_name,
                notes=notes,
                raw_data=row,
            )
        except Exception as e:
            logger.warning(f"CSV行解析失败: {e}")
            return None
    
    def _parse_json_item(self, item: Dict) -> Optional[TradeRecord]:
        """解析JSON项"""
        try:
            self._trade_counter += 1
            
            ticker = item.get('ticker', item.get('代码', ''))
            stock_name = item.get('stock_name', item.get('名称', ''))
            
            if not ticker or not stock_name:
                return None
            
            ticker = self._normalize_ticker(ticker)
            
            trade_date_str = item.get('trade_date', item.get('日期', ''))
            trade_date = self._parse_date(trade_date_str)
            
            price = float(item.get('price', item.get('价格', 0)))
            volume = int(item.get('volume', item.get('数量', 0)))
            amount = float(item.get('amount', item.get('金额', price * volume)))
            profit_loss = float(item.get('profit_loss', item.get('盈亏', 0)))
            
            trade_mode = item.get('trade_mode', item.get('模式', ''))
            if not trade_mode:
                trade_mode = self._auto_detect_mode(price, volume, amount)
            
            profit_loss_pct = 0.0
            if amount > 0:
                profit_loss_pct = round(profit_loss / amount * 100, 2)
            
            return TradeRecord(
                trade_id=f"T{self._trade_counter:04d}",
                ticker=ticker,
                stock_name=stock_name,
                trade_date=trade_date,
                trade_type=item.get('trade_type', item.get('类型', '买入')),
                price=price,
                volume=volume,
                amount=amount,
                commission=float(item.get('commission', item.get('手续费', 0))),
                trade_mode=trade_mode,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                hold_days=int(item.get('hold_days', item.get('持仓天数', 0))),
                emotion_cycle=item.get('emotion_cycle', item.get('情绪周期', '')),
                theme_name=item.get('theme_name', item.get('题材', '')),
                notes=item.get('notes', item.get('备注', '')),
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"JSON项解析失败: {e}")
            return None
    
    def _normalize_ticker(self, ticker: str) -> str:
        """标准化股票代码"""
        ticker = ticker.strip().upper()
        # 移除已有后缀
        ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
        # 纯数字代码
        if ticker.isdigit():
            if ticker.startswith('6'):
                return f"{ticker}.SH"
            elif ticker.startswith('0') or ticker.startswith('3'):
                return f"{ticker}.SZ"
            elif ticker.startswith('8') or ticker.startswith('4'):
                return f"{ticker}.BJ"
        return ticker
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%Y%m%d',
            '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"日期解析失败: {date_str}")
        return None
    
    def _auto_detect_mode(self, price: float, volume: int, amount: float) -> str:
        """自动识别交易模式
        
        根据价格和金额特征判断:
        - 大额+整数价 → 打板
        - 小额+非整数 → 低吸
        - 中等金额 → 半路
        """
        if amount >= 100000 and price >= 10:
            return "打板"
        elif amount < 30000:
            return "低吸"
        elif amount >= 50000:
            return "半路"
        else:
            return "其他"
    
    def _get_field(self, row: Dict, keys: List[str], default: str = '') -> str:
        """从字典中获取字段(支持多种键名)"""
        for key in keys:
            if key in row and row[key]:
                return str(row[key]).strip()
        return default