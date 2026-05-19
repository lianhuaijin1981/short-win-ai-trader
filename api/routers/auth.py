"""认证路由 — 注册、登录、Token管理

提供用户注册、登录、登出、密码修改等认证相关API。
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from short_win_ai_trader.modules.m09_user_system.models import (
    RegisterRequest, LoginRequest, ChangePasswordRequest, TokenResponse
)
from short_win_ai_trader.modules.m09_user_system.auth_engine import get_auth_engine
from short_win_ai_trader.modules.m09_user_system.membership_manager import get_membership_manager
from short_win_ai_trader.modules.m09_user_system.security import get_security_manager
from short_win_ai_trader.modules.m09_user_system.audit_logger import get_audit_logger

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    return request.client.host if request.client else "unknown"


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


# ── 注册 ────────────────────────────────────────────────

@router.post("/register", response_model=Dict)
async def register(req: RegisterRequest, request: Request):
    """用户注册

    新用户注册，自动赠送7天季卡体验权益。
    """
    ip = get_client_ip(request)
    security = get_security_manager()
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()

    # 安全检查
    allowed, message = security.check_rate_limit(ip, "register")
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    # 注册
    success, message, user = auth_engine.register(req)
    if not success:
        return {"code": 400, "message": message}

    # 启动试用
    membership_mgr = get_membership_manager()
    membership_mgr.start_trial(user)

    # 记录审计
    audit_logger.log_register(
        user_id=user.id,
        username=user.username,
        ip_address=ip,
        email=user.email,
    )

    return {
        "code": 200,
        "message": message,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "membership_type": user.membership_type.value,
            "is_trial": user.is_trial,
            "trial_expire_at": user.trial_expire_at.isoformat() if user.trial_expire_at else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 登录 ────────────────────────────────────────────────

@router.post("/login", response_model=Dict)
async def login(req: LoginRequest, request: Request):
    """用户登录

    支持用户名/邮箱/手机号登录。
    """
    ip = get_client_ip(request)
    security = get_security_manager()
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()

    # 安全检查
    allowed, message = security.check_rate_limit(ip, "login")
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    # 检查IP封禁
    blocked, reason = security.is_ip_blocked(ip)
    if blocked:
        raise HTTPException(status_code=403, detail=f"IP已被封禁: {reason}")

    # 登录
    success, message, token_response = auth_engine.login(req, ip_address=ip)

    if not success:
        # 记录失败尝试
        user = auth_engine.get_user_by_username(req.username)
        if user:
            security.record_login_attempt(user.id, ip, success=False)
            security.detect_brute_force(ip)

        audit_logger.log_login(
            user_id=None,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
            success=False,
        )

        return {"code": 401, "message": message}

    # 记录成功登录
    user = auth_engine.get_user(token_response.user["id"])
    security.record_login_attempt(user.id, ip, success=True)
    security.detect_suspicious_login(user.id, ip)

    audit_logger.log_login(
        user_id=user.id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        success=True,
    )

    return {
        "code": 200,
        "message": message,
        "data": token_response.model_dump(),
        "timestamp": datetime.now().isoformat(),
    }


# ── 登出 ────────────────────────────────────────────────

@router.post("/logout", response_model=Dict)
async def logout(request: Request, authorization: str = Header(None)):
    """用户登出"""
    if not authorization or not authorization.startswith("Bearer "):
        return {"code": 200, "message": "已登出"}

    token = authorization[7:]
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()

    user_id = auth_engine.get_user_id_from_token(token)
    auth_engine.logout(token)

    if user_id:
        audit_logger.log_logout(user_id=user_id, ip=get_client_ip(request))

    return {"code": 200, "message": "已登出", "timestamp": datetime.now().isoformat()}


# ── Token刷新 ───────────────────────────────────────────

@router.post("/refresh", response_model=Dict)
async def refresh_token(refresh_token: str):
    """刷新访问Token"""
    auth_engine = get_auth_engine()
    result = auth_engine.refresh_access_token(refresh_token)

    if not result:
        raise HTTPException(status_code=401, detail="Refresh Token无效或已过期")

    access_token, new_refresh_token = result

    return {
        "code": 200,
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": auth_engine.token_expire_hours * 3600,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 修改密码 ────────────────────────────────────────────

@router.post("/change-password", response_model=Dict)
async def change_password(req: ChangePasswordRequest, request: Request,
                         authorization: str = Header(None)):
    """修改密码"""
    user, token = get_current_user(authorization)
    ip = get_client_ip(request)
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()
    security = get_security_manager()

    # 频率限制
    allowed, message = security.check_rate_limit(user.id, "password_change")
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    success, message = auth_engine.change_password(user.id, req.old_password, req.new_password)

    if not success:
        return {"code": 400, "message": message}

    audit_logger.log_password_change(user_id=user.id, ip_address=ip)

    return {
        "code": 200,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


# ── 获取当前用户信息 ────────────────────────────────────

@router.get("/me", response_model=Dict)
async def get_current_user_info(authorization: str = Header(None)):
    """获取当前登录用户信息"""
    user, token = get_current_user(authorization)
    membership_mgr = get_membership_manager()

    # 检查试用/会员过期
    membership_mgr.handle_trial_expiry(user)
    membership_mgr.handle_membership_expiry(user)

    membership_info = membership_mgr.get_membership_info(user)

    return {
        "code": 200,
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "status": user.status.value,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "login_count": user.login_count,
            },
            "membership": membership_info,
        },
        "timestamp": datetime.now().isoformat(),
    }