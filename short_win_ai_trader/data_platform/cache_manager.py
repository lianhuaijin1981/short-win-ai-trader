"""数据缓存管理器 — 支持内存缓存和文件缓存"""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.logger import get_logger

logger = get_logger("swat.cache")


class CacheManager:
    """两级缓存管理器: 内存 + 文件"""

    def __init__(self, cache_dir: str = "./cache", default_ttl: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"缓存管理器初始化: dir={cache_dir}, ttl={default_ttl}s")

    def _make_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        raw = f"{prefix}:{identifier}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _file_path(self, key: str) -> Path:
        """文件缓存路径"""
        return self.cache_dir / f"{key}.cache"

    def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """获取缓存"""
        key = self._make_key(prefix, identifier)

        # 先查内存
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry["expires"] > time.time():
                logger.debug(f"内存缓存命中: {prefix}:{identifier}")
                return entry["data"]
            else:
                del self._memory_cache[key]

        # 再查文件
        fpath = self._file_path(key)
        if fpath.exists():
            try:
                with open(fpath, "rb") as f:
                    entry = pickle.load(f)
                if entry["expires"] > time.time():
                    # 回填内存
                    self._memory_cache[key] = entry
                    logger.debug(f"文件缓存命中: {prefix}:{identifier}")
                    return entry["data"]
                else:
                    fpath.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"读取缓存文件失败: {e}")
                fpath.unlink(missing_ok=True)

        return None

    def set(self, prefix: str, identifier: str, data: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        key = self._make_key(prefix, identifier)
        ttl = ttl or self.default_ttl
        entry = {
            "key": key,
            "expires": time.time() + ttl,
            "data": data,
        }

        # 写内存
        self._memory_cache[key] = entry

        # 写文件
        try:
            fpath = self._file_path(key)
            with open(fpath, "wb") as f:
                pickle.dump(entry, f)
            logger.debug(f"缓存已写入: {prefix}:{identifier}, ttl={ttl}s")
        except Exception as e:
            logger.warning(f"写入缓存文件失败: {e}")

    def invalidate(self, prefix: str, identifier: Optional[str] = None) -> None:
        """使缓存失效"""
        if identifier:
            key = self._make_key(prefix, identifier)
            self._memory_cache.pop(key, None)
            self._file_path(key).unlink(missing_ok=True)
        else:
            # 清空整个prefix
            keys_to_remove = [k for k in self._memory_cache if k.startswith(self._make_key(prefix, "")[:16])]
            for k in keys_to_remove:
                del self._memory_cache[k]
            for f in self.cache_dir.glob("*.cache"):
                f.unlink(missing_ok=True)

    def clear_all(self) -> None:
        """清空所有缓存"""
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.cache"):
            f.unlink(missing_ok=True)
        logger.info("全部缓存已清空")

    def stats(self) -> Dict:
        """缓存统计"""
        memory_count = len(self._memory_cache)
        file_count = len(list(self.cache_dir.glob("*.cache")))
        return {
            "memory_entries": memory_count,
            "file_entries": file_count,
            "cache_dir": str(self.cache_dir),
            "default_ttl": self.default_ttl,
        }
