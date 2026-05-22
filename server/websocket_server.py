#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket实时推送服务
提供盘中数据实时更新功能，支持以下推送通道：
- market_index: 大盘指数实时更新
- stock_realtime: 个股实时行情
- limit_up: 涨停板动态
- moneyflow: 资金流向更新
- news: 新闻推送
- system: 系统通知
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

from database import db_manager

load_dotenv()

# ── 配置 ──────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'short-win-ai-trader-secret')
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# ── 房间管理 ──────────────────────────────────────────────────────

# 订阅管理: {room_name: {sid: client_info}}
_subscriptions: Dict[str, Dict[str, Dict]] = defaultdict(dict)

# 客户端信息: {sid: {rooms: [], info: {}}}
_clients: Dict[str, Dict] = {}


def _add_client_to_room(sid: str, room: str, client_info: Dict = None):
    """添加客户端到房间"""
    join_room(room, sid=sid)
    _subscriptions[room][sid] = client_info or {}
    if sid in _clients:
        _clients[sid]['rooms'].add(room)
    else:
        _clients[sid] = {'rooms': {room}, 'info': client_info or {}}


def _remove_client_from_room(sid: str, room: str):
    """从房间移除客户端"""
    leave_room(room, sid=sid)
    if room in _subscriptions:
        _subscriptions[room].pop(sid, None)
    if sid in _clients:
        _clients[sid]['rooms'].discard(room)


def get_room_subscribers(room: str) -> int:
    """获取房间订阅数"""
    return len(_subscriptions.get(room, {}))


# ── 消息广播 ──────────────────────────────────────────────────────

def broadcast_to_room(room: str, data: Dict, exclude_sids: List[str] = None):
    """向房间广播消息"""
    if exclude_sids:
        for sid, client_info in _subscriptions.get(room, {}).items():
            if sid not in exclude_sids:
                socketio.emit(room, data, room=room, skip_sid=sid)
    else:
        socketio.emit(room, data, room=room)


def broadcast_to_all(event: str, data: Dict):
    """向所有客户端广播"""
    socketio.emit(event, data)


def send_to_client(sid: str, event: str, data: Dict):
    """向特定客户端发送消息"""
    socketio.emit(event, data, room=sid)


