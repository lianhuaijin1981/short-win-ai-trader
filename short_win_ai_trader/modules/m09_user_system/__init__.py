"""用户账号体系模块 — m09_user_system

提供完整的用户管理、会员体系、权限控制、安全风控功能：
- 用户注册/登录/认证
- 会员付费体系（免费/月卡/季卡/年卡）
- 权限分级管理
- 订单与支付管理
- 安全风控与日志审计
"""

from short_win_ai_trader.modules.m09_user_system.models import (
    User, UserProfile, MembershipTier, MembershipPlan,
    Order, PaymentRecord, Permission, UserPermission,
    AuditLog, SecurityEvent, UsageQuota
)
from short_win_ai_trader.modules.m09_user_system.auth_engine import AuthEngine
from short_win_ai_trader.modules.m09_user_system.membership_manager import MembershipManager
from short_win_ai_trader.modules.m09_user_system.order_manager import OrderManager
from short_win_ai_trader.modules.m09_user_system.permission_manager import PermissionManager
from short_win_ai_trader.modules.m09_user_system.security import SecurityManager
from short_win_ai_trader.modules.m09_user_system.audit_logger import AuditLogger

__all__ = [
    "User", "UserProfile", "MembershipTier", "MembershipPlan",
    "Order", "PaymentRecord", "Permission", "UserPermission",
    "AuditLog", "SecurityEvent", "UsageQuota",
    "AuthEngine", "MembershipManager", "OrderManager",
    "PermissionManager", "SecurityManager", "AuditLogger",
]