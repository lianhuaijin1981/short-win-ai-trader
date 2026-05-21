# Tushare 数据接入指南

## 一、Tushare 简介

Tushare 是一个免费、开源的 Python 财经数据接口包，提供：
- A股/港股/美股行情数据
- 基金/期货/期权数据
- 财务数据/宏观经济数据
- 新闻/舆情数据

**官网**: https://tushare.pro

---

## 二、注册与获取Token

### 1. 注册账号
1. 访问 https://tushare.pro/register
2. 填写邮箱、密码注册
3. 登录邮箱验证

### 2. 获取Token
1. 登录后进入"个人中心"
2. 复制你的 `token`（一串字符）
3. 妥善保管，不要公开

### 3. 积分说明
| 积分等级 | 调用频率 | 费用 |
|---------|---------|------|
| 120积分（注册默认） | 200次/分钟 | 免费 |
| 2000积分 | 500次/分钟 | 免费（需完善信息） |
| 5000积分+ | 更高频率 | 付费（约¥200-500/年） |

**建议**: 注册后完善个人信息可获得2000积分，足够日常使用。

---

## 三、快速启动

### 方式一：使用Python后端代理（推荐）

#### 1. 安装Python依赖
```bash
cd server
pip install -r requirements.txt
```

#### 2. 设置Token
```bash
# Windows CMD
set TUSHARE_TOKEN=your_token_here

# Windows PowerShell
$env:TUSHARE_TOKEN="your_token_here"

# Linux/Mac
export TUSHARE_TOKEN=your_token_here
```

或者创建 `.env` 文件：
```bash
# server/.env
TUSHARE_TOKEN=your_token_here
```

#### 3. 启动服务
```bash
cd server
python tushare_proxy.py
```

服务启动后访问: http://localhost:5000/api/health

#### 4. 配置前端
在 `.env.local` 中配置：
```env
VITE_TUSHARE_API_BASE=http://localhost:5000/api
VITE_TUSHARE_TOKEN=your_token_here
```

---

### 方式二：直接在前端调用（不推荐，会暴露Token）

仅用于测试，生产环境务必使用后端代理。

```typescript
import tushare, { codeConverter } from '@/services/tushare';

// 转换股票代码
const tsCode = codeConverter.toTushareCode('000001'); // 000001.SZ

// 获取日线数据
const bars = await tushare.market.getDailyBars(tsCode, '20260101', '20260522');

// 获取资金流向
const moneyflow = await tushare.fund.getStockMoneyFlow(tsCode, '20260101', '20260522');

// 获取涨停板列表
const limitUp = await tushare.sector.getLimitUpList('20260522');
```

---

## 四、API接口说明

### 行情数据

| 方法 | 说明 | 参数 |
|------|------|------|
| `tushare.market.getDailyBars()` | 获取日线K线 | tsCode, startDate, endDate |
| `tushare.market.getStockKline()` | 获取K线（多周期） | tsCode, period, count |
| `tushare.market.getIndexQuotes()` | 获取大盘指数 | - |
| `tushare.market.getTechnicalIndicators()` | 获取技术指标 | tsCode, indicator |

### 资金流向

| 方法 | 说明 | 参数 |
|------|------|------|
| `tushare.fund.getStockMoneyFlow()` | 个股资金流向 | tsCode, startDate, endDate |
| `tushare.fund.getNorthboundFlow()` | 北向资金 | startDate, endDate |
| `tushare.fund.getSectorMoneyFlow()` | 板块资金流向 | type, tradeDate |
| `tushare.fund.getDragonTigerList()` | 龙虎榜 | tradeDate, tsCode |

### 板块题材

| 方法 | 说明 | 参数 |
|------|------|------|
| `tushare.sector.getLimitUpList()` | 涨停板列表 | tradeDate |
| `tushare.sector.getLimitDownList()` | 跌停板列表 | tradeDate |
| `tushare.sector.getIndustryList()` | 行业板块列表 | - |
| `tushare.sector.getConceptList()` | 概念板块列表 | - |

### 基本面

| 方法 | 说明 | 参数 |
|------|------|------|
| `tushare.fundamental.getStockBasic()` | 股票基本信息 | tsCode |
| `tushare.fundamental.getDailyBasic()` | 每日指标 | tsCode, startDate, endDate |
| `tushare.fundamental.getFinanceData()` | 财务数据 | tsCode |

---

## 五、股票代码转换

Tushare使用 `ts_code` 格式，需要转换：

| 普通代码 | Tushare格式 | 市场 |
|---------|------------|------|
| 000001 | 000001.SZ | 深市 |
| 600000 | 600000.SH | 沪市 |
| 300001 | 300001.SZ | 创业板 |
| 688001 | 688001.SH | 科创板 |
| 830001 | 830001.BJ | 北交所 |

使用内置转换工具：
```typescript
import { codeConverter } from '@/services/tushare';

codeConverter.toTushareCode('000001');    // 000001.SZ
codeConverter.toTushareCode('600000');   // 600000.SH
codeConverter.fromTushareCode('000001.SZ'); // 000001
```

---

## 六、数据缓存策略

系统内置三级缓存：

```
请求 → 内存缓存 → IndexedDB缓存 → 网络请求
         ↓           ↓            ↓
       10秒-1小时   24小时       实时获取
```

缓存配置：
| 数据类型 | 内存缓存 | 持久化 |
|---------|---------|--------|
| 实时行情 | 10秒 | 否 |
| 分时数据 | 30秒 | 否 |
| 日线数据 | 1小时 | 是 |
| 基础信息 | 24小时 | 是 |
| 诊断结果 | 24小时 | 是 |

---

## 七、降级策略

当网络请求失败时：
1. 返回缓存中的旧数据
2. 返回fallback默认数据
3. 抛出错误由UI处理

```typescript
import { dataFetcher } from '@/services/dataCache';

const data = await dataFetcher.fetch({
  key: 'daily_000001.SZ',
  type: 'daily',
  fetcher: () => tushare.market.getDailyBars('000001.SZ'),
  fallback: mockData,  // 降级数据
  timeout: 10000,
});
```

---

## 八、常见问题

### Q1: 调用频率限制怎么办？
- 使用缓存减少重复请求
- 批量获取数据而非逐个请求
- 考虑升级积分

### Q2: 数据延迟多久？
- 日线数据：收盘后更新
- 实时行情：交易时间实时更新
- 资金流向：盘后更新

### Q3: 如何获取实时数据？
Tushare免费版不提供Level-2实时数据，可考虑：
- 东方财富免费API
- 新浪财经API
- 券商交易接口

### Q4: Token安全吗？
- 不要在前端代码中硬编码Token
- 使用后端代理服务
- 定期更换Token

---

## 九、费用参考

| 用途 | 积分需求 | 费用 |
|------|---------|------|
| 个人学习 | 120-2000 | 免费 |
| 原型开发 | 2000-5000 | 免费 |
| 生产环境 | 5000+ | ¥200-500/年 |
| 商业授权 | 联系官方 | 协商 |

---

## 十、替代数据源

如果Tushare不满足需求，可考虑：

| 数据源 | 特点 | 费用 |
|--------|------|------|
| AKShare | Python开源 | 免费 |
| 聚宽JQData | 量化专用 | ¥200/月起 |
| 米筐RQData | 机构级 | ¥300/月起 |
| 东方财富API | 免费HTTP | 免费 |
| 万得Wind | 专业终端 | ¥3000/月起 |