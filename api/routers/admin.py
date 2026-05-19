"""后台管理路由 — 用户管理、订单管理、安全管理、系统配置

提供完整的后台管理功能，仅管理员可访问。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request

from short_win_ai_trader.modules.m09_user_system.models import (
    UserStatus, MembershipType, OrderStatus, AuditAction
)
from short_win_ai_trader.modules.m09_user_system.auth_engine import get_auth_engine
from short_win_ai_trader.modules.m09_user_system.membership_manager import get_membership_manager
from short_win_ai_trader.modules.m09_user_system.order_manager import get_order_manager
from short_win_ai_trader.modules.m09_user_system.permission_manager import get_permission_manager
from short_win_ai_trader.modules.m09_user_system.security import get_security_manager
from short_win_ai_trader.modules.m09_user_system.audit_logger import get_audit_logger

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_user(authorization: str = Header(None)):
    """获取管理员用户"""
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

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    return user, token


# ═══════════════════════════════════════════════════════
# 仪表盘
# ═══════════════════════════════════════════════════════

@router.get("/dashboard", response_model=Dict)
async def get_dashboard(authorization: str = Header(None)):
    """获取管理后台仪表盘数据"""
    admin, token = get_admin_user(authorization)
    auth_engine = get_auth_engine()
    membership_mgr = get_membership_manager()
    order_mgr = get_order_manager()
    security_mgr = get_security_manager()

    return {
        "code": 200,
        "data": {
            "users": {
                "total": auth_engine.get_user_count(),
                "active": auth_engine.get_active_user_count(),
            },
            "membership": membership_mgr.get_membership_stats(),
            "revenue": order_mgr.get_revenue_stats(),
            "security": security_mgr.get_security_stats(),
        },
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════
# 用户管理
# ═══════════════════════════════════════════════════════

@router.get("/users", response_model=Dict)
async def list_users(page: int = Query(1, ge=1),
                    page_size: int = Query(20, ge=1, le=100),
                    status: UserStatus = Query(None),
                    membership: MembershipType = Query(None),
                    keyword: str = Query(None),
                    authorization: str = Header(None)):
    """获取用户列表"""
    admin, token = get_admin_user(authorization)
    auth_engine = get_auth_engine()

    users, total = auth_engine.list_users(page, page_size)

    # 过滤
    if status:
        users = [u for u in users if u.status == status]
    if membership:
        users = [u for u in users if u.membership_type == membership]
    if keyword:
        users = [u for u in users if keyword.lower() in u.username.lower() or 
                (u.email and keyword.lower() in u.email.lower())]

    return {
        "code": 200,
        "data": {
            "users": [{
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "status": u.status.value,
                "membership_type": u.membership_type.value,
                "is_trial": u.is_trial,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "login_count": u.login_count,
            } for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/users/{user_id}/status", response_model=Dict)
async def update_user_status(user_id: str,
                            status: UserStatus = Query(...),
                            authorization: str = Header(None)):
    """更新用户状态"""
    admin, token = get_admin_user(authorization)
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()

    success, message = auth_engine.update_user_status(user_id, status, admin.id)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"更新用户状态: {status.value}",
        target_user_id=user_id,
    )

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/users/{user_id}/admin", response_model=Dict)
async def set_user_admin(user_id: str,
                        is_admin: bool = Query(...),
                        authorization: str = Header(None)):
    """设置管理员权限"""
    admin, token = get_admin_user(authorization)
    auth_engine = get_auth_engine()
    audit_logger = get_audit_logger()

    success, message = auth_engine.set_user_admin(user_id, is_admin)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"{'授予' if is_admin else '撤销'}管理员权限",
        target_user_id=user_id,
    )

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/users/{user_id}/membership", response_model=Dict)
async def set_user_membership(user_id: str,
                             membership_type: MembershipType = Query(...),
                             duration_days: int = Query(30),
                             authorization: str = Header(None)):
    """手动设置用户会员（管理员）"""
    admin, token = get_admin_user(authorization)
    auth_engine = get_auth_engine()
    membership_mgr = get_membership_manager()
    audit_logger = get_audit_logger()

    user = auth_engine.get_user(user_id)
    if not user:
        return {"code": 404, "message": "用户不存在"}

    plan = membership_mgr.activate_membership(user, membership_type, duration_days)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"设置会员: {membership_type.value} ({duration_days}天)",
        target_user_id=user_id,
    )

    return {
        "code": 200,
        "message": f"已设置{membership_type.value}会员",
        "data": {
            "membership_type": membership_type.value,
            "expire_at": plan.expire_at.isoformat(),
        },
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════
# 订单管理
# ═══════════════════════════════════════════════════════

@router.get("/orders", response_model=Dict)
async def list_orders(page: int = Query(1, ge=1),
                     page_size: int = Query(20, ge=1, le=100),
                     status: OrderStatus = Query(None),
                     user_id: str = Query(None),
                     authorization: str = Header(None)):
    """获取订单列表"""
    admin, token = get_admin_user(authorization)
    order_mgr = get_order_manager()

    if user_id:
        orders, total = order_mgr.get_user_orders(user_id, status, page, page_size)
    else:
        # 获取所有订单
        all_orders = list(order_mgr._orders.values())
        if status:
            all_orders = [o for o in all_orders if o.status == status]
        all_orders.sort(key=lambda x: x.created_at, reverse=True)
        total = len(all_orders)
        start = (page - 1) * page_size
        end = start + page_size
        orders = all_orders[start:end]

    return {
        "code": 200,
        "data": {
            "orders": [{
                "id": o.id,
                "order_no": o.order_no,
                "user_id": o.user_id,
                "membership_type": o.membership_type.value,
                "amount": o.amount,
                "status": o.status.value,
                "payment_method": o.payment_method.value if o.payment_method else None,
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                "created_at": o.created_at.isoformat(),
            } for o in orders],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/orders/stats", response_model=Dict)
async def get_order_stats(days: int = Query(30, ge=1, le=365),
                         authorization: str = Header(None)):
    """获取订单统计"""
    admin, token = get_admin_user(authorization)
    order_mgr = get_order_manager()

    start_date = datetime.now() - timedelta(days=days)
    stats = order_mgr.get_order_stats(start_date=start_date)
    revenue = order_mgr.get_revenue_stats()

    return {
        "code": 200,
        "data": {
            "period_days": days,
            "order_stats": stats,
            "revenue_stats": revenue,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════
# 安全管理
# ═══════════════════════════════════════════════════════

@router.get("/security/events", response_model=Dict)
async def get_security_events(severity: str = Query(None),
                             limit: int = Query(50, ge=1, le=200),
                             authorization: str = Header(None)):
    """获取安全事件"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()

    events = security_mgr.get_security_events(severity, limit)

    return {
        "code": 200,
        "data": {
            "events": events,
            "stats": security_mgr.get_security_stats(),
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/security/blocked-ips", response_model=Dict)
async def get_blocked_ips(authorization: str = Header(None)):
    """获取被封禁的IP列表"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()

    blocked_ips = security_mgr.get_blocked_ips()

    return {
        "code": 200,
        "data": {"blocked_ips": blocked_ips},
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/security/block-ip", response_model=Dict)
async def block_ip(ip: str = Query(...),
                  reason: str = Query("管理员手动封禁"),
                  duration: int = Query(3600),
                  authorization: str = Header(None)):
    """封禁IP"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()
    audit_logger = get_audit_logger()

    security_mgr.block_ip(ip, reason, duration)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"封禁IP: {ip}",
        details={"reason": reason, "duration": duration},
    )

    return {
        "code": 200,
        "message": f"IP {ip} 已被封禁",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/security/unblock-ip", response_model=Dict)
async def unblock_ip(ip: str = Query(...),
                    authorization: str = Header(None)):
    """解封IP"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()
    audit_logger = get_audit_logger()

    success = security_mgr.unblock_ip(ip)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"解封IP: {ip}",
    )

    return {
        "code": 200 if success else 404,
        "message": f"IP {ip} 已解封" if success else "IP未被封禁",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/security/locked-accounts", response_model=Dict)
async def get_locked_accounts(authorization: str = Header(None)):
    """获取被锁定的账号"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()

    locked = security_mgr.get_locked_accounts()

    return {
        "code": 200,
        "data": {"locked_accounts": locked},
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/security/unlock-account", response_model=Dict)
async def unlock_account(user_id: str = Query(...),
                        authorization: str = Header(None)):
    """解锁账号"""
    admin, token = get_admin_user(authorization)
    security_mgr = get_security_manager()
    audit_logger = get_audit_logger()

    success = security_mgr.unlock_account(user_id)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"解锁账号: {user_id}",
        target_user_id=user_id,
    )

    return {
        "code": 200 if success else 404,
        "message": f"账号已解锁" if success else "账号未被锁定",
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════
# 审计日志
# ═══════════════════════════════════════════════════════

@router.get("/audit/logs", response_model=Dict)
async def get_audit_logs(user_id: str = Query(None),
                        action: AuditAction = Query(None),
                        page: int = Query(1, ge=1),
                        page_size: int = Query(50, ge=1, le=200),
                        authorization: str = Header(None)):
    """获取审计日志"""
    admin, token = get_admin_user(authorization)
    audit_logger = get_audit_logger()

    logs, total = audit_logger.get_logs(
        user_id=user_id,
        action=action,
        page=page,
        page_size=page_size,
    )

    return {
        "code": 200,
        "data": {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/audit/compliance-report", response_model=Dict)
async def get_compliance_report(days: int = Query(30, ge=1, le=365),
                                authorization: str = Header(None)):
    """获取合规报告"""
    admin, token = get_admin_user(authorization)
    audit_logger = get_audit_logger()

    start_date = datetime.now() - timedelta(days=days)
    report = audit_logger.generate_compliance_report(start_date=start_date)

    return {
        "code": 200,
        "data": report,
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════
# 权限管理
# ═══════════════════════════════════════════════════════

@router.get("/permissions", response_model=Dict)
async def list_permissions(authorization: str = Header(None)):
    """获取所有权限定义"""
    admin, token = get_admin_user(authorization)
    permission_mgr = get_permission_manager()

    permissions = permission_mgr.get_all_permissions()

    return {
        "code": 200,
        "data": {
            "permissions": [{
                "code": p.code,
                "name": p.name,
                "category": p.category.value,
                "membership_required": p.membership_required.value if p.membership_required else None,
                "is_active": p.is_active,
            } for p in permissions],
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/permissions/grant", response_model=Dict)
async def grant_permission(user_id: str = Query(...),
                          permission_code: str = Query(...),
                          authorization: str = Header(None)):
    """授予用户权限"""
    admin, token = get_admin_user(authorization)
    permission_mgr = get_permission_manager()
    audit_logger = get_audit_logger()

    success, message = permission_mgr.grant_permission(user_id, permission_code, admin.id)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"授予权限: {permission_code}",
        target_user_id=user_id,
    )

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/permissions/revoke", response_model=Dict)
async def revoke_permission(user_id: str = Query(...),
                           permission_code: str = Query(...),
                           authorization: str = Header(None)):
    """撤销用户权限"""
    admin, token = get_admin_user(authorization)
    permission_mgr = get_permission_manager()
    audit_logger = get_audit_logger()

    success, message = permission_mgr.revoke_permission(user_id, permission_code)

    audit_logger.log_admin_action(
        admin_id=admin.id,
        action_desc=f"撤销权限: {permission_code}",
        target_user_id=user_id,
    )

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }