"""认证 API 路由."""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from web.server.auth.mac_auth import authenticate, is_arp_miss, USER_PINS_PATH
from web.server.api.deps import create_token, get_current_user
from web.server.state import UserSession

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str


class UserEntry(BaseModel):
    username: str
    role: str = "operator"
    display_name: str = ""
    mac_addresses: list[str]


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    """用户名 + MAC 地址免密登录."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    result = authenticate(req.username, client_ip)
    if result is None:
        if is_arp_miss(client_ip):
            raise HTTPException(
                status_code=425,
                detail="正在获取设备信息，请重试",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前设备未注册",
        )

    token = create_token(
        username=req.username,
        role=result["role"],
        display_name=result.get("display_name", req.username),
    )
    expire = datetime.utcnow() + timedelta(hours=8)

    return {
        "token": token,
        "expires_at": expire.isoformat(),
        "role": result["role"],
        "display_name": result.get("display_name", req.username),
    }


@router.get("/users")
async def list_users(current: UserSession = Depends(get_current_user)):
    """列出所有用户（仅 admin）."""
    if current.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    if not USER_PINS_PATH.exists():
        return []
    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    return [
        {"username": k, "role": v.get("role"), "display_name": v.get("display_name", k),
         "mac_addresses": v.get("mac_addresses", [])}
        for k, v in users.items()
    ]


@router.post("/users")
async def create_user(entry: UserEntry, current: UserSession = Depends(get_current_user)):
    """新增用户（仅 admin）."""
    if current.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    users = {}
    if USER_PINS_PATH.exists():
        with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
            users = json.load(f)
    users[entry.username] = {
        "role": entry.role,
        "display_name": entry.display_name or entry.username,
        "mac_addresses": [m.upper() for m in entry.mac_addresses],
    }
    with open(USER_PINS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True}


@router.put("/users/{username}")
async def update_user(username: str, entry: UserEntry, current: UserSession = Depends(get_current_user)):
    """修改用户（仅 admin）."""
    if current.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    if not USER_PINS_PATH.exists():
        raise HTTPException(status_code=404, detail="用户不存在")
    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    if username not in users:
        raise HTTPException(status_code=404, detail="用户不存在")
    if entry.role:
        users[username]["role"] = entry.role
    if entry.display_name:
        users[username]["display_name"] = entry.display_name
    if entry.mac_addresses:
        users[username]["mac_addresses"] = [m.upper() for m in entry.mac_addresses]
    with open(USER_PINS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True}


@router.delete("/users/{username}")
async def delete_user(username: str, current: UserSession = Depends(get_current_user)):
    """删除用户（仅 admin）."""
    if current.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    if not USER_PINS_PATH.exists():
        raise HTTPException(status_code=404, detail="用户不存在")
    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    users.pop(username, None)
    with open(USER_PINS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True}
