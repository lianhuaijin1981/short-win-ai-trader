"""用户系统数据模型

定义用户、会员、订单、权限、审计等核心数据模型。
"""

import enum
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr


# ═══════════════════════════════════════════════════════
# 枚举定义
# ═══════════════════════════════════════════════════════

class UserStatus(str, enum.Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    PENDING_VERIFY = "pending_verify"


class MembershipType(str, enum.Enum):
    """会员类型"""
    FREE = "free"           # 免费版
    MONTHLY = "monthly"     # 月卡
    QUARTERLY = "quarterly" # 季卡
    YEARLY = "yearly"       # 年卡


class OrderStatus(str, enum.Enum):
    """订单状态"""
    PENDING = "pending"         # 待支付
    PAID = "paid"               # 已支付
    CANCELLED = "cancelled"     # 已取消
    REFUNDED = "refunded"       # 已退款
    EXPIRED = "expired"         # 已过期


class PaymentMethod(str, enum.Enum):
    """支付方式"""
    WECHAT = "wechat"       # 微信支付
    ALIPAY = "alipay"       # 支付宝
    BANK_CARD = "bank_card" # 银行卡


class PermissionCategory(str, enum.Enum):
    """权限分类"""
    AI_PARSE = "ai_parse"           # AI解析
    EXPORT = "export"               # 导出功能
    STORAGE = "storage"             # 数据存储
    HISTORY = "history"             # 历史回溯
    ADVANCED = "advanced"           # 高级功能
    ADMIN = "admin"                 # 管理功能


class AuditAction(str, enum.Enum):
    """审计动作"""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    UPDATE_PROFILE = "update_profile"
    CHANGE_PASSWORD = "change_password"
    PURCHASE = "purchase"
    RENEW = "renew"
    UPGRADE = "upgrade"
    EXPORT_DATA = "export_data"
    AI_CALL = "ai_call"
    ADMIN_ACTION = "admin_action"


class SecurityEventType(str, enum.Enum):
    """安全事件类型"""
    BRUTE_FORCE = "brute_force"         # 暴力破解
    SUSPICIOUS_LOGIN = "suspicious_login" # 异常登录
    RATE_LIMIT = "rate_limit"           # 频率限制
    IP_BLOCK = "ip_block"               # IP封禁
    ACCOUNT_LOCK = "account_lock"       # 账号锁定


# ═══════════════════════════════════════════════════════
# 会员权益配置
# ═══════════════════════════════════════════════════════

MEMBERSHIP_BENEFITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "免费版",
        "price": 0,
        "duration_days": 0,
        "ai_parse_daily": 10,
        "image_export_daily": 2,
        "excel_export_daily": 0,
        "storage_days": 15,
        "history_depth_months": 3,
        "features": [
            "全自动复盘表单",
            "每日大盘总览",
            "市场情绪统计",
            "热点板块复盘",
            "涨停梯队分层",
            "AI语音交易日记",
        ],
        "excluded": [
            "Excel结构化导出",
            "AI错误统计",
            "个人交易体系报告",
            "个股智能标签",
            "板块AI预判",
        ],
    },
    "monthly": {
        "name": "月卡会员",
        "price": 68,
        "original_price": 98,
        "duration_days": 30,
        "ai_parse_daily": 60,
        "image_export_daily": -1,  # -1 表示不限
        "excel_export_daily": 3,
        "storage_days": 90,
        "history_depth_months": 6,
        "features": [
            "免费版全部功能",
            "AI解析60次/天",
            "图片导出不限次",
            "Excel导出3次/天",
            "90天复盘存档",
            "6个月历史回溯",
            "个股智能标签",
            "板块AI预判",
            "精简/专业双视图",
        ],
    },
    "quarterly": {
        "name": "季卡会员",
        "price": 168,
        "original_price": 264,
        "duration_days": 90,
        "ai_parse_daily": 200,
        "image_export_daily": -1,
        "excel_export_daily": -1,
        "storage_days": 180,
        "history_depth_months": 12,
        "features": [
            "月卡全部功能",
            "AI解析200次/天",
            "Excel导出不限次",
            "180天复盘存档",
            "1年历史精准匹配",
            "AI错误归因分类",
            "交易节奏AI总结",
            "板块资金精细分析",
            "优先体验内测功能",
        ],
    },
    "yearly": {
        "name": "年卡至尊会员",
        "price": 498,
        "original_price": 816,
        "duration_days": 365,
        "ai_parse_daily": -1,
        "image_export_daily": -1,
        "excel_export_daily": -1,
        "storage_days": -1,  # 永久
        "history_depth_months": -1,  # 全周期
        "features": [
            "全功能、全AI、全导出无上限",
            "复盘数据永久存档",
            "全周期历史数据库",
            "个人交易体系AI报告",
            "交易胜率仪表盘",
            "全部未来迭代功能",
            "专属纯净体验",
        ],
    },
}


