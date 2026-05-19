"""会员路由 — 会员等级、权益、订阅管理

提供会员等级查询、订阅管理、权益对比等API。
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from short_win_ai_trader.modules.m09_user_system.models import MembershipType
from short_win_ai_trader.modules.m09_user_system.auth_engine import get_auth_engine
from short_win_ai_trader.modules.m09_user_system.membership_manager import get_membership_manager
from short_win_ai_trader.modules.m09_user_system.permission_manager import get_permission_manager

router = APIRouter(prefix="/membership", tags=["Membership"])


def get_current_user(authorization: str = Header(None)):
    """获取当前登录用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或Token无效")

    token = authorization[7:]
    auth_engine = get_auth_engine()
    payload = auth_engine.validate_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token已过期或无效")

    user = auth_engine.get_user(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user, token


# ── 会员等级 ────────────────────────────────────────────

@router.get("/tiers", response_model=Dict)
async def get_membership_tiers():
    """获取所有会员等级信息"""
    membership_mgr = get_membership_manager()
    tiers = membership_mgr.get_all_tiers()

    return {
        "code": 200,
        "data": {
            "tiers": tiers,
            "trial_info": {
                "duration_days": 7,
                "trial_membership": "quarterly",
                "description": "新注册用户自动赠送7天季卡体验权益",
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/tiers/{membership_type}", response_model=Dict)
async def get_tier_info(membership_type: str):
    """获取指定会员等级详情"""
    membership_mgr = get_membership_manager()
    tier = membership_mgr.get_tier_info(membership_type)

    if not tier:
        raise HTTPException(status_code=404, detail=f"会员等级不存在: {membership_type}")

    return {
        "code": 200,
        "data": tier,
        "timestamp": datetime.now().isoformat(),
    }


# ── 权益对比 ────────────────────────────────────────────

@router.get("/comparison", response_model=Dict)
async def get_membership_comparison():
    """获取会员权益对比表"""
    permission_mgr = get_permission_manager()
    comparison = permission_mgr.get_membership_permission_comparison()

    return {
        "code": 200,
        "data": {
            "comparison": comparison,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 用户会员信息 ────────────────────────────────────────

@router.get("/my-info", response_model=Dict)
async def get_my_membership(authorization: str = Header(None)):
    """获取当前用户会员信息"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    info = membership_mgr.get_membership_info(user)

    return {
        "code": 200,
        "data": info,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/my-plan", response_model=Dict)
async def get_my_plan(authorization: str = Header(None)):
    """获取当前用户会员计划"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    plan = membership_mgr.get_user_plan(user.id)

    if not plan:
        return {
            "code": 200,
            "data": {
                "message": "暂无会员计划",
                "membership_type": user.membership_type.value,
            },
            "timestamp": datetime.now().isoformat(),
        }

    return {
        "code": 200,
        "data": {
            "plan": {
                "id": plan.id,
                "membership_type": plan.membership_type.value,
                "start_at": plan.start_at.isoformat(),
                "expire_at": plan.expire_at.isoformat(),
                "is_active": plan.is_active,
                "auto_renew": plan.auto_renew,
            },
            "days_remaining": max(0, (plan.expire_at - datetime.now()).days) if plan.expire_at > datetime.now() else 0,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 自动续费管理 ────────────────────────────────────────

@router.post("/auto-renew", response_model=Dict)
async def set_auto_renew(enabled: bool = Query(...),
                        authorization: str = Header(None)):
    """设置自动续费"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    plan = membership_mgr.get_user_plan(user.id)
    if not plan:
        return {"code": 400, "message": "暂无有效会员计划"}

    plan.auto_renew = enabled

    return {
        "code": 200,
        "message": f"自动续费已{'开启' if enabled else '关闭'}",
        "data": {"auto_renew": enabled},
        "timestamp": datetime.now().isoformat(),
    }


# ── 会员统计（管理员） ──────────────────────────────────

@router.get("/stats", response_model=Dict)
async def get_membership_stats(authorization: str = Header(None)):
    """获取会员统计"""
    user, token = get_current_user(authorization)

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    membership_mgr = get_membership_manager()
    stats = membership_mgr.get_membership_stats()

    return {
        "code": 200,
        "data": stats,
        "timestamp": datetime.now().isoformat(),
    }