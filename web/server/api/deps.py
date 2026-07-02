"""FastAPI 依赖注入 — JWT 验证与会话获取."""
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from web.server.state import session_manager, UserSession

SECRET_KEY = os.environ.get("JWT_SECRET", "ee-autotool-web-2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8

security = HTTPBearer(auto_error=False)


def create_token(username: str, role: str, display_name: str) -> str:
    """生成 JWT."""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": username,
        "role": role,
        "display_name": display_name,
        "iat": datetime.utcnow(),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserSession:
    """从 JWT 解析当前用户并返回其会话."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证令牌")

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "operator")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期")

    return session_manager.get_or_create(username, role)
