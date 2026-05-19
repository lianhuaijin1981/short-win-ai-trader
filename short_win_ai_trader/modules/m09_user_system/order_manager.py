"""订单管理器 — 充值订单、支付流水管理

管理订单创建、支付、退款等完整订单生命周期。
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    User, Order, OrderStatus, PaymentRecord, PaymentMethod,
    MembershipType, MEMBERSHIP_BENEFITS
)


class OrderManager:
    """订单管理器"""

    def __init__(self):
        self._orders: Dict[str, Order] = {}  # order_id -> order
        self._orders_by_no: Dict[str, str] = {}  # order_no -> order_id
        self._payments: Dict[str, PaymentRecord] = {}  # payment_id -> payment
        self._payments_by_order: Dict[str, str] = {}  # order_id -> payment_id

    # ── 订单创建 ────────────────────────────────────────

    def create_order(self, user_id: str, membership_type: MembershipType,
                    payment_method: PaymentMethod = None) -> Order:
        """创建充值订单"""
        benefits = MEMBERSHIP_BENEFITS.get(membership_type.value, {})
        price = benefits.get("price", 0)
        original_price = benefits.get("original_price", price)

        order = Order(
            user_id=user_id,
            membership_type=membership_type,
            amount=price,
            original_amount=original_price,
            discount_amount=original_price - price,
            payment_method=payment_method,
            expire_at=datetime.now() + timedelta(minutes=30),
        )

        self._orders[order.id] = order
        self._orders_by_no[order.order_no] = order.id

        return order

    # ── 订单查询 ────────────────────────────────────────

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self._orders.get(order_id)

    def get_order_by_no(self, order_no: str) -> Optional[Order]:
        """通过订单号获取订单"""
        order_id = self._orders_by_no.get(order_no)
        return self._orders.get(order_id) if order_id else None

    def get_user_orders(self, user_id: str, status: OrderStatus = None,
                       page: int = 1, page_size: int = 10) -> Tuple[List[Order], int]:
        """获取用户订单列表"""
        orders = [o for o in self._orders.values() if o.user_id == user_id]

        if status:
            orders = [o for o in orders if o.status == status]

        orders.sort(key=lambda x: x.created_at, reverse=True)
        total = len(orders)
        start = (page - 1) * page_size
        end = start + page_size

        return orders[start:end], total

    # ── 订单状态管理 ────────────────────────────────────

    def pay_order(self, order_id: str, payment_method: PaymentMethod,
                 transaction_id: str = None) -> Tuple[bool, str, Optional[PaymentRecord]]:
        """
        支付订单
        返回: (success, message, payment_record)
        """
        order = self._orders.get(order_id)
        if not order:
            return False, "订单不存在", None

        if order.status != OrderStatus.PENDING:
            return False, f"订单状态异常: {order.status.value}", None

        if datetime.now() > order.expire_at:
            order.status = OrderStatus.EXPIRED
            order.updated_at = datetime.now()
            return False, "订单已过期", None

        # 创建支付记录
        payment = PaymentRecord(
            order_id=order.id,
            user_id=order.user_id,
            amount=order.amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status="paid",
            paid_at=datetime.now(),
        )

        self._payments[payment.id] = payment
        self._payments_by_order[order.id] = payment.id

        # 更新订单状态
        order.status = OrderStatus.PAID
        order.payment_method = payment_method
        order.paid_at = datetime.now()
        order.updated_at = datetime.now()

        return True, "支付成功", payment

    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """取消订单"""
        order = self._orders.get(order_id)
        if not order:
            return False, "订单不存在"

        if order.status != OrderStatus.PENDING:
            return False, "只能取消待支付订单"

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()

        return True, "订单已取消"

    def refund_order(self, order_id: str, refund_amount: float = None,
                    reason: str = None) -> Tuple[bool, str]:
        """退款"""
        order = self._orders.get(order_id)
        if not order:
            return False, "订单不存在"

        if order.status != OrderStatus.PAID:
            return False, "只能退款已支付订单"

        payment_id = self._payments_by_order.get(order_id)
        if payment_id:
            payment = self._payments.get(payment_id)
            if payment:
                payment.refund_amount = refund_amount or order.amount
                payment.refund_at = datetime.now()
                payment.status = "refunded"

        order.status = OrderStatus.REFUNDED
        order.updated_at = datetime.now()
        order.remark = f"退款原因: {reason}" if reason else "已退款"

        return True, "退款成功"

    # ── 支付记录 ────────────────────────────────────────

    def get_payment(self, payment_id: str) -> Optional[PaymentRecord]:
        """获取支付记录"""
        return self._payments.get(payment_id)

    def get_payment_by_order(self, order_id: str) -> Optional[PaymentRecord]:
        """通过订单获取支付记录"""
        payment_id = self._payments_by_order.get(order_id)
        return self._payments.get(payment_id) if payment_id else None

    def get_user_payments(self, user_id: str) -> List[PaymentRecord]:
        """获取用户支付记录"""
        return [p for p in self._payments.values() if p.user_id == user_id]

    # ── 模拟支付（开发环境） ────────────────────────────

    def mock_payment(self, order_id: str) -> Tuple[bool, str, Optional[PaymentRecord]]:
        """模拟支付成功（开发/测试环境）"""
        order = self._orders.get(order_id)
        if not order:
            return False, "订单不存在", None

        return self.pay_order(
            order_id=order_id,
            payment_method=PaymentMethod.WECHAT,
            transaction_id=f"MOCK_{uuid.uuid4().hex[:12].upper()}"
        )

    # ── 统计 ────────────────────────────────────────────

    def get_order_stats(self, start_date: datetime = None, 
                       end_date: datetime = None) -> Dict[str, Any]:
        """获取订单统计"""
        orders = list(self._orders.values())

        if start_date:
            orders = [o for o in orders if o.created_at >= start_date]
        if end_date:
            orders = [o for o in orders if o.created_at <= end_date]

        stats = {
            "total_orders": len(orders),
            "total_amount": sum(o.amount for o in orders if o.status == OrderStatus.PAID),
            "by_status": {},
            "by_membership": {},
            "by_payment_method": {},
        }

        for status in OrderStatus:
            stats["by_status"][status.value] = sum(1 for o in orders if o.status == status)

        for mtype in MembershipType:
            count = sum(1 for o in orders if o.membership_type == mtype and o.status == OrderStatus.PAID)
            amount = sum(o.amount for o in orders if o.membership_type == mtype and o.status == OrderStatus.PAID)
            stats["by_membership"][mtype.value] = {"count": count, "amount": amount}

        for method in PaymentMethod:
            count = sum(1 for o in orders if o.payment_method == method and o.status == OrderStatus.PAID)
            stats["by_payment_method"][method.value] = count

        return stats

    def get_revenue_stats(self) -> Dict[str, Any]:
        """获取收入统计"""
        paid_orders = [o for o in self._orders.values() if o.status == OrderStatus.PAID]
        refunded_orders = [o for o in self._orders.values() if o.status == OrderStatus.REFUNDED]

        return {
            "total_revenue": sum(o.amount for o in paid_orders),
            "total_refunded": sum(o.amount for o in refunded_orders),
            "net_revenue": sum(o.amount for o in paid_orders) - sum(o.amount for o in refunded_orders),
            "paid_order_count": len(paid_orders),
            "refunded_order_count": len(refunded_orders),
            "average_order_value": sum(o.amount for o in paid_orders) / len(paid_orders) if paid_orders else 0,
        }


# 全局单例
_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    """获取订单管理器单例"""
    global _order_manager
    if _order_manager is None:
        _order_manager = OrderManager()
    return _order_manager