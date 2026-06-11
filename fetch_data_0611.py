#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取2026-06-11实际收盘数据并更新数据文件"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

def fetch_market_data():
    """获取市场数据"""
    # 获取A股实时行情
    df = ak.stock_zh_a_spot_em()
    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['最新价'] = pd.to_numeric(df['最新价'], errors='coerce')
    df['成交量'] = pd.to_numeric(df['成交量'], errors='coerce')
    df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
    df['量比'] = pd.to_numeric(df['量比'], errors='coerce')
    
    # 涨停股（涨跌幅>=9.8%）
    limit_up = df[df['涨跌幅'] >= 9.8].sort_values('涨跌幅', ascending=False)
    
    # 跌停股
    limit_down = df[df['涨跌幅'] <= -9.8].sort_values('涨跌幅')
    
    # 上涨/下跌家数
    up_count = len(df[df['涨跌幅'] > 0])
    down_count = len(df[df['涨跌幅'] < 0])
    
    # 成交额（亿）
    total_amount = df['成交额'].sum() / 100000000
    
    print("=" * 60)
    print("2026-06-11 市场数据")
    print("=" * 60)
    print(f"上涨: {up_count}家")
    print(f"下跌: {down_count}家")
    print(f"涨停: {len(limit_up)}家")
    print(f"跌停: {len(limit_down)}家")
    print(f"总成交额: {total_amount:.0f}亿")
    
    print("\n" + "=" * 60)
    print("涨停股TOP20:")
    print("=" * 60)
    
    for i, row in limit_up.head(20).iterrows():
        print(f"{row['代码']} {row['名称']} {row['最新价']}元 {row['涨跌幅']}% 量比{row.get('量比', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("跌停股TOP10:")
    print("=" * 60)
    
    for i, row in limit_down.head(10).iterrows():
        print(f"{row['代码']} {row['名称']} {row['最新价']}元 {row['涨跌幅']}%")
    
    # 获取指数数据
    print("\n" + "=" * 60)
    print("指数数据:")
    print("=" * 60)
    
    # 上证指数
    sh = ak.stock_zh_index_daily(symbol="sh000001")
    print(f"上证指数最新: {sh['close'].iloc[-1]:.2f}")
    
    # 深证成指
    sz = ak.stock_zh_index_daily(symbol="sz399001")
    print(f"深证成指最新: {sz['close'].iloc[-1]:.2f}")
    
    # 创业板指
    cy = ak.stock_zh_index_daily(symbol="sz399006")
    print(f"创业板指最新: {cy['close'].iloc[-1]:.2f}")
    
    return limit_up, limit_down, up_count, down_count, total_amount

if __name__ == "__main__":
    fetch_market_data()