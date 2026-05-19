"""审计日志管理器 — 操作日志、合规审计

记录所有用户操作、系统事件，支持审计查询和合规报告。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    AuditLog, AuditAction
)


class AuditLogger:
    """审计日志管理器"""

    def __init__(self, max_logs: int = 100000):
        self._logs: List[AuditLog] = []
        self._max_logs = max_logs

    # ── 日志记录 ────────────────────────────────────────

    def log(self, action: AuditAction, user_id: str = None,
            resource_type: str = None, resource_id: str = None,
            ip_address: str = None, user_agent: str = None,
            details: Dict[str, Any] = None) -> AuditLog:
        """记录审计日志"""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        self._logs.append(log_entry)

        # 清理过期日志
        self._cleanup()

        return log_entry

    def log_login(self, user_id: str, ip_address: str = None,
                 user_agent: str = None, success: bool = True):
        """记录登录"""
        self.log(
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"success": success},
        )

    def log_logout(self, user_id: str, ip_address: str = None):
        """记录登出"""
        self.log(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            ip_address=ip_address,
        )

    def log_register(self, user_id: str, username: str,
                    ip_address: str = None, email: str = None):
        """记录注册"""
        self.log(
            action=AuditAction.REGISTER,
            user_id=user_id,
            ip_address=ip_address,
            details={"username": username, "email": email},
        )

    def log_profile_update(self, user_id: str, fields: List[str],
                          ip_address: str = None):
        """记录资料更新"""
        self.log(
            action=AuditAction.UPDATE_PROFILE,
            user_id=user_id,
            ip_address=ip_address,
            details={"updated_fields": fields},
        )

    def log_password_change(self, user_id: str, ip_address: str = None):
        """记录密码修改"""
        self.log(
            action=AuditAction.CHANGE_PASSWORD,
            user_id=user_id,
            ip_address=ip_address,
        )

    def log_purchase(self, user_id: str, order_id: str,
                    membership_type: str, amount: float,
                    ip_address: str = None):
        """记录购买"""
        self.log(
            action=AuditAction.PURCHASE,
            user_id=user_id,
            resource_type="order",
            resource_id=order_id,
            ip_address=ip_address,
            details={
                "membership_type": membership_type,
                "amount": amount,
            },
        )

    def log_export(self, user_id: str, export_type: str,
                  resource_id: str = None, ip_address: str = None):
        """记录导出"""
        self.log(
            action=AuditAction.EXPORT_DATA,
            user_id=user_id,
            resource_type=export_type,
            resource_id=resource_id,
            ip_address=ip_address,
        )

    def log_ai_call(self, user_id: str, ai_type: str,
                   ip_address: str = None):
        """记录AI调用"""
        self.log(
            action=AuditAction.AI_CALL,
            user_id=user_id,
            resource_type="ai",
            details={"ai_type": ai_type},
            ip_address=ip_address,
        )

    def log_admin_action(self, admin_id: str, action_desc: str,
                        target_user_id: str = None,
                        ip_address: str = None, details: Dict = None):
        """记录管理员操作"""
        self.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            resource_type="admin",
            resource_id=target_user_id,
            ip_address=ip_address,
            details={"action": action_desc, **(details or {})},
        )

    # ── 日志查询 ────────────────────────────────────────

    def get_logs(self, user_id: str = None, action: AuditAction = None,
                start_date: datetime = None, end_date: datetime = None,
                page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """查询审计日志"""
        logs = self._logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        if action:
            logs = [l for l in logs if l.action == action]
        if start_date:
            logs = [l for l in logs if l.created_at >= start_date]
        if end_date:
            logs = [l for l in logs if l.created_at <= end_date]

        # 按时间倒序
        logs = sorted(logs, key=lambda x: x.created_at, reverse=True)
        total = len(logs)

        start = (page - 1) * page_size
        end = start + page_size
        page_logs = logs[start:end]

        return [l.model_dump() for l in page_logs], total

    def get_user_activity(self, user_id: str, days: int = 30) -> List[Dict]:
        """获取用户活动记录"""
        start_date = datetime.now() - timedelta(days=days)
        logs, _ = self.get_logs(user_id=user_id, start_date=start_date)
        return logs

    def get_action_summary(self, user_id: str = None, 
                          days: int = 7) -> Dict[str, int]:
        """获取操作汇总"""
        start_date = datetime.now() - timedelta(days=days)
        logs = self._logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        logs = [l for l in logs if l.created_at >= start_date]

        summary = {}
        for log in logs:
            action = log.action.value
            summary[action] = summary.get(action, 0) + 1

        return summary

    # ── 合规报告 ────────────────────────────────────────

    def generate_compliance_report(self, start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """生成合规报告"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        logs = [l for l in self._logs 
                if start_date <= l.created_at <= end_date]

        # 统计
        action_counts = {}
        user_counts = {}
        ip_counts = {}

        for log in logs:
            action = log.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

            if log.user_id:
                user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1

            if log.ip_address:
                ip_counts[log.ip_address] = ip_counts.get(log.ip_address, 0) + 1

        # 活跃用户TOP10
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 高频IPTOP10
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_logs": len(logs),
                "unique_users": len(user_counts),
                "unique_ips": len(ip_counts),
            },
            "action_distribution": action_counts,
            "top_active_users": [{"user_id": uid, "count": cnt} for uid, cnt in top_users],
            "top_ips": [{"ip": ip, "count": cnt} for ip, cnt in top_ips],
            "security_notes": self._generate_security_notes(logs),
        }

    def _generate_security_notes(self, logs: List[AuditLog]) -> List[str]:
        """生成安全备注"""
        notes = []

        # 检查异常登录
        login_logs = [l for l in logs if l.action == AuditAction.LOGIN]
        failed_logins = [l for l in login_logs if not l.details.get("success", True)]

        if len(failed_logins) > 50:
            notes.append(f"警告: 检测到{len(failed_logins)}次失败登录尝试")

        # 检查管理员操作
        admin_logs = [l for l in logs if l.action == AuditAction.ADMIN_ACTION]
        if admin_logs:
            notes.append(f"管理员操作记录: {len(admin_logs)}次")

        # 检查大量导出
        export_logs = [l for l in logs if l.action == AuditAction.EXPORT_DATA]
        if len(export_logs) > 100:
            notes.append(f"注意: 检测到{len(export_logs)}次数据导出操作")

        return notes

    # ── 内部方法 ────────────────────────────────────────

    def _cleanup(self):
        """清理过期日志"""
        if len(self._logs) > self._max_logs:
            # 保留最近的日志
            self._logs = self._logs[-self._max_logs:]

    def get_log_count(self) -> int:
        """获取日志总数"""
        return len(self._logs)

    def clear_logs(self):
        """清空日志（管理员操作）"""
        self._logs.clear()


# 全局单例
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志管理器单例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger