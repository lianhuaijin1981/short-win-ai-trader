# WebSocket实时推送 & PostgreSQL持久化 使用指南

## 概述

本文档介绍短线AI交易系统的WebSocket实时推送和PostgreSQL数据库持久化功能。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  useWebSocket Hook                                        │   │
│  │  - 自动连接/重连                                          │   │
│  │  - 频道订阅/取消订阅                                      │   │
│  │  - 消息处理                                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                     WebSocket (Socket.IO)                        │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                     后端 (Python Flask)                          │
│  ┌───────────────────────────┼──────────────────────────────┐   │
│  │  WebSocket Server         │                              │   │
│  │  - 房间管理               │  Data Sync Service           │   │
│  │  - 消息广播               │  - Tushare数据获取           │   │
│  │  - 心跳检测               │  - PostgreSQL数据存储        │   │
│  │                           │  - 定时同步                  │   │
│  └───────────────────────────┼──────────────────────────────┘   │
│                              │                                   │
│                     SQLAlchemy ORM                               │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                    PostgreSQL 数据库                              │
│  ┌───────────────────────────┼──────────────────────────────┐   │
│  │  - stock_basic (股票基本信息)                              │   │
│  │  - stock_daily (日线行情)                                  │   │
│  │  - stock_realtime (实时行情)                               │   │
│  │  - stock_moneyflow (资金流向)                              │   │
│  │  - index_daily (大盘指数)                                  │   │
│  │  - limit_stocks (涨跌停)                                   │   │
│  │  - northbound_flow (北向资金)                              │   │
│  │  - trade_records (交易记录)                                │   │
│  │  - trade_journal (交易日志)                                │   │
│  │  - news_records (新闻记录)                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 一、环境准备

### 1.1 安装PostgreSQL

```bash
# Windows (使用Chocolatey)
choco install postgresql

# 或使用安装包
# https://www.postgresql.org/download/windows/
```

### 1.2 创建数据库

```sql
-- 连接PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE short_win_trader;

-- 创建用户（可选）
CREATE USER trader WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE short_win_trader TO trader;
```

### 1.3 安装Python依赖

```bash
cd server
pip install -r requirements.txt
```

### 1.4 配置环境变量

复制 `.env.example` 为 `.env.local`：

```bash
# 前端配置
VITE_WS_URL=http://localhost:5001

# 后端数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/short_win_trader

# Tushare配置
TUSHARE_TOKEN=your_tushare_token

# 同步间隔（秒）
SYNC_INTERVAL=300

# 关注股票列表
WATCH_LIST=000001.SZ,600000.SH,000002.SZ,600519.SH,000858.SZ
```

## 二、启动服务

### 2.1 启动WebSocket服务

```bash
cd server
python websocket_server.py
```

服务启动后：
- HTTP API: http://localhost:5001
- WebSocket: ws://localhost:5001
- 统计接口: http://localhost:5001/api/ws/stats

### 2.2 启动数据同步服务（可选）

```bash
cd server
python data_sync.py
```

### 2.3 启动前端

```bash
npm run dev
```

## 三、WebSocket频道

### 3.1 支持的频道

| 频道名 | 说明 | 推送间隔 |
|--------|------|----------|
| market_index | 大盘指数 | 3秒 |
| stock_realtime | 个股实时行情 | 5秒 |
| limit_up | 涨停板动态 | 10秒 |
| limit_down | 跌停板动态 | 10秒 |
| moneyflow | 资金流向 | 30秒 |
| northbound | 北向资金 | 60秒 |
| news | 新闻推送 | 实时 |
| system | 系统通知 | 事件触发 |

### 3.2 前端使用示例

```tsx
import { useWebSocket, ChannelType } from '../services/websocket';

function MyComponent() {
  const {
    connected,
    subscribe,
    unsubscribe,
    lastMessages,
  } = useWebSocket({
    channels: ['market_index'],
    autoConnect: true,
    onMessage: (channel, data) => {
      console.log(`收到${channel}消息:`, data);
    },
  });

  // 订阅更多频道
  const handleSubscribe = () => {
    subscribe(['stock_realtime', 'moneyflow']);
  };

  return (
    <div>
      <p>连接状态: {connected ? '已连接' : '未连接'}</p>
      <button onClick={handleSubscribe}>订阅实时行情</button>
      
      {/* 显示最新大盘指数 */}
      {lastMessages.market_index?.data && (
        <div>
          最新指数: {JSON.stringify(lastMessages.market_index.data)}
        </div>
      )}
    </div>
  );
}
```

### 3.3 直接使用客户端

