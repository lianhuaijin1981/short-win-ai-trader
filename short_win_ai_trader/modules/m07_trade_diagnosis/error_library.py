"""交易错题预警库 — 私人避坑清单"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from ...core.logger import get_logger

logger = get_logger("swat.error_library")


class ErrorLibrary:
    """交易错题预警库
    
    自动收录所有亏损交易错误场景:
    - 建立专属私人避坑清单
    - 相似盘面/形态/题材时自动弹窗预警
    - 同类错误二次发生前强制风控提示
    """

    def __init__(self, library_path: str = "data/error_library.json"):
        self.library_path = Path(library_path)
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[Dict] = self._load()
        logger.info(f"错题库初始化: 共{len(self._entries)}条记录")

    def _load(self) -> List[Dict]:
        """加载错题库"""
        if self.library_path.exists():
            with open(self.library_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self) -> None:
        """保存错题库"""
        with open(self.library_path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=2)

    def add_entry(self, error_entry: Dict) -> None:
        """添加错题记录"""
        entry = {
            "id": len(self._entries) + 1,
            "error_type": error_entry.get("error_type", "未知"),
            "ticker": error_entry.get("ticker", ""),
            "stock_name": error_entry.get("stock_name", ""),
            "trade_mode": error_entry.get("trade_mode", ""),
            "emotion_cycle": error_entry.get("emotion_cycle", ""),
            "loss_amount": error_entry.get("loss_amount", 0),
            "loss_pct": error_entry.get("loss_pct", 0),
            "reasons": error_entry.get("reasons", []),
            "timestamp": error_entry.get("timestamp", ""),
            "key_tags": error_entry.get("key_tags", []),
        }
        self._entries.append(entry)
        self.save()
        logger.info(f"错题已收录: #{entry['id']} {entry['ticker']} {entry['error_type']}")

    def find_similar_alerts(self, ticker: str, context: Dict) -> List[str]:
        """查找相似历史错题预警"""
        alerts = []
        emotion = context.get("emotion_cycle", "")
        mode = context.get("trade_mode", "")
        tags = context.get("tags", [])

        for entry in self._entries[-50:]:  # 最近50条
            score = 0
            if entry.get("emotion_cycle") == emotion:
                score += 2
            if entry.get("trade_mode") == mode:
                score += 2
            for tag in tags:
                if tag in entry.get("key_tags", []):
                    score += 1

            if score >= 3:
                alerts.append(
                    f"⚠️ 历史错题预警: #{entry['id']} 曾在{entry['emotion_cycle']}"
                    f"以{entry['trade_mode']}模式亏损{entry['loss_pct']:.1f}%，"
                    f"原因: {entry['error_type']}"
                )

        return alerts

    def get_summary(self) -> Dict:
        """获取错题统计摘要"""
        if not self._entries:
            return {"total": 0, "by_type": {}, "by_emotion": {}, "recent": []}

        by_type = {}
        by_emotion = {}
        for e in self._entries:
            et = e.get("error_type", "未知")
            by_type[et] = by_type.get(et, 0) + 1
            ec = e.get("emotion_cycle", "未知")
            by_emotion[ec] = by_emotion.get(ec, 0) + 1

        return {
            "total": len(self._entries),
            "by_type": by_type,
            "by_emotion": by_emotion,
            "recent": self._entries[-10:],
        }

    def clear(self) -> None:
        """清空错题库"""
        self._entries = []
        self.save()
        logger.info("错题库已清空")
