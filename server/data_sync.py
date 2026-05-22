#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步服务
从Tushare获取数据并存储到PostgreSQL，同时通过WebSocket推送更新
支持定时任务和手动触发
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import tushare as ts
from dotenv import load_dotenv

from database import db_manager
from websocket_server import pusher, broadcast_to_room

load_dotenv()

# ── 配置 ──────────────────────────────────────────────────────────

TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', '300'))  # 默认5分钟同步一次
WATCH_LIST = os.getenv('WATCH_LIST', '000001.SZ,600000.SH,000002.SZ,600519.SH,000858.SZ').split(',')

# 初始化Tushare
if TUSHARE_TOKEN:
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
else:
    print("警告: 未设置 TUSHARE_TOKEN")
    pro = None


# ── 数据同步类 ────────────────────────────────────────────────────

class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self._running = False
        self._sync_thread: Optional[threading.Thread] = None
    
    def start(self, interval: int = None):
        """启动定时同步"""
        if self._running:
            return
        
        self._running = True
        interval = interval or SYNC_INTERVAL
        
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            args=(interval,),
            daemon=True
        )
        self._sync_thread.start()
        print(f"数据同步服务已启动，间隔: {interval}秒")
    
    def stop(self):
        """停止同步"""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=10)
        print("数据同步服务已停止")
    
    def _sync_loop(self, interval: int):
        """同步循环"""
        while self._running:
            try:
                self.sync_all()
            except Exception as e:
                print(f"同步错误: {e}")
            
            time.sleep(interval)
    
    def sync_all(self):
        """同步所有数据"""
        print(f"[{datetime.now()}] 开始数据同步...")
        
        # 同步股票基本信息
        self.sync_stock_basic()
        
        # 同步日线数据
        self.sync_daily()
        
        # 同步实时行情
        self.sync_realtime()
        
        # 同步资金流向
        self.sync_moneyflow()
        
        # 同步大盘指数
        self.sync_index()
        
        # 同步北向资金
        self.sync_northbound()
        
        print(f"[{datetime.now()}] 数据同步完成")
    
    def sync_stock_basic(self):
        """同步股票基本信息"""
        if not pro:
            return
        
        try:
            df = pro.stock_basic(exchange='', list_status='L')
            if df is not None and not df.empty:
                count = 0
                for _, row in df.iterrows():
                    data = row.to_dict()
                    db_manager.upsert_stock_basic(data)
                    count += 1
                print(f"  股票基本信息: 同步 {count} 条")
        except Exception as e:
            print(f"  股票基本信息同步失败: {e}")
    
    def sync_daily(self, trade_date: str = None):
        """同步日线数据"""
        if not pro:
            return
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            # 获取交易日
            cal_df = pro.trade_cal(exchange='SSE', start_date=trade_date, end_date=trade_date)
            if cal_df is not None and not cal_df.empty and cal_df.iloc[0]['is_open'] == 0:
                print(f"  日线数据: {trade_date} 非交易日，跳过")
                return
            
            # 同步关注股票
            for ts_code in WATCH_LIST:
                df = pro.daily(ts_code=ts_code, start_date=trade_date, end_date=trade_date)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        db_manager.upsert_stock_daily(row.to_dict())
                    print(f"  日线数据: 同步 {ts_code}")
        except Exception as e:
            print(f"  日线数据同步失败: {e}")
    
    def sync_realtime(self):
        """同步实时行情"""
        try:
            # 使用Tushare实时行情接口
            for ts_code in WATCH_LIST:
                code = ts_code.split('.')[0]
                df = ts.get_realtime_quotes(code)
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    data = {
                        'ts_code': ts_code,
                        'name': row['name'],
                        'price': float(row['price']),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'pre_close': float(row['pre_close']),
                        'change': float(row['change']),
                        'pct_chg': float(row['pct_chg']),
                        'vol': float(row['volume']),
                        'amount': float(row['amount']),
                        'bid': float(row['bid_p']),
                        'ask': float(row['ask_p']),
                        'bid_vol': float(row['bid_v']),
                        'ask_vol': float(row['ask_v']),
                    }
                    db_manager.insert_stock_realtime(data)
                    print(f"  实时行情: 同步 {ts_code} - {data['price']}")
        except Exception as e:
            print(f"  实时行情同步失败: {e}")
    
    def sync_moneyflow(self, trade_date: str = None):
        """同步资金流向"""
        if not pro:
            return
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            for ts_code in WATCH_LIST:
                df = pro.moneyflow(ts_code=ts_code, start_date=trade_date, end_date=trade_date)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        data = row.to_dict()
                        # 计算净流入
                        if 'net_amount' not in data:
                            net_elg = data.get('net_elg_amount', 0) or 0
                            net_lg = data.get('net_lg_amount', 0) or 0
                            net_md = data.get('net_md_amount', 0) or 0
                            net_sm = data.get('net_sm_amount', 0) or 0
                            data['net_amount'] = net_elg + net_lg + net_md + net_sm
                        db_manager.upsert_stock_moneyflow(data)
                    print(f"  资金流向: 同步 {ts_code}")
        except Exception as e:
            print(f"  资金流向同步失败: {e}")
    
    def sync_index(self, trade_date: str = None):
        """同步大盘指数"""
        if not pro:
            return
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH']
        
        try:
            for code in index_codes:
                df = pro.index_daily(ts_code=code, start_date=trade_date, end_date=trade_date)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        db_manager.upsert_stock_daily(row.to_dict())
                    print(f"  大盘指数: 同步 {code}")
        except Exception as e:
            print(f"  大盘指数同步失败: {e}")
    
    def sync_northbound(self, trade_date: str = None):
        """同步北向资金"""
        if not pro:
            return
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = pro.moneyflow_hsgt(start_date=trade_date, end_date=trade_date)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    data = row.to_dict()
                    db_manager.upsert_stock_basic({
                        'ts_code': 'northbound',
                        'trade_date': trade_date,
                        'north_money': data.get('north_money', 0),
                        'south_money': data.get('south_money', 0),
                    })
                print(f"  北向资金: 同步完成")
        except Exception as e:
            print(f"  北向资金同步失败: {e}")
    
    def sync_limit_stocks(self, trade_date: str = None):
        """同步涨跌停股票"""
        if not pro:
            return
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            # 涨停
            df_up = pro.limit_list_d(trade_date=trade_date, limit_type='U')
            if df_up is not None and not df_up.empty:
                data_list = []
                for _, row in df_up.iterrows():
                    data = row.to_dict()
                    data['limit_type'] = 'U'
                    data_list.append(data)
                db_manager.batch_insert_limit_stocks(data_list)
                print(f"  涨停股票: 同步 {len(data_list)} 条")
            
            # 跌停
            df_down = pro.limit_list_d(trade_date=trade_date, limit_type='D')
            if df_down is not None and not df_down.empty:
                data_list = []
                for _, row in df_down.iterrows():
                    data = row.to_dict()
                    data['limit_type'] = 'D'
                    data_list.append(data)
                db_manager.batch_insert_limit_stocks(data_list)
                print(f"  跌停股票: 同步 {len(data_list)} 条")
        except Exception as e:
            print(f"  涨跌停股票同步失败: {e}")


# ── 全局同步服务实例 ─────────────────────────────────────────────

sync_service = DataSyncService()


# ── 快捷函数 ──────────────────────────────────────────────────────

def sync_and_push(channel: str, data: Any):
    """同步数据并推送到WebSocket"""
    broadcast_to_room(channel, {
        'type': channel,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("数据同步服务")
    print("=" * 60)
    
    # 初始化数据库
    try:
        db_manager.init_db()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        exit(1)
    
    # 执行一次全量同步
    print("\n执行全量同步...")
    sync_service.sync_all()
    
    # 启动定时同步
    print(f"\n启动定时同步，间隔: {SYNC_INTERVAL}秒")
    sync_service.start()
    
    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止同步服务...")
        sync_service.stop()