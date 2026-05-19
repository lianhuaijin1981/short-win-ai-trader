"""会员管理器 — 会员等级、权益、配额管理

管理会员等级、权益配置、使用配额、试用管理等。
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    User, MembershipType, MembershipPlan, MembershipTier,
    UsageQuota, MEMBERSHIP_BENEFITS
)


class MembershipManager:
    """会员管理器"""

    def __init__(self):
        self._plans: Dict[str, MembershipPlan] = {}  # user_id -> plan
        self._quotas: Dict[str, Dict[str, UsageQuota]] = {}  # user_id -> {date_str -> quota}

    # ── 会员等级 ────────────────────────────────────────

    def get_all_tiers(self) -> List[Dict[str, Any]]:
        """获取所有会员等级信息"""
        tiers = []
        for mtype, benefits in MEMBERSHIP_BENEFITS.items():
            tiers.append({
                "type": mtype,
                "name": benefits["name"],
                "price": benefits["price"],
                "original_price": benefits.get("original_price", benefits["price"]),
                "duration_days": benefits["duration_days"],
                "benefits": benefits,
            })
        return tiers

    def get_tier_info(self, membership_type: str) -> Optional[Dict[str, Any]]:
        """获取指定会员等级信息"""
        benefits = MEMBERSHIP_BENEFITS.get(membership_type)
        if not benefits:
            return None
        return {
            "type": membership_type,
            "name": benefits["name"],
            "price": benefits["price"],
            "original_price": benefits.get("original_price", benefits["price"]),
            "duration_days": benefits["duration_days"],
            "benefits": benefits,
        }

    # ── 会员计划管理 ────────────────────────────────────

    def get_user_plan(self, user_id: str) -> Optional[MembershipPlan]:
        """获取用户会员计划"""
        return self._plans.get(user_id)

    def activate_membership(self, user: User, membership_type: MembershipType, 
                           duration_days: int = None) -> MembershipPlan:
        """激活/续费会员"""
        benefits = MEMBERSHIP_BENEFITS.get(membership_type.value, {})
        if duration_days is None:
            duration_days = benefits.get("duration_days", 30)

        now = datetime.now()

        # 检查是否已有有效会员
        existing = self._plans.get(user.id)
        if existing and existing.is_active and existing.expire_at > now:
            # 续费：在现有到期时间基础上延长
            start_at = existing.expire_at
        else:
            start_at = now

        expire_at = start_at + timedelta(days=duration_days)

        plan = MembershipPlan(
            user_id=user.id,
            membership_type=membership_type,
            start_at=start_at,
            expire_at=expire_at,
            is_active=True,
        )

        self._plans[user.id] = plan

        # 更新用户会员信息
        user.membership_type = membership_type
        user.membership_expire_at = expire_at
        user.is_trial = False
        user.updated_at = now

        return plan

    def deactivate_membership(self, user_id: str):
        """停用会员（降级为免费版）"""
        plan = self._plans.get(user_id)
        if plan:
            plan.is_active = False

    def check_membership_expired(self, user: User) -> bool:
        """检查会员是否过期"""
        if user.membership_type == MembershipType.FREE:
            return False

        if user.membership_expire_at:
            return datetime.now() > user.membership_expire_at
        return True

    def handle_membership_expiry(self, user: User):
        """处理会员过期"""
        if self.check_membership_expired(user):
            user.membership_type = MembershipType.FREE
            user.membership_expire_at = None
            user.updated_at = datetime.now()

            plan = self._plans.get(user.id)
            if plan:
                plan.is_active = False

    # ── 试用管理 ────────────────────────────────────────

    def start_trial(self, user: User, trial_days: int = 7) -> bool:
        """开始试用（新用户7天季卡体验）"""
        if user.is_trial or user.membership_type != MembershipType.FREE:
            return False

        user.is_trial = True
        user.trial_expire_at = datetime.now() + timedelta(days=trial_days)
        user.membership_type = MembershipType.QUARTERLY  # 试用期间享受季卡权益
        user.updated_at = datetime.now()

        return True

    def check_trial_expired(self, user: User) -> bool:
        """检查试用是否过期"""
        if not user.is_trial or not user.trial_expire_at:
            return False
        return datetime.now() > user.trial_expire_at

    def handle_trial_expiry(self, user: User):
        """处理试用过期"""
        if self.check_trial_expired(user):
            user.is_trial = False
            user.membership_type = MembershipType.FREE
            user.membership_expire_at = None
            user.trial_expire_at = None
            user.updated_at = datetime.now()

    # ── 使用配额管理 ────────────────────────────────────

    def get_user_quota(self, user_id: str, membership_type: MembershipType = None) -> UsageQuota:
        """获取用户今日使用配额"""
        today = date.today()
        today_str = today.isoformat()

        # 检查缓存
        if user_id in self._quotas and today_str in self._quotas[user_id]:
            return self._quotas[user_id][today_str]

        # 获取会员权益配置
        mtype = membership_type.value if membership_type else "free"
        benefits = MEMBERSHIP_BENEFITS.get(mtype, MEMBERSHIP_BENEFITS["free"])

        quota = UsageQuota(
            user_id=user_id,
            date=today,
            ai_parse_limit=benefits.get("ai_parse_daily", 10),
            image_export_limit=benefits.get("image_export_daily", 2),
            excel_export_limit=benefits.get("excel_export_daily", 0),
            voice_journal_limit=5,
        )

        if user_id not in self._quotas:
            self._quotas[user_id] = {}
        self._quotas[user_id][today_str] = quota

        return quota

    def consume_quota(self, user_id: str, quota_type: str, 
                     membership_type: MembershipType = None) -> Tuple[bool, str]:
        """
        消耗配额
        返回: (success, message)
        """
        quota = self.get_user_quota(user_id, membership_type)

        if quota_type == "ai_parse":
            if quota.ai_parse_limit != -1 and quota.ai_parse_count >= quota.ai_parse_limit:
                return False, f"今日AI解析额度已用完({quota.ai_parse_count}/{quota.ai_parse_limit})"
            quota.ai_parse_count += 1
            return True, f"AI解析额度: {quota.ai_parse_count}/{quota.ai_parse_limit if quota.ai_parse_limit != -1 else '∞'}"

        elif quota_type == "image_export":
            if quota.image_export_limit != -1 and quota.image_export_count >= quota.image_export_limit:
                return False, f"今日图片导出额度已用完({quota.image_export_count}/{quota.image_export_limit})"
            quota.image_export_count += 1
            return True, f"图片导出额度: {quota.image_export_count}/{quota.image_export_limit if quota.image_export_limit != -1 else '∞'}"

        elif quota_type == "excel_export":
            if quota.excel_export_limit != -1 and quota.excel_export_count >= quota.excel_export_limit:
                return False, f"今日Excel导出额度已用完({quota.excel_export_count}/{quota.excel_export_limit})"
            quota.excel_export_count += 1
            return True, f"Excel导出额度: {quota.excel_export_count}/{quota.excel_export_limit if quota.excel_export_limit != -1 else '∞'}"

        elif quota_type == "voice_journal":
            if quota.voice_journal_count >= quota.voice_journal_limit:
                return False, f"今日语音日记额度已用完({quota.voice_journal_count}/{quota.voice_journal_limit})"
            quota.voice_journal_count += 1
            return True, f"语音日记额度: {quota.voice_journal_count}/{quota.voice_journal_limit}"

        return False, "未知的配额类型"

    def get_quota_status(self, user_id: str, membership_type: MembershipType = None) -> Dict[str, Any]:
        """获取配额使用状态"""
        quota = self.get_user_quota(user_id, membership_type)
        return {
            "ai_parse": {
                "used": quota.ai_parse_count,
                "limit": quota.ai_parse_limit,
                "remaining": max(0, quota.ai_parse_limit - quota.ai_parse_count) if quota.ai_parse_limit != -1 else -1,
            },
            "image_export": {
                "used": quota.image_export_count,
                "limit": quota.image_export_limit,
                "remaining": max(0, quota.image_export_limit - quota.image_export_count) if quota.image_export_limit != -1 else -1,
            },
            "excel_export": {
                "used": quota.excel_export_count,
                "limit": quota.excel_export_limit,
                "remaining": max(0, quota.excel_export_limit - quota.excel_export_count) if quota.excel_export_limit != -1 else -1,
            },
            "voice_journal": {
                "used": quota.voice_journal_count,
                "limit": quota.voice_journal_limit,
                "remaining": max(0, quota.voice_journal_limit - quota.voice_journal_count),
            },
        }

    # ── 会员信息 ────────────────────────────────────────

    def get_membership_info(self, user: User) -> Dict[str, Any]:
        """获取用户完整会员信息"""
        self.handle_trial_expiry(user)
        self.handle_membership_expiry(user)

        benefits = MEMBERSHIP_BENEFITS.get(user.membership_type.value, MEMBERSHIP_BENEFITS["free"])
        plan = self._plans.get(user.id)

        info = {
            "type": user.membership_type.value,
            "name": benefits["name"],
            "is_trial": user.is_trial,
            "trial_expire_at": user.trial_expire_at.isoformat() if user.trial_expire_at else None,
            "membership_expire_at": user.membership_expire_at.isoformat() if user.membership_expire_at else None,
            "benefits": benefits,
            "quota": self.get_quota_status(user.id, user.membership_type),
        }

        if plan:
            info["plan"] = {
                "start_at": plan.start_at.isoformat(),
                "expire_at": plan.expire_at.isoformat(),
                "is_active": plan.is_active,
                "auto_renew": plan.auto_renew,
            }

        return info

    # ── 统计 ────────────────────────────────────────────

    def get_membership_stats(self) -> Dict[str, Any]:
        """获取会员统计"""
        stats = {
            "total_plans": len(self._plans),
            "active_plans": sum(1 for p in self._plans.values() if p.is_active),
            "by_type": {},
        }

        for mtype in MembershipType:
            count = sum(1 for p in self._plans.values() 
                       if p.membership_type == mtype and p.is_active)
            stats["by_type"][mtype.value] = count

        return stats


# 全局单例
_membership_manager: Optional[MembershipManager] = None


def get_membership_manager() -> MembershipManager:
    """获取会员管理器单例"""
    global _membership_manager
    if _membership_manager is None:
        _membership_manager = MembershipManager()
    return _membership_manager