```ts
import { wsClient } from '../services/websocket';

// 连接
await wsClient.connect();

// 订阅
wsClient.subscribe(['market_index', 'stock_realtime']);

// 添加消息处理器
wsClient.on('market_index', (data) => {
  console.log('大盘指数更新:', data);
});

// 获取实时行情
wsClient.getRealtime(['000001.SZ', '600000.SH']);

// 断开
wsClient.disconnect();
```

## 四、数据库模型

### 4.1 股票基本信息 (stock_basic)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | VARCHAR(20) | 股票代码 |
| symbol | VARCHAR(20) | 股票代码 |
| name | VARCHAR(50) | 股票名称 |
| area | VARCHAR(20) | 所在地域 |
| industry | VARCHAR(30) | 所属行业 |
| market | VARCHAR(20) | 市场类型 |
| list_date | VARCHAR(20) | 上市日期 |

### 4.2 日线行情 (stock_daily)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | VARCHAR(20) | 股票代码 |
| trade_date | VARCHAR(20) | 交易日期 |
| open | FLOAT | 开盘价 |
| high | FLOAT | 最高价 |
| low | FLOAT | 最低价 |
| close | FLOAT | 收盘价 |
| pct_chg | FLOAT | 涨跌幅% |
| vol | FLOAT | 成交量 |
| amount | FLOAT | 成交额 |

### 4.3 实时行情 (stock_realtime)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | VARCHAR(20) | 股票代码 |
| price | FLOAT | 当前价 |
| change | FLOAT | 涨跌额 |
| pct_chg | FLOAT | 涨跌幅% |
| vol | FLOAT | 成交量 |
| timestamp | DATETIME | 时间戳 |

### 4.4 资金流向 (stock_moneyflow)

| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | VARCHAR(20) | 股票代码 |
| trade_date | VARCHAR(20) | 交易日期 |
| net_elg_amount | FLOAT | 超大单净流入 |
| net_lg_amount | FLOAT | 大单净流入 |
| net_md_amount | FLOAT | 中单净流入 |
| net_sm_amount | FLOAT | 小单净流入 |
| net_amount | FLOAT | 总净流入 |

## 五、数据库操作

### 5.1 使用DatabaseManager

```python
from database import db_manager

# 初始化数据库
db_manager.init_db()

# 插入股票基本信息
db_manager.upsert_stock_basic({
    'ts_code': '000001.SZ',
    'symbol': '000001',
    'name': '平安银行',
    'industry': '银行',
})

# 查询日线数据
daily_data = db_manager.get_stock_daily(
    ts_code='000001.SZ',
    start_date='20260101',
    limit=30
)

# 搜索股票
results = db_manager.search_stocks('平安')

# 获取每日统计
stats = db_manager.get_daily_stats('20260522')
```

### 5.2 HTTP API

```bash
# 获取WebSocket统计
curl http://localhost:5001/api/ws/stats

# 手动广播消息
curl -X POST http://localhost:5001/api/ws/broadcast \
  -H "Content-Type: application/json" \
  -d '{"event": "system", "message": "系统维护通知"}'
```

## 六、使用示例组件

项目中包含了一个实时数据监控示例组件：

```tsx
import RealtimeMonitor from '../components/RealtimeMonitor';

function App() {
  return (
    <RealtimeMonitor 
      watchList={['000001.SZ', '600000.SH', '000002.SZ']}
      showLog={true}
    />
  );
}
```

## 七、故障排查

### 7.1 WebSocket连接失败

1. 检查WebSocket服务是否启动
2. 检查端口5001是否被占用
3. 检查防火墙设置
4. 查看浏览器控制台错误信息

### 7.2 数据库连接失败

```bash
# 测试数据库连接
cd server
python -c "from database import db_manager; db_manager.init_db()"
```

### 7.3 数据同步失败

1. 检查TUSHARE_TOKEN是否正确
2. 检查Tushare积分是否足够
3. 查看同步服务日志

## 八、生产部署

### 8.1 使用Gunicorn启动

```bash
pip install gunicorn gevent

gunicorn -k gevent -w 1 -b 0.0.0.0:5001 websocket_server:app
```

### 8.2 使用Supervisor管理进程

```ini
[program:ws-server]
command=/path/to/venv/bin/python websocket_server.py
directory=/path/to/server
autostart=true
autorestart=true
```

### 8.3 数据库连接池调优

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 连接池大小
    max_overflow=40,       # 最大溢出连接数
    pool_timeout=30,       # 获取连接超时时间
    pool_recycle=3600,     # 连接回收时间
    pool_pre_ping=True,    # 连接前检测
)