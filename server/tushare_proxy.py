#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 数据代理服务
用于前端调用Tushare API，避免暴露Token

安装依赖:
pip install flask flask-cors tushare python-dotenv

使用方法:
1. 设置环境变量 TUSHARE_TOKEN
2. 运行: python tushare_proxy.py
3. 前端配置 VITE_TUSHARE_API_BASE=http://localhost:5000/api
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import tushare as ts
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ── 配置 ────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# Tushare Token配置
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
if not TUSHARE_TOKEN:
    print("警告: 未设置 TUSHARE_TOKEN 环境变量")
    print("请设置: export TUSHARE_TOKEN=your_token_here")

# 初始化Tushare
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 数据缓存
_cache = {}
CACHE_EXPIRE = 60  # 缓存过期时间（秒）

# ── 工具函数 ────────────────────────────────────────────────────

def get_cached(key: str, expire: int = CACHE_EXPIRE) -> Optional[dict]:
    """获取缓存数据"""
    if key in _cache:
        data, timestamp = _cache[key]
        if (datetime.now() - timestamp).seconds < expire:
            return data
        del _cache[key]
    return None

def set_cache(key: str, data: dict):
    """设置缓存"""
    _cache[key] = (data, datetime.now())

def df_to_list(df) -> list:
    """将DataFrame转换为列表格式"""
    if df is None or df.empty:
        return []
    return df.to_dict('records')

def error_response(msg: str, code: int = -1) -> dict:
    """错误响应"""
    return {'code': code, 'msg': msg, 'data': None}

def success_response(data: dict) -> dict:
    """成功响应"""
    return {'code': 0, 'msg': 'OK', 'data': data}

# ── 健康检查 ────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Tushare Proxy',
        'timestamp': datetime.now().isoformat()
    })

# ── Tushare API 代理 ───────────────────────────────────────────

@app.route('/api/tushare', methods=['POST'])
def tushare_proxy():
    """
    Tushare API 统一代理接口
    请求体:
    {
        "api_name": "daily",
        "token": "your_token",
        "params": {"ts_code": "000001.SZ", "start_date": "20260101"},
        "fields": "ts_code,trade_date,open,high,low,close"
    }
    """
    try:
        body = request.get_json()
        if not body:
            return jsonify(error_response('请求体不能为空')), 400

        api_name = body.get('api_name')
        if not api_name:
            return jsonify(error_response('api_name不能为空')), 400

        params = body.get('params', {})
        fields = body.get('fields', '')

        # 缓存键
        cache_key = f"{api_name}:{str(params)}:{fields}"
        cached = get_cached(cache_key)
        if cached:
            return jsonify(success_response(cached))

        # 调用Tushare API
        result = call_tushare_api(api_name, params, fields)
        
        if result is not None:
            set_cache(cache_key, result)
            return jsonify(success_response(result))
        else:
            return jsonify(error_response(f'API调用失败: {api_name}')), 500

    except Exception as e:
        return jsonify(error_response(f'服务器错误: {str(e)}')), 500

def call_tushare_api(api_name: str, params: dict, fields: str = '') -> dict:
    """
    调用Tushare API
    支持所有Tushare接口
    """
    try:
        # 根据api_name调用对应的接口
        api_func = getattr(pro, api_name, None)
        if api_func is None:
            return {'fields': [], 'items': []}

        # 调用API
        df = api_func(**params)
        
        if df is None or df.empty:
            return {'fields': [], 'items': []}

        # 如果指定了fields，只返回指定字段
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [f for f in field_list if f in df.columns]
            df = df[available_fields]
        else:
            available_fields = list(df.columns)

        # 转换为Tushare标准格式
        items = []
        for _, row in df.iterrows():
            item = [row.get(f) for f in available_fields]
            items.append(item)

        return {
            'fields': available_fields,
            'items': items
        }

    except Exception as e:
        print(f"Tushare API调用失败 [{api_name}]: {str(e)}")
        return {'fields': [], 'items': []}

# ── 快捷接口 ────────────────────────────────────────────────────

