#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库模型层
提供数据持久化功能，支持股票行情、资金流向、交易记录等数据存储
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Text, Boolean, Index, UniqueConstraint, func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

# ── 数据库配置 ────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/short_win_trader'
)

# 连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── 数据库模型 ────────────────────────────────────────────────────

class StockBasic(Base):
    """股票基本信息表"""
    __tablename__ = 'stock_basic'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), unique=True, nullable=False, index=True)
    symbol = Column(String(20), index=True)
    name = Column(String(50), nullable=False)
    area = Column(String(20))
    industry = Column(String(30), index=True)
    market = Column(String(20))
    list_date = Column(String(20))
    is_hs = Column(String(10))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_stock_basic_code', 'ts_code', 'symbol'),
    )


class StockDaily(Base):
    """股票日线行情表"""
    __tablename__ = 'stock_daily'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(String(20), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)
    turnover_rate = Column(Float)
    volume_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uq_stock_daily_code_date'),
        Index('idx_stock_daily_date', 'trade_date', 'pct_chg'),
    )


class StockRealtime(Base):
    """股票实时行情表"""
    __tablename__ = 'stock_realtime'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    name = Column(String(50))
    price = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    bid_vol = Column(Float)
    ask_vol = Column(Float)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_stock_realtime_code', 'ts_code', 'timestamp'),
    )


class StockMoneyflow(Base):
    """个股资金流向表"""
    __tablename__ = 'stock_moneyflow'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(String(20), nullable=False, index=True)
    buy_elg_amount = Column(Float)  # 超大单买入
    sell_elg_amount = Column(Float)  # 超大单卖出
    buy_lg_amount = Column(Float)    # 大单买入
    sell_lg_amount = Column(Float)   # 大单卖出
    buy_md_amount = Column(Float)    # 中单买入
    sell_md_amount = Column(Float)   # 中单卖出
    buy_sm_amount = Column(Float)    # 小单买入
    sell_sm_amount = Column(Float)   # 小单卖出
    net_elg_amount = Column(Float)   # 超大单净流入
    net_lg_amount = Column(Float)    # 大单净流入
    net_md_amount = Column(Float)    # 中单净流入
    net_sm_amount = Column(Float)    # 小单净流入
    net_amount = Column(Float)       # 总净流入
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uq_moneyflow_code_date'),
        Index('idx_moneyflow_net', 'trade_date', 'net_amount'),
    )


class IndexDaily(Base):
    """大盘指数日线表"""
    __tablename__ = 'index_daily'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(String(20), nullable=False, index=True)
    close = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uq_index_daily_code_date'),
    )


class LimitStock(Base):
    """涨跌停股票表"""
    __tablename__ = 'limit_stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    name = Column(String(50))
    trade_date = Column(String(20), nullable=False, index=True)
    limit_type = Column(String(10), nullable=False)  # U=涨停, D=跌停
    price = Column(Float)
    pct_chg = Column(Float)
    amount = Column(Float)
    turnover_rate = Column(Float)
    free_float = Column(Float)
    limit_order = Column(Float)  # 封单量
    limit_amount = Column(Float)  # 封单额
    first_time = Column(String(20))  # 首次涨停时间
    last_time = Column(String(20))   # 最后涨停时间
    open_times = Column(Integer)     # 开板次数
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_limit_stocks_date_type', 'trade_date', 'limit_type'),
    )


class NorthboundFlow(Base):
    """北向资金流向表"""
    __tablename__ = 'northbound_flow'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(20), nullable=False, unique=True, index=True)
    north_money = Column(Float)      # 北向资金净流入
    south_money = Column(Float)      # 南向资金净流入
    north_buy = Column(Float)        # 北向买入
    north_sell = Column(Float)       # 北向卖出
    created_at = Column(DateTime, default=datetime.now)


class TradeRecord(Base):
    """交易记录表"""
    __tablename__ = 'trade_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    trade_type = Column(String(10), nullable=False)  # BUY/SELL
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    amount = Column(Float)
    commission = Column(Float)
    tax = Column(Float)
    profit = Column(Float)
    trade_date = Column(String(20), nullable=False, index=True)
    trade_time = Column(DateTime, default=datetime.now)
    strategy = Column(String(50))
    note = Column(Text)
    status = Column(String(20), default='COMPLETED')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_trade_records_date', 'trade_date', 'trade_type'),
    )


