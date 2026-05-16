"""配置管理 — 使用Pydantic Settings"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class iFindConfig(BaseModel):
    """iFind数据源配置"""
    enabled: bool = True
    rate_limit: int = 10
    cache_dir: str = "./cache"
    cache_ttl: int = 300
    max_tickers_per_query: int = 10
    max_date_range_years: int = 3


class EmotionCycleConfig(BaseModel):
    """情绪周期配置"""
    default_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "market_index": 0.25,
            "board_index": 0.25,
            "fund_index": 0.25,
            "theme_index": 0.25,
        }
    )
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "high_explode_rate": 50.0,
            "high_limit_down": 10.0,
            "volume_anomaly": 30.0,
        }
    )


class PositionConfig(BaseModel):
    """仓位配置"""
    chaos_max: int = 20
    start_max: int = 40
    ferment_max: int = 60
    peak_max: int = 30
    diverge_max: int = 30
    retreat_max: int = 10
    single_stock_max: Dict[str, int] = Field(
        default_factory=lambda: {
            "chaos": 10,
            "start": 40,
            "ferment": 35,
            "peak": 20,
            "diverge": 15,
            "retreat": 5,
        }
    )


class ScoringConfig(BaseModel):
    """评分配置"""
    dimensions: Dict[str, Dict] = Field(
        default_factory=lambda: {
            "news_catalyst": {"weight": 20, "sub_weights": {"level": 0.4, "timeliness": 0.3, "strength": 0.2, "market_feedback": 0.1}},
            "fundamental": {"weight": 15, "sub_weights": {"growth": 0.35, "valuation": 0.25, "health": 0.25, "theme_purity": 0.15}},
            "technical": {"weight": 20, "sub_weights": {"ma_system": 0.3, "breakout": 0.3, "volume": 0.2, "indicators": 0.2}},
            "chip_structure": {"weight": 15, "sub_weights": {"concentration": 0.3, "lock_ratio": 0.3, "trapped_ratio": 0.2, "peak_shape": 0.2}},
            "emotion_fit": {"weight": 15, "sub_weights": {"cycle_match": 0.4, "sector_effect": 0.25, "dragon_status": 0.2, "profit_effect": 0.15}},
            "fund_flow": {"weight": 15, "sub_weights": {"main_inflow": 0.35, "dragon_bond": 0.25, "seal_strength": 0.25, "northbound": 0.15}},
        }
    )


class RiskConfig(BaseModel):
    """风控配置"""
    default_stop_loss: float = 4.0
    max_stop_loss: float = 5.0
    min_take_profit: float = 8.0
    max_take_profit: float = 20.0
    golden_take_profit: float = 15.0
    min_risk_reward: float = 1.5
    score_update_interval: int = 900
    score_trigger_threshold: int = 10


class AlertConfig(BaseModel):
    """预警配置"""
    sector_effect_threshold: int = 3
    sector_avg_open_high: float = 3.0
    sector_daily_change: float = 5.0
    fund_outflow_threshold: float = 1000000000.0
    expectation_check_interval: int = 30
    fund_summary_interval: int = 1800


class YingYouConfig(BaseModel):
    """游资配置"""
    fingerprints_file: str = "config/yingyou_fingerprints.json"
    match_score_threshold: int = 60
    update_interval: int = 900
    consensus_min_count: int = 3


class TacticsConfig(BaseModel):
    """战法配置"""
    rules_file: str = "config/tactic_rules.json"
    max_results_per_tactic: int = 5
    resonance_levels: List[str] = Field(default_factory=lambda: ["双战法共振", "三战法共振", "多战法强共振"])


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    file: str = "logs/swat.log"
    max_size: int = 10485760
    backup_count: int = 5


class DataConfig(BaseModel):
    """数据总配置"""
    ifind: iFindConfig = Field(default_factory=iFindConfig)


class AppConfig(BaseSettings):
    """应用总配置"""
    model_config = SettingsConfigDict(
        env_prefix="SWAT_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    data: DataConfig = Field(default_factory=DataConfig)
    emotion_cycle: EmotionCycleConfig = Field(default_factory=EmotionCycleConfig)
    position: PositionConfig = Field(default_factory=PositionConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    alert: AlertConfig = Field(default_factory=AlertConfig)
    yingyou: YingYouConfig = Field(default_factory=YingYouConfig)
    tactics: TacticsConfig = Field(default_factory=TacticsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        """从YAML文件加载配置"""
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data) if data else cls()


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载配置
    
    优先级: 环境变量 > 配置文件 > 默认值
    """
    if config_path and Path(config_path).exists():
        return AppConfig.from_yaml(config_path)
    
    # 尝试默认路径
    default_paths = [
        "config/default.yaml",
        "config/local.yaml",
        os.path.expanduser("~/.swat/config.yaml"),
    ]
    for p in default_paths:
        if Path(p).exists():
            return AppConfig.from_yaml(p)
    
    return AppConfig()