@app.route('/api/stock/daily/<ts_code>', methods=['GET'])
def get_stock_daily(ts_code: str):
    """获取个股日线行情"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y%m%d'))
    
    cache_key = f"daily:{ts_code}:{start_date}:{end_date}"
    cached = get_cached(cache_key)
    if cached:
        return jsonify(success_response(cached))
    
    try:
        params = {'ts_code': ts_code}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        df = pro.daily(**params)
        result = df_to_list(df)
        set_cache(cache_key, result)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/stock/realtime/<ts_code>', methods=['GET'])
def get_stock_realtime(ts_code: str):
    """获取实时行情"""
    try:
        df = ts.get_realtime_quotes(ts_code.split('.')[0])
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/market/index', methods=['GET'])
def get_market_index():
    """获取大盘指数"""
    try:
        index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH', '000688.SH']
        results = []
        for code in index_codes:
            df = pro.index_daily(ts_code=code, limit=1)
            if df is not None and not df.empty:
                results.append(df.iloc[0].to_dict())
        return jsonify(success_response(results))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/market/breadth/<trade_date>', methods=['GET'])
def get_market_breadth(trade_date: str):
    """获取市场广度（涨跌家数）"""
    try:
        # 获取涨跌股票数
        df = pro.index_daily(ts_code='000001.SH', start_date=trade_date, end_date=trade_date)
        if df is not None and not df.empty:
            return jsonify(success_response(df.iloc[0].to_dict()))
        return jsonify(success_response({}))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/stock/moneyflow/<ts_code>', methods=['GET'])
def get_stock_moneyflow(ts_code: str):
    """获取个股资金流向"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y%m%d'))
    
    try:
        params = {'ts_code': ts_code}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        df = pro.moneyflow(**params)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/stock/basic', methods=['GET'])
def get_stock_basic():
    """获取股票基本信息"""
    ts_code = request.args.get('ts_code', '')
    
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        
        df = pro.stock_basic(**params)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/sector/limit_up/<trade_date>', methods=['GET'])
def get_limit_up_list(trade_date: str):
    """获取涨停板列表"""
    try:
        df = pro.limit_list_d(trade_date=trade_date, limit_type='U')
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/sector/limit_down/<trade_date>', methods=['GET'])
def get_limit_down_list(trade_date: str):
    """获取跌停板列表"""
    try:
        df = pro.limit_list_d(trade_date=trade_date, limit_type='D')
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/northbound/flow', methods=['GET'])
def get_northbound_flow():
    """获取北向资金流向"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y%m%d'))
    
    try:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        df = pro.moneyflow_hsgt(**params)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/stock/kline/<ts_code>', methods=['GET'])
def get_stock_kline(ts_code: str):
    """获取K线数据"""
    freq = request.args.get('freq', 'D')
    count = request.args.get('count', 100, type=int)
    
    try:
        df = ts.pro_bar(ts_code=ts_code, freq=freq, adj='qfq', count=count)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/stock/indicator/<ts_code>', methods=['GET'])
def get_stock_indicator(ts_code: str):
    """获取技术指标"""
    try:
        df = pro.stk_factor(ts_code=ts_code)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/news/list', methods=['GET'])
def get_news_list():
    """获取新闻列表"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y%m%d'))
    
    try:
        # 使用新闻快讯接口
        df = pro.news(start_date=start_date, end_date=end_date)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

@app.route('/api/calendar', methods=['GET'])
def get_trade_calendar():
    """获取交易日历"""
    exchange = request.args.get('exchange', 'SSE')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    try:
        params = {'exchange': exchange}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        df = pro.trade_cal(**params)
        result = df_to_list(df)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(str(e))), 500

# ── 启动服务 ────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("Tushare 数据代理服务")
    print("=" * 50)
    print(f"服务地址: http://localhost:5000")
    print(f"API代理: http://localhost:5000/api/tushare")
    print(f"健康检查: http://localhost:5000/api/health")
    print("=" * 50)
    
    # 检查Token
    if not TUSHARE_TOKEN:
        print("⚠️  警告: 未设置 TUSHARE_TOKEN")
        print("请前往 https://tushare.pro 注册并获取Token")
        print("设置方法: export TUSHARE_TOKEN=your_token")
    
    app.run(host='0.0.0.0', port=5000, debug=True)