class TradeJournal(Base):
    """交易日志表"""
    __tablename__ = 'trade_journal'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(20), nullable=False, unique=True, index=True)
    market_sentiment = Column(String(20))  # 市场情绪
    position_ratio = Column(Float)         # 仓位比例
    daily_profit = Column(Float)           # 当日盈亏
    trade_count = Column(Integer)          # 交易次数
    win_rate = Column(Float)               # 胜率
    max_drawdown = Column(Float)           # 最大回撤
    summary = Column(Text)                 # 总结
    plan = Column(Text)                    # 明日计划
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class NewsRecord(Base):
    """新闻记录表"""
    __tablename__ = 'news_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    source = Column(String(50))
    category = Column(String(30), index=True)
    publish_time = Column(DateTime)
    url = Column(String(500))
    importance = Column(Integer, default=1)  # 1-5重要性
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_news_category_time', 'category', 'publish_time'),
    )


class WebSocketMessage(Base):
    """WebSocket消息记录表"""
    __tablename__ = 'websocket_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False, index=True)
    message_type = Column(String(30), nullable=False)
    payload = Column(Text)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now, index=True)


# ── 数据库操作类 ──────────────────────────────────────────────────

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def init_db(self):
        """初始化数据库（创建所有表）"""
        Base.metadata.create_all(bind=self.engine)
        print("数据库初始化完成")
    
    def drop_db(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)
        print("数据库已删除")
    
    # ── 股票基本信息操作 ──────────────────────────────────────
    
    def upsert_stock_basic(self, data: Dict[str, Any]) -> int:
        """插入或更新股票基本信息"""
        with self.get_session() as session:
            stock = session.query(StockBasic).filter(
                StockBasic.ts_code == data['ts_code']
            ).first()
            
            if stock:
                for key, value in data.items():
                    if hasattr(stock, key):
                        setattr(stock, key, value)
            else:
                stock = StockBasic(**data)
                session.add(stock)
            
            session.flush()
            return stock.id
    
    def get_stock_basic(self, ts_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        with self.get_session() as session:
            stock = session.query(StockBasic).filter(
                StockBasic.ts_code == ts_code
            ).first()
            return stock.__dict__ if stock else None
    
    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索股票"""
        with self.get_session() as session:
            stocks = session.query(StockBasic).filter(
                (StockBasic.ts_code.ilike(f'%{keyword}%')) |
                (StockBasic.name.ilike(f'%{keyword}%')) |
                (StockBasic.symbol.ilike(f'%{keyword}%'))
            ).limit(limit).all()
            return [s.__dict__ for s in stocks]
    
    # ── 日线行情操作 ──────────────────────────────────────────
    
    def upsert_stock_daily(self, data: Dict[str, Any]) -> int:
        """插入或更新日线数据"""
        with self.get_session() as session:
            daily = session.query(StockDaily).filter(
                StockDaily.ts_code == data['ts_code'],
                StockDaily.trade_date == data['trade_date']
            ).first()
            
            if daily:
                for key, value in data.items():
                    if hasattr(daily, key):
                        setattr(daily, key, value)
            else:
                daily = StockDaily(**data)
                session.add(daily)
            
            session.flush()
            return daily.id
    
    def batch_upsert_stock_daily(self, data_list: List[Dict[str, Any]]):
        """批量插入或更新日线数据"""
        with self.get_session() as session:
            for data in data_list:
                daily = session.query(StockDaily).filter(
                    StockDaily.ts_code == data['ts_code'],
                    StockDaily.trade_date == data['trade_date']
                ).first()
                
                if daily:
                    for key, value in data.items():
                        if hasattr(daily, key):
                            setattr(daily, key, value)
                else:
                    daily = StockDaily(**data)
                    session.add(daily)
    
    def get_stock_daily(self, ts_code: str, start_date: str = None, 
                        end_date: str = None, limit: int = 100) -> List[Dict]:
        """获取股票日线数据"""
        with self.get_session() as session:
            query = session.query(StockDaily).filter(
                StockDaily.ts_code == ts_code
            )
            if start_date:
                query = query.filter(StockDaily.trade_date >= start_date)
            if end_date:
                query = query.filter(StockDaily.trade_date <= end_date)
            
            dailies = query.order_by(StockDaily.trade_date.desc()).limit(limit).all()
            return [d.__dict__ for d in dailies]
    
    # ── 实时行情操作 ──────────────────────────────────────────
    
    def insert_stock_realtime(self, data: Dict[str, Any]) -> int:
        """插入实时行情数据"""
        with self.get_session() as session:
            realtime = StockRealtime(**data)
            session.add(realtime)
            session.flush()
            return realtime.id
    
    def get_latest_realtime(self, ts_code: str) -> Optional[Dict]:
        """获取最新实时行情"""
        with self.get_session() as session:
            realtime = session.query(StockRealtime).filter(
                StockRealtime.ts_code == ts_code
            ).order_by(StockRealtime.timestamp.desc()).first()
            return realtime.__dict__ if realtime else None
    
    # ── 资金流向操作 ──────────────────────────────────────────
    
    def upsert_stock_moneyflow(self, data: Dict[str, Any]) -> int:
        """插入或更新资金流向数据"""
        with self.get_session() as session:
            mf = session.query(StockMoneyflow).filter(
                StockMoneyflow.ts_code == data['ts_code'],
                StockMoneyflow.trade_date == data['trade_date']
            ).first()
            
            if mf:
                for key, value in data.items():
                    if hasattr(mf, key):
                        setattr(mf, key, value)
            else:
                mf = StockMoneyflow(**data)
                session.add(mf)
            
            session.flush()
            return mf.id
    
    def get_stock_moneyflow(self, ts_code: str, limit: int = 30) -> List[Dict]:
        """获取资金流向数据"""
        with self.get_session() as session:
            mfs = session.query(StockMoneyflow).filter(
                StockMoneyflow.ts_code == ts_code
            ).order_by(StockMoneyflow.trade_date.desc()).limit(limit).all()
            return [m.__dict__ for m in mfs]
    
    # ── 涨跌停操作 ────────────────────────────────────────────
    
    def batch_insert_limit_stocks(self, data_list: List[Dict[str, Any]]):
        """批量插入涨跌停数据"""
        with self.get_session() as session:
            for data in data_list:
                limit_stock = LimitStock(**data)
                session.add(limit_stock)
    
    def get_limit_stocks(self, trade_date: str, limit_type: str = 'U') -> List[Dict]:
        """获取涨跌停股票列表"""
        with self.get_session() as session:
            stocks = session.query(LimitStock).filter(
                LimitStock.trade_date == trade_date,
                LimitStock.limit_type == limit_type
            ).all()
            return [s.__dict__ for s in stocks]
    
    # ── 交易记录操作 ──────────────────────────────────────────
    
    def insert_trade_record(self, data: Dict[str, Any]) -> int:
        """插入交易记录"""
        with self.get_session() as session:
            trade = TradeRecord(**data)
            session.add(trade)
            session.flush()
            return trade.id
    
    def get_trade_records(self, start_date: str = None, end_date: str = None,
                          stock_code: str = None, limit: int = 100) -> List[Dict]:
        """获取交易记录"""
        with self.get_session() as session:
            query = session.query(TradeRecord)
            if start_date:
                query = query.filter(TradeRecord.trade_date >= start_date)
            if end_date:
                query = query.filter(TradeRecord.trade_date <= end_date)
            if stock_code:
                query = query.filter(TradeRecord.stock_code == stock_code)
            
            records = query.order_by(TradeRecord.trade_time.desc()).limit(limit).all()
            return [r.__dict__ for r in records]
    
    # ── 统计查询 ──────────────────────────────────────────────
    
    def get_daily_stats(self, trade_date: str) -> Dict:
        """获取每日统计"""
        with self.get_session() as session:
            # 涨跌家数
            up_count = session.query(func.count(StockDaily.id)).filter(
                StockDaily.trade_date == trade_date,
                StockDaily.pct_chg > 0
            ).scalar()
            
            down_count = session.query(func.count(StockDaily.id)).filter(
                StockDaily.trade_date == trade_date,
                StockDaily.pct_chg < 0
            ).scalar()
            
            # 涨停跌停
            limit_up = session.query(func.count(LimitStock.id)).filter(
                LimitStock.trade_date == trade_date,
                LimitStock.limit_type == 'U'
            ).scalar()
            
            limit_down = session.query(func.count(LimitStock.id)).filter(
                LimitStock.trade_date == trade_date,
                LimitStock.limit_type == 'D'
            ).scalar()
            
            return {
                'trade_date': trade_date,
                'up_count': up_count or 0,
                'down_count': down_count or 0,
                'limit_up': limit_up or 0,
                'limit_down': limit_down or 0,
                'total': (up_count or 0) + (down_count or 0)
            }


# ── 全局数据库管理器实例 ─────────────────────────────────────────

db_manager = DatabaseManager()


def get_db() -> Session:
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    # 测试数据库连接
    print("测试数据库连接...")
    try:
        db_manager.init_db()
        print("数据库连接成功，表已创建")
    except Exception as e:
        print(f"数据库连接失败: {e}")