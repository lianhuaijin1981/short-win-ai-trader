"""安全风控管理器 — 防刷、IP封禁、异常检测

提供安全防护、频率限制、暴力破解防护、异常登录检测等功能。
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    SecurityEvent, SecurityEventType
)


class RateLimiter:
    """频率限制器"""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._limits: Dict[str, Tuple[int, int]] = {
            "login": (5, 300),       # 5次/5分钟
            "register": (3, 3600),   # 3次/1小时
            "api_call": (100, 60),   # 100次/1分钟
            "password_change": (3, 3600),  # 3次/1小时
            "export": (10, 60),      # 10次/1分钟
        }

    def check(self, key: str, limit_type: str = "api_call") -> Tuple[bool, str]:
        """
        检查频率限制
        返回: (allowed, message)
        """
        max_requests, window = self._limits.get(limit_type, (100, 60))
        now = time.time()
        cutoff = now - window

        # 清理过期记录
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= max_requests:
            remaining_time = int(window - (now - self._requests[key][0]))
            return False, f"请求过于频繁，请{remaining_time}秒后重试"

        self._requests[key].append(now)
        return True, "OK"

    def get_remaining(self, key: str, limit_type: str = "api_call") -> int:
        """获取剩余请求次数"""
        max_requests, window = self._limits.get(limit_type, (100, 60))
        now = time.time()
        cutoff = now - window

        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        return max(0, max_requests - len(self._requests[key]))


class SecurityManager:
    """安全风控管理器"""

    def __init__(self):
        self._rate_limiter = RateLimiter()
        self._blocked_ips: Dict[str, Dict] = {}  # ip -> {reason, expire_at}
        self._locked_accounts: Dict[str, Dict] = {}  # user_id -> {reason, expire_at, attempts}
        self._login_attempts: Dict[str, List[Dict]] = defaultdict(list)  # ip -> attempts
        self._security_events: List[SecurityEvent] = []

        # 安全配置
        self.max_login_attempts = 5
        self.login_lockout_duration = 900  # 15分钟
        self.ip_block_duration = 3600  # 1小时
        self.suspicious_threshold = 10

    # ── 频率限制 ────────────────────────────────────────

    def check_rate_limit(self, key: str, limit_type: str = "api_call") -> Tuple[bool, str]:
        """检查频率限制"""
        return self._rate_limiter.check(key, limit_type)

    def get_rate_limit_info(self, key: str, limit_type: str = "api_call") -> Dict[str, Any]:
        """获取频率限制信息"""
        return {
            "remaining": self._rate_limiter.get_remaining(key, limit_type),
            "limit_type": limit_type,
        }

    # ── IP管理 ──────────────────────────────────────────

    def block_ip(self, ip: str, reason: str = "异常行为", duration: int = None):
        """封禁IP"""
        if duration is None:
            duration = self.ip_block_duration

        self._blocked_ips[ip] = {
            "reason": reason,
            "blocked_at": datetime.now().isoformat(),
            "expire_at": (datetime.now() + timedelta(seconds=duration)).isoformat(),
        }

        # 记录安全事件
        self._record_security_event(
            event_type=SecurityEventType.IP_BLOCK,
            ip_address=ip,
            severity="high",
            description=f"IP被封禁: {reason}",
        )

    def unblock_ip(self, ip: str) -> bool:
        """解封IP"""
        if ip in self._blocked_ips:
            del self._blocked_ips[ip]
            return True
        return False

    def is_ip_blocked(self, ip: str) -> Tuple[bool, Optional[str]]:
        """检查IP是否被封禁"""
        if ip not in self._blocked_ips:
            return False, None

        block_info = self._blocked_ips[ip]
        expire_at = datetime.fromisoformat(block_info["expire_at"])

        if datetime.now() > expire_at:
            del self._blocked_ips[ip]
            return False, None

        return True, block_info["reason"]

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """获取所有被封禁的IP"""
        result = []
        for ip, info in self._blocked_ips.items():
            result.append({
                "ip": ip,
                "reason": info["reason"],
                "blocked_at": info["blocked_at"],
                "expire_at": info["expire_at"],
            })
        return result

    # ── 账号锁定 ────────────────────────────────────────

    def record_login_attempt(self, user_id: str, ip: str, success: bool):
        """记录登录尝试"""
        attempt = {
            "ip": ip,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        self._login_attempts[user_id].append(attempt)

        # 检查是否需要锁定
        if not success:
            recent_failures = [
                a for a in self._login_attempts[user_id]
                if not a["success"] and 
                datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(seconds=self.login_lockout_duration)
            ]

            if len(recent_failures) >= self.max_login_attempts:
                self.lock_account(user_id, "连续登录失败次数过多")

    def lock_account(self, user_id: str, reason: str = "安全原因", duration: int = None):
        """锁定账号"""
        if duration is None:
            duration = self.login_lockout_duration

        self._locked_accounts[user_id] = {
            "reason": reason,
            "locked_at": datetime.now().isoformat(),
            "expire_at": (datetime.now() + timedelta(seconds=duration)).isoformat(),
            "attempts": len(self._login_attempts.get(user_id, [])),
        }

        self._record_security_event(
            event_type=SecurityEventType.ACCOUNT_LOCK,
            user_id=user_id,
            severity="high",
            description=f"账号被锁定: {reason}",
        )

    def unlock_account(self, user_id: str) -> bool:
        """解锁账号"""
        if user_id in self._locked_accounts:
            del self._locked_accounts[user_id]
            self._login_attempts[user_id] = []
            return True
        return False

    def is_account_locked(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """检查账号是否被锁定"""
        if user_id not in self._locked_accounts:
            return False, None

        lock_info = self._locked_accounts[user_id]
        expire_at = datetime.fromisoformat(lock_info["expire_at"])

        if datetime.now() > expire_at:
            del self._locked_accounts[user_id]
            self._login_attempts[user_id] = []
            return False, None

        return True, lock_info["reason"]

    def get_locked_accounts(self) -> List[Dict[str, Any]]:
        """获取所有被锁定的账号"""
        result = []
        for user_id, info in self._locked_accounts.items():
            result.append({
                "user_id": user_id,
                "reason": info["reason"],
                "locked_at": info["locked_at"],
                "expire_at": info["expire_at"],
                "attempts": info["attempts"],
            })
        return result

    # ── 异常检测 ────────────────────────────────────────

    def detect_brute_force(self, ip: str) -> bool:
        """检测暴力破解"""
        recent_attempts = [
            a for attempts in self._login_attempts.values()
            for a in attempts
            if a["ip"] == ip and not a["success"] and
            datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(minutes=10)
        ]

        if len(recent_attempts) >= self.suspicious_threshold:
            self._record_security_event(
                event_type=SecurityEventType.BRUTE_FORCE,
                ip_address=ip,
                severity="critical",
                description=f"检测到暴力破解: {len(recent_attempts)}次失败尝试",
            )
            self.block_ip(ip, "暴力破解攻击")
            return True

        return False

    def detect_suspicious_login(self, user_id: str, ip: str) -> bool:
        """检测异常登录"""
        # 检查是否是新IP
        known_ips = set(a["ip"] for a in self._login_attempts.get(user_id, []))

        if ip not in known_ips and len(known_ips) > 3:
            self._record_security_event(
                event_type=SecurityEventType.SUSPICIOUS_LOGIN,
                user_id=user_id,
                ip_address=ip,
                severity="medium",
                description=f"异常IP登录: {ip}",
            )
            return True

        return False

    # ── 安全事件 ────────────────────────────────────────

    def _record_security_event(self, event_type: SecurityEventType, 
                               user_id: str = None, ip_address: str = None,
                               severity: str = "medium", description: str = "",
                               details: Dict = None):
        """记录安全事件"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            description=description,
            details=details or {},
        )
        self._security_events.append(event)

    def get_security_events(self, severity: str = None, limit: int = 50) -> List[Dict]:
        """获取安全事件"""
        events = self._security_events

        if severity:
            events = [e for e in events if e.severity == severity]

        events = sorted(events, key=lambda x: x.created_at, reverse=True)
        return [e.model_dump() for e in events[:limit]]

    def get_security_stats(self) -> Dict[str, Any]:
        """获取安全统计"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        recent_events = [e for e in self._security_events if e.created_at > yesterday]

        return {
            "total_events": len(self._security_events),
            "recent_24h": len(recent_events),
            "blocked_ips": len(self._blocked_ips),
            "locked_accounts": len(self._locked_accounts),
            "by_severity": {
                "critical": sum(1 for e in recent_events if e.severity == "critical"),
                "high": sum(1 for e in recent_events if e.severity == "high"),
                "medium": sum(1 for e in recent_events if e.severity == "medium"),
                "low": sum(1 for e in recent_events if e.severity == "low"),
            },
            "by_type": {
                et.value: sum(1 for e in recent_events if e.event_type == et)
                for et in SecurityEventType
            },
        }

    # ── 请求验证 ────────────────────────────────────────

    def validate_request(self, ip: str, user_id: str = None, 
                        action: str = "api_call") -> Tuple[bool, str]:
        """
        综合验证请求
        返回: (allowed, message)
        """
        # 检查IP封禁
        blocked, reason = self.is_ip_blocked(ip)
        if blocked:
            return False, f"IP已被封禁: {reason}"

        # 检查账号锁定
        if user_id:
            locked, reason = self.is_account_locked(user_id)
            if locked:
                return False, f"账号已被锁定: {reason}"

        # 检查频率限制
        allowed, message = self.check_rate_limit(ip, action)
        if not allowed:
            return False, message

        return True, "OK"


# 全局单例
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """获取安全管理器单例"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager