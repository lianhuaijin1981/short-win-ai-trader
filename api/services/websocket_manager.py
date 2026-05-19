"""WebSocket 实时推送服务

为前端提供实时数据推送:
1. 市场数据实时更新
2. 情绪周期变化通知
3. 涨停板动态
4. 资金流向变化
5. 预警消息推送
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

from api.core.logger import get_logger

logger = get_logger("swat.websocket")


class ConnectionManager:
    """WebSocket 连接管理"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.discard(websocket)
        # 从所有频道移除
        for channel, subscribers in self.channel_subscriptions.items():
            subscribers.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, channel: str):
        """订阅频道"""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(websocket)
        logger.debug(f"WebSocket subscribed to {channel}")
    
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消订阅"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(websocket)
    
    async def send_to(self, websocket: WebSocket, data: dict):
        """发送数据到指定连接"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: dict, channel: Optional[str] = None):
        """广播数据"""
        message = {
            "type": "broadcast",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        
        if channel:
            targets = self.channel_subscriptions.get(channel, set()).copy()
        else:
            targets = self.active_connections.copy()
        
        disconnected = set()
        for websocket in targets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Broadcast failed to one client: {e}")
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_heartbeat(self):
        """发送心跳"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
        }
        
        disconnected = set()
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


class WebSocketService:
    """WebSocket 服务"""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._data_push_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动 WebSocket 服务"""
        if self._running:
            return
        
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._data_push_task = asyncio.create_task(self._data_push_loop())
        logger.info("WebSocketService started")
    
    async def stop(self):
        """停止 WebSocket 服务"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._data_push_task:
            self._data_push_task.cancel()
        logger.info("WebSocketService stopped")
    
    async def handle_connection(self, websocket: WebSocket, channel: str = "all"):
        """处理 WebSocket 连接"""
        await self.manager.connect(websocket)
        self.manager.subscribe(websocket, channel)
        
        # 发送欢迎消息
        await self.manager.send_to(websocket, {
            "type": "welcome",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to SWAT real-time data feed",
        })
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await self._handle_message(websocket, message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {data}")
        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.manager.disconnect(websocket)
    
    async def _handle_message(self, websocket: WebSocket, message: dict):
        """处理客户端消息"""
        msg_type = message.get("type", "")
        
        if msg_type == "subscribe":
            channel = message.get("channel", "")
            if channel:
                self.manager.subscribe(websocket, channel)
                await self.manager.send_to(websocket, {
                    "type": "subscribed",
                    "channel": channel,
                })
        
        elif msg_type == "unsubscribe":
            channel = message.get("channel", "")
            if channel:
                self.manager.unsubscribe(websocket, channel)
                await self.manager.send_to(websocket, {
                    "type": "unsubscribed",
                    "channel": channel,
                })
        
        elif msg_type == "ping":
            await self.manager.send_to(websocket, {
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
            })
    
    async def push_data(self, channel: str, data: dict):
        """推送数据到指定频道"""
        await self.manager.broadcast(data, channel=channel)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await self.manager.send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(30)  # 30秒心跳
    
    async def _data_push_loop(self):
        """数据推送循环"""
        from api.services.data_sync import data_sync_service
        
        while self._running:
            try:
                # 推送市场总览
                market_data = data_sync_service.cache.get("market_overview", ttl=60)
                if market_data:
                    await self.push_data("market", market_data)
                
                # 推送涨停板
                limit_up_data = data_sync_service.cache.get("limit_up", ttl=120)
                if limit_up_data:
                    await self.push_data("limit_up", limit_up_data)
                
                # 推送情绪
                sentiment_data = data_sync_service.cache.get("sentiment", ttl=180)
                if sentiment_data:
                    await self.push_data("sentiment", sentiment_data)
                
                # 推送资金流向
                fund_flow_data = data_sync_service.cache.get("fund_flow", ttl=60)
                if fund_flow_data:
                    await self.push_data("fund_flow", fund_flow_data)
                
            except Exception as e:
                logger.error(f"Data push error: {e}")
            
            await asyncio.sleep(10)  # 10秒推送一次


# 全局实例
websocket_service = WebSocketService()