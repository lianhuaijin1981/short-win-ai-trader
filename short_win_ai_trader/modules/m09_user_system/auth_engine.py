"""认证引擎 — 用户注册、登录、Token管理

提供JWT认证、密码加密、注册登录等核心认证功能。
"""

import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from short_win_ai_trader.modules.m09_user_system.models import (
    User, UserStatus, MembershipType, LoginRequest, RegisterRequest,
    TokenResponse, AuditAction
)


class AuthEngine:
    """认证引擎"""

    def __init__(self, secret_key: str = None, token_expire_hours: int = 24):
        self.secret_key = secret_key or os.environ.get("JWT_SECRET", "swat-secret-key-change-in-production")
        self.token_expire_hours = token_expire_hours
        self._users: Dict[str, User] = {}  # 内存存储，生产环境替换为数据库
        self._tokens: Dict[str, Dict] = {}  # token -> user_id mapping
        self._refresh_tokens: Dict[str, str] = {}  # refresh_token -> access_token

    # ── 密码管理 ────────────────────────────────────────

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        """使用bcrypt-style哈希密码"""
        if salt is None:
            salt = os.urandom(16).hex()
        # 使用PBKDF2进行密码哈希
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}${hashed.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, hashed = password_hash.split('$')
            expected = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            return hmac.compare_digest(hashed, expected)
        except (ValueError, AttributeError):
            return False

    # ── Token管理 ───────────────────────────────────────

    def generate_token(self, user_id: str, is_admin: bool = False) -> Tuple[str, str]:
        """生成access_token和refresh_token"""
        access_token = f"eyJhbGciOiJIUzI1NiJ9.{uuid.uuid4().hex}.{int(time.time())}"
        refresh_token = f"rt_{uuid.uuid4().hex}"

        expire_at = datetime.now() + timedelta(hours=self.token_expire_hours)

        self._tokens[access_token] = {
            "user_id": user_id,
            "is_admin": is_admin,
            "expire_at": expire_at.isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        self._refresh_tokens[refresh_token] = access_token

        return access_token, refresh_token

    def validate_token(self, token: str) -> Optional[Dict]:
        """验证token并返回payload"""
        if token not in self._tokens:
            return None

        token_data = self._tokens[token]
        expire_at = datetime.fromisoformat(token_data["expire_at"])

        if datetime.now() > expire_at:
            del self._tokens[token]
            return None

        return token_data

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """使用refresh_token获取新的access_token"""
        if refresh_token not in self._refresh_tokens:
            return None

        old_access_token = self._refresh_tokens[refresh_token]
        if old_access_token not in self._tokens:
            del self._refresh_tokens[refresh_token]
            return None

        user_id = self._tokens[old_access_token]["user_id"]
        is_admin = self._tokens[old_access_token]["is_admin"]

        # 删除旧token
        del self._tokens[old_access_token]
        del self._refresh_tokens[refresh_token]

        return self.generate_token(user_id, is_admin)

    def revoke_token(self, token: str):
        """撤销token"""
        if token in self._tokens:
            user_id = self._tokens[token]["user_id"]
            del self._tokens[token]
            # 同时删除关联的refresh_token
            for rt, at in list(self._refresh_tokens.items()):
                if at == token:
                    del self._refresh_tokens[rt]

    # ── 用户注册 ────────────────────────────────────────

    def register(self, req: RegisterRequest) -> Tuple[bool, str, Optional[User]]:
        """
        注册新用户
        返回: (success, message, user)
        """
        # 检查用户名
        for user in self._users.values():
            if user.username == req.username:
                return False, "用户名已存在", None
            if req.email and user.email == req.email:
                return False, "邮箱已被注册", None
            if req.phone and user.phone == req.phone:
                return False, "手机号已被注册", None

        # 创建用户
        password_hash = self.hash_password(req.password)
        user = User(
            username=req.username,
            email=req.email,
            phone=req.phone,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
            membership_type=MembershipType.FREE,
            is_trial=True,  # 新用户7天试用
            trial_expire_at=datetime.now() + timedelta(days=7),
        )

        self._users[user.id] = user
        return True, "注册成功，已赠送7天季卡体验", user

    # ── 用户登录 ────────────────────────────────────────

    def login(self, req: LoginRequest, ip_address: str = None) -> Tuple[bool, str, Optional[TokenResponse]]:
        """
        用户登录
        返回: (success, message, token_response)
        """
        # 查找用户
        user = None
        for u in self._users.values():
            if u.username == req.username or u.email == req.username or u.phone == req.username:
                user = u
                break

        if not user:
            return False, "用户名或密码错误", None

        # 检查状态
        if user.status == UserStatus.BANNED:
            return False, "账号已被封禁", None
        if user.status == UserStatus.INACTIVE:
            return False, "账号已停用", None

        # 验证密码
        if not self.verify_password(req.password, user.password_hash):
            return False, "用户名或密码错误", None

        # 检查试用是否过期
        self._check_trial_expiry(user)

        # 更新登录信息
        user.last_login_at = datetime.now()
        user.login_count += 1
        user.updated_at = datetime.now()

        # 生成token
        access_token, refresh_token = self.generate_token(user.id, user.is_admin)

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.token_expire_hours * 3600,
            user={
                "id": user.id,
                "username": user.username,
                "membership_type": user.membership_type.value,
                "is_trial": user.is_trial,
                "is_admin": user.is_admin,
            }
        )

        return True, "登录成功", token_response

    def logout(self, token: str):
        """用户登出"""
        self.revoke_token(token)

    # ── 密码修改 ────────────────────────────────────────

    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """修改密码"""
        user = self._users.get(user_id)
        if not user:
            return False, "用户不存在"

        if not self.verify_password(old_password, user.password_hash):
            return False, "原密码错误"

        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.now()

        # 撤销所有token，强制重新登录
        for token in list(self._tokens.keys()):
            if self._tokens[token]["user_id"] == user_id:
                del self._tokens[token]

        return True, "密码修改成功"

    # ── 用户查询 ────────────────────────────────────────

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """从token获取用户ID"""
        payload = self.validate_token(token)
        return payload["user_id"] if payload else None

    def list_users(self, page: int = 1, page_size: int = 20) -> Tuple[List[User], int]:
        """获取用户列表（管理员）"""
        users = list(self._users.values())
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        return users[start:end], total

    # ── 用户管理（管理员） ──────────────────────────────

    def update_user_status(self, user_id: str, status: UserStatus, admin_id: str) -> Tuple[bool, str]:
        """更新用户状态"""
        user = self._users.get(user_id)
        if not user:
            return False, "用户不存在"

        user.status = status
        user.updated_at = datetime.now()

        if status == UserStatus.BANNED:
            # 封禁时撤销所有token
            for token in list(self._tokens.keys()):
                if self._tokens[token]["user_id"] == user_id:
                    del self._tokens[token]

        return True, f"用户状态已更新为: {status.value}"

    def set_user_admin(self, user_id: str, is_admin: bool) -> Tuple[bool, str]:
        """设置管理员权限"""
        user = self._users.get(user_id)
        if not user:
            return False, "用户不存在"

        user.is_admin = is_admin
        user.updated_at = datetime.now()
        return True, f"管理员权限已{'授予' if is_admin else '撤销'}"

    # ── 内部方法 ────────────────────────────────────────

    def _check_trial_expiry(self, user: User):
        """检查试用是否过期"""
        if user.is_trial and user.trial_expire_at:
            if datetime.now() > user.trial_expire_at:
                user.is_trial = False
                user.membership_type = MembershipType.FREE
                user.membership_expire_at = None
                user.updated_at = datetime.now()

    def get_user_count(self) -> int:
        """获取用户总数"""
        return len(self._users)

    def get_active_user_count(self) -> int:
        """获取活跃用户数"""
        return sum(1 for u in self._users.values() if u.status == UserStatus.ACTIVE)


# 全局单例
_auth_engine: Optional[AuthEngine] = None


def get_auth_engine() -> AuthEngine:
    """获取认证引擎单例"""
    global _auth_engine
    if _auth_engine is None:
        _auth_engine = AuthEngine()
    return _auth_engine