# ═══════════════════════════════════════════════════════
# 用户模型
# ═══════════════════════════════════════════════════════

class User(BaseModel):
    """用户基础模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=32)
    email: Optional[str] = None
    phone: Optional[str] = None
    password_hash: str = Field(..., description="bcrypt加密密码")
    status: UserStatus = UserStatus.ACTIVE
    membership_type: MembershipType = MembershipType.FREE
    membership_expire_at: Optional[datetime] = None
    is_trial: bool = Field(default=False, description="是否试用中")
    trial_expire_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    is_admin: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "trader001",
                "email": "trader@example.com",
                "membership_type": "free",
                "status": "active",
            }
        }


class UserProfile(BaseModel):
    """用户资料模型"""
    user_id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    real_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    bio: Optional[str] = Field(None, max_length=500)
    trading_experience: Optional[str] = None  # 交易经验年限
    preferred_style: Optional[str] = None     # 偏好交易风格
    risk_tolerance: Optional[str] = None      # 风险偏好
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════
# 会员模型
# ═══════════════════════════════════════════════════════

class MembershipTier(BaseModel):
    """会员等级定义"""
    type: MembershipType
    name: str
    price: float
    original_price: float = 0
    duration_days: int
    description: str = ""
    benefits: Dict[str, Any] = {}
    is_active: bool = True
    sort_order: int = 0


class MembershipPlan(BaseModel):
    """用户会员计划"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    membership_type: MembershipType
    start_at: datetime
    expire_at: datetime
    is_active: bool = True
    auto_renew: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════
# 订单模型
# ═══════════════════════════════════════════════════════

class Order(BaseModel):
    """充值订单"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_no: str = Field(default_factory=lambda: f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}")
    user_id: str
    membership_type: MembershipType
    amount: float
    original_amount: float = 0
    discount_amount: float = 0
    status: OrderStatus = OrderStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    paid_at: Optional[datetime] = None
    expire_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(minutes=30))
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PaymentRecord(BaseModel):
    """支付流水记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    user_id: str
    amount: float
    payment_method: PaymentMethod
    transaction_id: Optional[str] = None  # 第三方支付流水号
    status: str = "pending"
    paid_at: Optional[datetime] = None
    refund_amount: float = 0
    refund_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════
# 权限模型
# ═══════════════════════════════════════════════════════

class Permission(BaseModel):
    """权限定义"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., description="权限代码，如 ai_parse:unlimited")
    name: str
    category: PermissionCategory
    description: str = ""
    membership_required: Optional[MembershipType] = None
    is_active: bool = True


class UserPermission(BaseModel):
    """用户权限关联"""
    user_id: str
    permission_code: str
    granted_at: datetime = Field(default_factory=datetime.now)
    expire_at: Optional[datetime] = None
    granted_by: Optional[str] = None  # 管理员ID


class UsageQuota(BaseModel):
    """使用配额"""
    user_id: str
    quota_date: date = Field(default_factory=date.today, alias="date")
    ai_parse_count: int = 0
    ai_parse_limit: int = 10
    image_export_count: int = 0
    image_export_limit: int = 2
    excel_export_count: int = 0
    excel_export_limit: int = 0
    voice_journal_count: int = 0
    voice_journal_limit: int = 5

    class Config:
        populate_by_name = True


# ═══════════════════════════════════════════════════════
# 审计 & 安全模型
# ═══════════════════════════════════════════════════════

class AuditLog(BaseModel):
    """审计日志"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)


class SecurityEvent(BaseModel):
    """安全事件"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SecurityEventType
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    details: Dict[str, Any] = {}
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════
# 请求/响应模型
# ═══════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    invite_code: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    remember_me: bool = False


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=64)


class UpdateProfileRequest(BaseModel):
    """更新资料请求"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    trading_experience: Optional[str] = None
    preferred_style: Optional[str] = None
    risk_tolerance: Optional[str] = None


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24小时
    refresh_token: Optional[str] = None
    user: Dict[str, Any] = {}


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    user: User
    profile: Optional[UserProfile] = None
    membership: Dict[str, Any] = {}
    quotas: Dict[str, Any] = {}
    permissions: List[str] = []