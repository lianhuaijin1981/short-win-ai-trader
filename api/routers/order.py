"""订单路由 — 充值订单、支付管理

提供订单创建、支付、查询、退款等API。
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request

from short_win_ai_trader.modules.m09_user_system.models import (
    MembershipType, PaymentMethod, OrderStatus
)
from short_win_ai_trader.modules.m09_user_system.auth_engine import get_auth_engine
from short_win_ai_trader.modules.m09_user_system.order_manager import get_order_manager
from short_win_ai_trader.modules.m09_user_system.membership_manager import get_membership_manager
from short_win_ai_trader.modules.m09_user_system.audit_logger import get_audit_logger

router = APIRouter(prefix="/order", tags=["Order"])


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


# ── 创建订单 ────────────────────────────────────────────

@router.post("/create", response_model=Dict)
async def create_order(membership_type: MembershipType = Query(..., description="会员类型"),
                      payment_method: PaymentMethod = Query(None, description="支付方式"),
                      authorization: str = Header(None)):
    """创建充值订单"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()

    order = order_mgr.create_order(
        user_id=user.id,
        membership_type=membership_type,
        payment_method=payment_method,
    )

    return {
        "code": 200,
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "membership_type": order.membership_type.value,
            "amount": order.amount,
            "original_amount": order.original_amount,
            "discount_amount": order.discount_amount,
            "status": order.status.value,
            "expire_at": order.expire_at.isoformat(),
            "payment_method": order.payment_method.value if order.payment_method else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 订单查询 ────────────────────────────────────────────

@router.get("/{order_id}", response_model=Dict)
async def get_order(order_id: str, authorization: str = Header(None)):
    """获取订单详情"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()

    order = order_mgr.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="无权查看此订单")

    payment = order_mgr.get_payment_by_order(order_id)

    return {
        "code": 200,
        "data": {
            "order": {
                "id": order.id,
                "order_no": order.order_no,
                "membership_type": order.membership_type.value,
                "amount": order.amount,
                "original_amount": order.original_amount,
                "discount_amount": order.discount_amount,
                "status": order.status.value,
                "payment_method": order.payment_method.value if order.payment_method else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "expire_at": order.expire_at.isoformat(),
                "created_at": order.created_at.isoformat(),
            },
            "payment": {
                "id": payment.id,
                "transaction_id": payment.transaction_id,
                "payment_method": payment.payment_method.value,
                "status": payment.status,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            } if payment else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/list/my", response_model=Dict)
async def get_my_orders(status: OrderStatus = Query(None),
                       page: int = Query(1, ge=1),
                       page_size: int = Query(10, ge=1, le=50),
                       authorization: str = Header(None)):
    """获取我的订单列表"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()

    orders, total = order_mgr.get_user_orders(user.id, status, page, page_size)

    return {
        "code": 200,
        "data": {
            "orders": [{
                "id": o.id,
                "order_no": o.order_no,
                "membership_type": o.membership_type.value,
                "amount": o.amount,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            } for o in orders],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 支付 ────────────────────────────────────────────────

@router.post("/{order_id}/pay", response_model=Dict)
async def pay_order(order_id: str,
                   payment_method: PaymentMethod = Query(...),
                   authorization: str = Header(None)):
    """支付订单"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()
    audit_logger = get_audit_logger()

    order = order_mgr.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    success, message, payment = order_mgr.pay_order(order_id, payment_method)

    if not success:
        return {"code": 400, "message": message}

    # 激活会员
    membership_mgr = get_membership_manager()
    membership_mgr.activate_membership(user, order.membership_type)

    # 记录审计
    audit_logger.log_purchase(
        user_id=user.id,
        order_id=order.id,
        membership_type=order.membership_type.value,
        amount=order.amount,
    )

    return {
        "code": 200,
        "message": "支付成功，会员已激活",
        "data": {
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "membership_type": order.membership_type.value,
            "membership_expire_at": user.membership_expire_at.isoformat() if user.membership_expire_at else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 模拟支付（开发环境） ────────────────────────────────

@router.post("/{order_id}/mock-pay", response_model=Dict)
async def mock_pay_order(order_id: str, authorization: str = Header(None)):
    """模拟支付（仅开发环境）"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()
    membership_mgr = get_membership_manager()
    audit_logger = get_audit_logger()

    order = order_mgr.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    success, message, payment = order_mgr.mock_payment(order_id)

    if not success:
        return {"code": 400, "message": message}

    # 激活会员
    membership_mgr.activate_membership(user, order.membership_type)

    # 记录审计
    audit_logger.log_purchase(
        user_id=user.id,
        order_id=order.id,
        membership_type=order.membership_type.value,
        amount=order.amount,
    )

    return {
        "code": 200,
        "message": "模拟支付成功，会员已激活",
        "data": {
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "membership_type": order.membership_type.value,
            "membership_expire_at": user.membership_expire_at.isoformat() if user.membership_expire_at else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── 取消订单 ────────────────────────────────────────────

@router.post("/{order_id}/cancel", response_model=Dict)
async def cancel_order(order_id: str, authorization: str = Header(None)):
    """取消订单"""
    user, token = get_current_user(authorization)
    order_mgr = get_order_manager()

    order = order_mgr.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    success, message = order_mgr.cancel_order(order_id)

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


# ── 退款（管理员） ──────────────────────────────────────

@router.post("/{order_id}/refund", response_model=Dict)
async def refund_order(order_id: str,
                      reason: str = Query(None),
                      authorization: str = Header(None)):
    """退款（管理员）"""
    user, token = get_current_user(authorization)

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    order_mgr = get_order_manager()
    success, message = order_mgr.refund_order(order_id, reason=reason)

    return {
        "code": 200 if success else 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }