"""用户路由 — 用户资料、权限、配额管理

提供用户资料管理、权限查询、配额管理等API。
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request

from short_win_ai_trader.modules.m09_user_system.models import (
    UpdateProfileRequest, UserProfile
)
from short_win_ai_trader.modules.m09_user_system.auth_engine import get_auth_engine
from short_win_ai_trader.modules.m09_user_system.membership_manager import get_membership_manager
from short_win_ai_trader.modules.m09_user_system.permission_manager import get_permission_manager
from short_win_ai_trader.modules.m09_user_system.audit_logger import get_audit_logger

router = APIRouter(prefix="/user", tags=["User"])


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


# ── 用户资料 ────────────────────────────────────────────

@router.get("/profile", response_model=Dict)
async def get_profile(authorization: str = Header(None)):
    """获取用户资料"""
    user, token = get_current_user(authorization)

    profile = UserProfile(
        user_id=user.id,
        nickname=user.username,
    )

    return {
        "code": 200,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "nickname": user.username,
            "membership_type": user.membership_type.value,
            "is_trial": user.is_trial,
            "created_at": user.created_at.isoformat(),
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/profile", response_model=Dict)
async def update_profile(req: UpdateProfileRequest, request: Request,
                        authorization: str = Header(None)):
    """更新用户资料"""
    user, token = get_current_user(authorization)
    audit_logger = get_audit_logger()

    updated_fields = []
    if req.nickname:
        updated_fields.append("nickname")
    if req.bio:
        updated_fields.append("bio")
    if req.trading_experience:
        updated_fields.append("trading_experience")
    if req.preferred_style:
        updated_fields.append("preferred_style")
    if req.risk_tolerance:
        updated_fields.append("risk_tolerance")

    audit_logger.log_profile_update(
        user_id=user.id,
        fields=updated_fields,
        ip_address=request.client.host if request.client else None,
    )

    return {
        "code": 200,
        "message": "资料更新成功",
        "data": {"updated_fields": updated_fields},
        "timestamp": datetime.now().isoformat(),
    }


# ── 配额管理 ────────────────────────────────────────────

@router.get("/quota", response_model=Dict)
async def get_quota(authorization: str = Header(None)):
    """获取当前配额使用情况"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    quota_status = membership_mgr.get_quota_status(user.id, user.membership_type)

    return {
        "code": 200,
        "data": {
            "membership_type": user.membership_type.value,
            "quotas": quota_status,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/quota/consume", response_model=Dict)
async def consume_quota(quota_type: str = Query(..., description="配额类型: ai_parse/image_export/excel_export/voice_journal"),
                       authorization: str = Header(None)):
    """消耗配额"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    success, message = membership_mgr.consume_quota(user.id, quota_type, user.membership_type)

    if not success:
        return {"code": 403, "message": message}

    quota_status = membership_mgr.get_quota_status(user.id, user.membership_type)

    return {
        "code": 200,
        "message": message,
        "data": {"quotas": quota_status},
        "timestamp": datetime.now().isoformat(),
    }


# ── 权限管理 ────────────────────────────────────────────

@router.get("/permissions", response_model=Dict)
async def get_permissions(authorization: str = Header(None)):
    """获取用户权限列表"""
    user, token = get_current_user(authorization)
    permission_mgr = get_permission_manager()

    perm_details = permission_mgr.get_user_permission_details(user)

    return {
        "code": 200,
        "data": perm_details,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/permissions/check", response_model=Dict)
async def check_permission(permission_code: str = Query(...),
                          authorization: str = Header(None)):
    """检查特定权限"""
    user, token = get_current_user(authorization)
    permission_mgr = get_permission_manager()

    has_perm, message = permission_mgr.check_permission(user, permission_code)

    return {
        "code": 200,
        "data": {
            "permission_code": permission_code,
            "has_permission": has_perm,
            "message": message,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 活动记录 ────────────────────────────────────────────

@router.get("/activity", response_model=Dict)
async def get_activity(days: int = Query(30, ge=1, le=90),
                      authorization: str = Header(None)):
    """获取用户活动记录"""
    user, token = get_current_user(authorization)
    audit_logger = get_audit_logger()

    activity = audit_logger.get_user_activity(user.id, days)

    return {
        "code": 200,
        "data": {
            "activities": activity,
            "total": len(activity),
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/activity/summary", response_model=Dict)
async def get_activity_summary(days: int = Query(7, ge=1, le=30),
                               authorization: str = Header(None)):
    """获取用户活动汇总"""
    user, token = get_current_user(authorization)
    audit_logger = get_audit_logger()

    summary = audit_logger.get_action_summary(user.id, days)

    return {
        "code": 200,
        "data": {
            "summary": summary,
            "period_days": days,
        },
        "timestamp": datetime.now().isoformat(),
    }