# ── WebSocket事件处理 ────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    sid = request.sid
    _clients[sid] = {'rooms': set(), 'info': {}, 'connected_at': datetime.now()}
    print(f"客户端连接: {sid}")
    
    # 发送欢迎消息
    emit('system', {
        'type': 'connected',
        'message': '连接成功',
        'sid': sid,
        'timestamp': datetime.now().isoformat()
    })
    
    # 自动加入默认房间
    default_rooms = ['market_index', 'system']
    for room in default_rooms:
        _add_client_to_room(sid, room)
    
    emit('system', {
        'type': 'subscribed',
        'rooms': default_rooms,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    sid = request.sid
    client = _clients.pop(sid, None)
    
    # 清理所有订阅
    if client:
        for room in client.get('rooms', set()):
            _remove_client_from_room(sid, room)
    
    print(f"客户端断开: {sid}")


@socketio.on('subscribe')
def handle_subscribe(data):
    """订阅频道"""
    sid = request.sid
    rooms = data.get('rooms', [])
    
    if isinstance(rooms, str):
        rooms = [rooms]
    
    subscribed_rooms = []
    for room in rooms:
        if room in ['market_index', 'stock_realtime', 'limit_up', 'limit_down', 
                    'moneyflow', 'news', 'system', 'northbound']:
            _add_client_to_room(sid, room, data)
            subscribed_rooms.append(room)
    
    emit('system', {
        'type': 'subscribed',
        'rooms': subscribed_rooms,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"客户端 {sid} 订阅: {subscribed_rooms}")


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """取消订阅"""
    sid = request.sid
    rooms = data.get('rooms', [])
    
    if isinstance(rooms, str):
        rooms = [rooms]
    
    unsubscribed_rooms = []
    for room in rooms:
        _remove_client_from_room(sid, room)
        unsubscribed_rooms.append(room)
    
    emit('system', {
        'type': 'unsubscribed',
        'rooms': unsubscribed_rooms,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('get_realtime')
def handle_get_realtime(data):
    """获取实时行情"""
    sid = request.sid
    ts_codes = data.get('ts_codes', [])
    
    results = []
    for code in ts_codes:
        latest = db_manager.get_latest_realtime(code)
        if latest:
            results.append(latest)
    
    emit('realtime_response', {
        'data': results,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('ping')
def handle_ping(data):
    """心跳响应"""
    emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'server_time': int(time.time())
    })


# ── 数据推送任务 ──────────────────────────────────────────────────

class DataPusher:
    """数据推送器"""
    
    def __init__(self):
        self._running = False
        self._threads: List[threading.Thread] = []
        self._intervals = {
            'market_index': 3,      # 大盘指数3秒更新
            'stock_realtime': 5,    # 个股行情5秒更新
            'limit_up': 10,         # 涨停板10秒更新
            'moneyflow': 30,        # 资金流向30秒更新
            'northbound': 60,       # 北向资金60秒更新
        }
    
    def start(self):
        """启动推送服务"""
        if self._running:
            return
        
        self._running = True
        
        # 启动各个推送线程
        for channel, interval in self._intervals.items():
            thread = threading.Thread(
                target=self._push_loop,
                args=(channel, interval),
                daemon=True
            )
            thread.start()
            self._threads.append(thread)
        
        print(f"数据推送服务已启动，通道: {list(self._intervals.keys())}")
    
    def stop(self):
        """停止推送服务"""
        self._running = False
        for thread in self._threads:
            thread.join(timeout=5)
        self._threads.clear()
        print("数据推送服务已停止")
    
    def _push_loop(self, channel: str, interval: int):
        """推送循环"""
        while self._running:
            try:
                if get_room_subscribers(channel) > 0:
                    data = self._fetch_channel_data(channel)
                    if data:
                        broadcast_to_room(channel, {
                            'type': channel,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                print(f"推送错误 [{channel}]: {e}")
            
            time.sleep(interval)
    
    def _fetch_channel_data(self, channel: str) -> Optional[Any]:
        """获取通道数据"""
        try:
            if channel == 'market_index':
                return self._get_market_index()
            elif channel == 'stock_realtime':
                return self._get_stock_realtime()
            elif channel == 'limit_up':
                return self._get_limit_up()
            elif channel == 'moneyflow':
                return self._get_moneyflow()
            elif channel == 'northbound':
                return self._get_northbound()
        except Exception as e:
            print(f"获取数据错误 [{channel}]: {e}")
        return None
    
    def _get_market_index(self) -> List[Dict]:
        """获取大盘指数"""
        from database import IndexDaily
        with db_manager.get_session() as session:
            # 获取最新的大盘指数数据
            indices = session.query(IndexDaily).order_by(
                IndexDaily.trade_date.desc()
            ).limit(10).all()
            return [i.__dict__ for i in indices]
    
    def _get_stock_realtime(self) -> List[Dict]:
        """获取个股实时行情"""
        from database import StockRealtime
        with db_manager.get_session() as session:
            # 获取最新的实时行情
            now = datetime.now()
            realtime = session.query(StockRealtime).order_by(
                StockRealtime.timestamp.desc()
            ).limit(50).all()
            return [r.__dict__ for r in realtime]
    
    def _get_limit_up(self) -> List[Dict]:
        """获取涨停板数据"""
        from database import LimitStock
        from datetime import date
        today = date.today().strftime('%Y%m%d')
        return db_manager.get_limit_stocks(today, 'U')
    
    def _get_moneyflow(self) -> List[Dict]:
        """获取资金流向"""
        from database import StockMoneyflow
        with db_manager.get_session() as session:
            mfs = session.query(StockMoneyflow).order_by(
                StockMoneyflow.trade_date.desc()
            ).limit(20).all()
            return [m.__dict__ for m in mfs]
    
    def _get_northbound(self) -> List[Dict]:
        """获取北向资金"""
        from database import NorthboundFlow
        with db_manager.get_session() as session:
            flows = session.query(NorthboundFlow).order_by(
                NorthboundFlow.trade_date.desc()
            ).limit(10).all()
            return [f.__dict__ for f in flows]


# 全局推送器实例
pusher = DataPusher()


# ── HTTP API ──────────────────────────────────────────────────────

@app.route('/api/ws/stats', methods=['GET'])
def get_ws_stats():
    """获取WebSocket统计信息"""
    return {
        'code': 0,
        'data': {
            'connected_clients': len(_clients),
            'rooms': {
                room: len(subs) 
                for room, subs in _subscriptions.items() 
                if len(subs) > 0
            },
            'pusher_running': pusher._running
        }
    }


@app.route('/api/ws/broadcast', methods=['POST'])
def manual_broadcast():
    """手动广播消息"""
    data = request.get_json()
    event = data.get('event', 'system')
    message = data.get('message', '')
    room = data.get('room')
    
    if room:
        broadcast_to_room(room, {'type': event, 'message': message})
    else:
        broadcast_to_all(event, {'message': message})
    
    return {'code': 0, 'msg': '广播成功'}


# ── 启动服务 ──────────────────────────────────────────────────────

def create_app():
    """创建应用（用于WSGI服务器）"""
    return app


if __name__ == '__main__':
    print("=" * 60)
    print("WebSocket 实时推送服务")
    print("=" * 60)
    print(f"服务地址: http://localhost:5001")
    print(f"WebSocket: ws://localhost:5001")
    print(f"统计接口: http://localhost:5001/api/ws/stats")
    print("=" * 60)
    
    # 初始化数据库
    try:
        db_manager.init_db()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
    
    # 启动推送服务
    pusher.start()
    
    # 启动WebSocket服务
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False
    )