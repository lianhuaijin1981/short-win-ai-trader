"""权限管理器 — 功能权限、角色管理

管理权限定义、用户权限分配、权限验证等。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    User, MembershipType, Permission, PermissionCategory,
    UserPermission, MEMBERSHIP_BENEFITS
)


# 默认权限定义
DEFAULT_PERMISSIONS: List[Dict[str, Any]] = [
    # AI解析权限
    {"code": "ai_parse:basic", "name": "基础AI解析", "category": PermissionCategory.AI_PARSE, "membership_required": None},
    {"code": "ai_parse:advanced", "name": "高级AI解析", "category": PermissionCategory.AI_PARSE, "membership_required": MembershipType.MONTHLY},
    {"code": "ai_parse:unlimited", "name": "AI解析无限制", "category": PermissionCategory.AI_PARSE, "membership_required": MembershipType.YEARLY},

    # 导出权限
    {"code": "export:image", "name": "图片导出", "category": PermissionCategory.EXPORT, "membership_required": None},
    {"code": "export:excel", "name": "Excel导出", "category": PermissionCategory.EXPORT, "membership_required": MembershipType.MONTHLY},
    {"code": "export:unlimited", "name": "导出无限制", "category": PermissionCategory.EXPORT, "membership_required": MembershipType.QUARTERLY},

    # 存储权限
    {"code": "storage:15days", "name": "15天存储", "category": PermissionCategory.STORAGE, "membership_required": None},
    {"code": "storage:90days", "name": "90天存储", "category": PermissionCategory.STORAGE, "membership_required": MembershipType.MONTHLY},
    {"code": "storage:180days", "name": "180天存储", "category": PermissionCategory.STORAGE, "membership_required": MembershipType.QUARTERLY},
    {"code": "storage:permanent", "name": "永久存储", "category": PermissionCategory.STORAGE, "membership_required": MembershipType.YEARLY},

    # 历史回溯权限
    {"code": "history:3months", "name": "3个月历史", "category": PermissionCategory.HISTORY, "membership_required": None},
    {"code": "history:6months", "name": "6个月历史", "category": PermissionCategory.HISTORY, "membership_required": MembershipType.MONTHLY},
    {"code": "history:1year", "name": "1年历史", "category": PermissionCategory.HISTORY, "membership_required": MembershipType.QUARTERLY},
    {"code": "history:all", "name": "全周期历史", "category": PermissionCategory.HISTORY, "membership_required": MembershipType.YEARLY},

    # 高级功能权限
    {"code": "advanced:stock_tags", "name": "个股智能标签", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.MONTHLY},
    {"code": "advanced:sector_predict", "name": "板块AI预判", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.MONTHLY},
    {"code": "advanced:dual_view", "name": "双视图切换", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.MONTHLY},
    {"code": "advanced:error_analysis", "name": "AI错误归因", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.QUARTERLY},
    {"code": "advanced:rhythm_analysis", "name": "交易节奏分析", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.QUARTERLY},
    {"code": "advanced:capital_analysis", "name": "资金精细分析", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.QUARTERLY},
    {"code": "advanced:trading_report", "name": "交易体系报告", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.YEARLY},
    {"code": "advanced:dashboard", "name": "交易仪表盘", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.YEARLY},
    {"code": "advanced:beta_access", "name": "内测功能", "category": PermissionCategory.ADVANCED, "membership_required": MembershipType.QUARTERLY},

    # 管理权限
    {"code": "admin:user_manage", "name": "用户管理", "category": PermissionCategory.ADMIN, "membership_required": None},
    {"code": "admin:order_manage", "name": "订单管理", "category": PermissionCategory.ADMIN, "membership_required": None},
    {"code": "admin:content_manage", "name": "内容管理", "category": PermissionCategory.ADMIN, "membership_required": None},
    {"code": "admin:system_config", "name": "系统配置", "category": PermissionCategory.ADMIN, "membership_required": None},
]


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._user_permissions: Dict[str, Set[str]] = {}  # user_id -> set of permission codes
        self._init_default_permissions()

    def _init_default_permissions(self):
        """初始化默认权限"""
        for p in DEFAULT_PERMISSIONS:
            perm = Permission(
                code=p["code"],
                name=p["name"],
                category=p["category"],
                membership_required=p.get("membership_required"),
            )
            self._permissions[perm.code] = perm

    # ── 权限查询 ────────────────────────────────────────

    def get_permission(self, code: str) -> Optional[Permission]:
        """获取权限定义"""
        return self._permissions.get(code)

    def get_all_permissions(self) -> List[Permission]:
        """获取所有权限"""
        return list(self._permissions.values())

    def get_permissions_by_category(self, category: PermissionCategory) -> List[Permission]:
        """按分类获取权限"""
        return [p for p in self._permissions.values() if p.category == category]

    # ── 用户权限 ────────────────────────────────────────

    def get_user_permissions(self, user: User) -> List[str]:
        """获取用户所有权限"""
        permissions = set()

        # 基于会员等级的权限
        membership_perms = self._get_membership_permissions(user.membership_type, user.is_trial)
        permissions.update(membership_perms)

        # 额外授予的权限
        user_perms = self._user_permissions.get(user.id, set())
        permissions.update(user_perms)

        # 管理员权限
        if user.is_admin:
            admin_perms = [p.code for p in self._permissions.values() 
                          if p.category == PermissionCategory.ADMIN]
            permissions.update(admin_perms)

        return sorted(permissions)

    def _get_membership_permissions(self, membership_type: MembershipType, 
                                    is_trial: bool = False) -> Set[str]:
        """根据会员等级获取权限"""
        # 试用期间享受季卡权益
        if is_trial:
            effective_type = MembershipType.QUARTERLY
        else:
            effective_type = membership_type

        # 会员等级优先级
        tier_order = {
            MembershipType.FREE: 0,
            MembershipType.MONTHLY: 1,
            MembershipType.QUARTERLY: 2,
            MembershipType.YEARLY: 3,
        }
        user_tier = tier_order.get(effective_type, 0)

        permissions = set()
        for perm in self._permissions.values():
            if perm.membership_required is None:
                # 免费权限
                permissions.add(perm.code)
            else:
                required_tier = tier_order.get(perm.membership_required, 0)
                if user_tier >= required_tier:
                    permissions.add(perm.code)

        return permissions

    def has_permission(self, user: User, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        user_perms = self.get_user_permissions(user)
        return permission_code in user_perms

    def check_permission(self, user: User, permission_code: str) -> Tuple[bool, str]:
        """
        检查权限并返回详细信息
        返回: (has_permission, message)
        """
        perm = self._permissions.get(permission_code)
        if not perm:
            return False, f"权限不存在: {permission_code}"

        if self.has_permission(user, permission_code):
            return True, "有权限"

        if perm.membership_required:
            return False, f"需要{perm.membership_required.value}会员才能使用此功能"
        return False, "无权限"

    # ── 权限授予/撤销 ──────────────────────────────────

    def grant_permission(self, user_id: str, permission_code: str,
                        granted_by: str = None, expire_at: datetime = None) -> Tuple[bool, str]:
        """授予用户权限"""
        if permission_code not in self._permissions:
            return False, f"权限不存在: {permission_code}"

        if user_id not in self._user_permissions:
            self._user_permissions[user_id] = set()

        self._user_permissions[user_id].add(permission_code)
        return True, f"已授予权限: {permission_code}"

    def revoke_permission(self, user_id: str, permission_code: str) -> Tuple[bool, str]:
        """撤销用户权限"""
        if user_id not in self._user_permissions:
            return False, "用户无额外权限"

        if permission_code not in self._user_permissions[user_id]:
            return False, f"用户无此权限: {permission_code}"

        self._user_permissions[user_id].discard(permission_code)
        return True, f"已撤销权限: {permission_code}"

    # ── 权限详情 ────────────────────────────────────────

    def get_user_permission_details(self, user: User) -> Dict[str, Any]:
        """获取用户权限详情"""
        all_perms = self.get_user_permissions(user)
        
        details = {
            "membership_type": user.membership_type.value,
            "is_trial": user.is_trial,
            "is_admin": user.is_admin,
            "permissions": [],
            "by_category": {},
        }

        for code in all_perms:
            perm = self._permissions.get(code)
            if perm:
                details["permissions"].append({
                    "code": perm.code,
                    "name": perm.name,
                    "category": perm.category.value,
                })

                cat = perm.category.value
                if cat not in details["by_category"]:
                    details["by_category"][cat] = []
                details["by_category"][cat].append(perm.name)

        return details

    def get_membership_permission_comparison(self) -> Dict[str, Any]:
        """获取各会员等级权限对比"""
        comparison = {}
        for mtype in MembershipType:
            perms = self._get_membership_permissions(mtype)
            comparison[mtype.value] = {
                "name": MEMBERSHIP_BENEFITS.get(mtype.value, {}).get("name", mtype.value),
                "permissions": sorted(perms),
                "permission_count": len(perms),
            }
        return comparison


# 全局单例
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """获取权限管理器单例"""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager