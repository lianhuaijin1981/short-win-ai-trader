# 短线致胜 AI 交易智能体 (Short-Win AI Trader)

A股超短线AI交易决策智能体，对接同花顺iFind历史和实时行情数据，为职业短线交易者提供全流程智能化决策支持。

## 系统架构

```
short_win_ai_trader/
├── core/                    # 核心框架（配置、日志、异常、数据管理）
├── data_platform/           # 数据中台（iFind封装、缓存、数据模型）
├── modules/                 # 七大核心业务模块
│   ├── m01_news_collector/   # 模块一：全域资讯智能采集
│   ├── m02_market_replay/    # 模块二：全维度智能复盘 + 情绪周期
│   ├── m03_intraday_watch/   # 模块三：盘中看盘（主升龙头真经）
│   ├── m04_yingyou_diagnosis/# 模块四：淘股吧游资模式诊断
│   ├── m05_tactic_screening/ # 模块五：抖音主流短线战法筛选
│   ├── m06_scoring_decision/ # 模块六：综合评分 + 智能仓位 + 交易决策
│   └── m07_trade_diagnosis/  # 模块七：交割单诊断 + 风格定位
├── cli/                     # 命令行界面
└── tests/                   # 测试套件
```

## 七大核心模块

| 模块 | 名称 | 核心功能 |
|------|------|----------|
| 模块一 | 全域资讯智能采集 | 全渠道资讯采集、回测驱动筛选、风险预警 |
| 模块二 | 全维度智能复盘 | 大盘/连板/题材/资金复盘、情绪周期研判、仓位匹配 |
| 模块三 | 盘中看盘 | 锚定标的锁定、资金轨迹追踪、板块效应预警、龙头梯队监测 |
| 模块四 | 游资模式诊断 | 8大游资数字指纹、盘面诊断、标的推荐、共识分析 |
| 模块五 | 战法筛选研判 | 15+战法规则库、智能选股、多战法共振、错配过滤 |
| 模块六 | 综合评分决策 | 6维量化评分、风险收益比、动态仓位、完整交易计划 |
| 模块七 | 交割单诊断 | 交易归因、风格画像、错题库、自定义标的研判 |

## 数据对接

- **数据源**: 同花顺iFind金融数据平台
- **覆盖范围**: A股全市场行情、财务数据、龙虎榜、公告、股东信息
- **实时能力**: 盘中实时行情推送、异动预警（3秒响应）
- **历史数据**: 近3年历史和财务数据

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 盘前分析
python -m short_win_ai_trader pre-market --date 2026-05-16

# 盘中监控
python -m short_win_ai_trader intraday --watch-interval 30

# 盘后复盘
python -m short_win_ai_trader post-market --date 2026-05-16

# 个股分析
python -m short_win_ai_trader analyze --ticker 600519.SH

# 综合评分
python -m short_win_ai_trader score --ticker 600519.SH

# 交割单诊断
python -m short_win_ai_trader diagnose --file 交割单.xlsx

# 游资诊断
python -m short_win_ai_trader yingyou --emotion-cycle 发酵期

# 战法筛选
python -m short_win_ai_trader tactics --tactic 筹码峰战法
```

## 技术栈

- Python 3.10+
- 异步框架: asyncio + aiohttp
- 数据: pandas + numpy
- 配置: Pydantic Settings
- 日志: structlog
- CLI: click + rich

## 版本

- **Version**: 1.0.0
- **Date**: 2026-05-16
- **Author**: lianhuaijin
