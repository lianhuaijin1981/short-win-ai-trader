"""API配置管理"""

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API服务配置"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # iFind
    ifind_enabled: bool = True
    ifind_rate_limit: int = 10
    
    # Cache
    cache_ttl: int = 300  # 秒
    
    class Config:
        env_prefix = "SWAT_API_"
