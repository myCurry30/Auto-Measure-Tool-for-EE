# EE Power On AutoTool Web 版 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 PySide6 桌面应用完整移植为 FastAPI + React Web 架构，支持局域网多人并发使用。

**Architecture:** FastAPI 后端复用现有 `core/` 业务层（不改动），每个用户通过 `SessionManager` 持有独立的 VISA 连接和 Excel 实例。React + Ant Design 前端通过 REST API + WebSocket 与后端通信。认证采用用户名 + ARP MAC 地址自动验证。

**Tech Stack:** Python 3.12, FastAPI, PyVISA, win32com, React 18, TypeScript, Ant Design 5, Vite, JWT (python-jose)

## Global Constraints

- 不修改 `core/` 下的任何文件
- 所有后端阻塞操作（VISA/COM）必须用 `asyncio.to_thread()` 包装
- 每个 API 请求通过 JWT 识别用户，注入到 `SessionManager`
- `user_pins.json` 全局读写用 `threading.Lock` 保护
- 前端未登录时所有路由重定向到 `/login`
- 服务器 bind `0.0.0.0:8000`，前端开发时 Vite dev server 独立运行

---

### Task 1: 项目脚手架 — 目录结构 + 依赖

**Files:**
- Create: `web/server/__init__.py`
- Create: `web/server/main.py` (骨架)
- Create: `web/server/state.py` (骨架)
- Create: `web/client/` (Vite 脚手架)
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `web/server/main.py:app` (FastAPI 实例), `web/server/state.py:SessionManager` (空类)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p web/server/api web/server/auth web/client
```

- [ ] **Step 2: 更新 requirements.txt**

在现有 `requirements.txt` 末尾追加：

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.9
websockets>=12.0
```

- [ ] **Step 3: 创建 FastAPI 入口骨架**

```python
# web/server/__init__.py

# web/server/main.py
"""EE Power On AutoTool — Web 版 FastAPI 入口."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭生命周期."""
    print("[web] 服务器启动 — bind 0.0.0.0:8000")
    yield
    print("[web] 服务器关闭")


app = FastAPI(
    title="EE Power On AutoTool API",
    version="3.0.0-web",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段；生产改为具体地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 创建 SessionManager 骨架**

```python
# web/server/state.py
"""后端全局状态管理 — 多用户会话隔离."""
import threading
import asyncio
from dataclasses import dataclass, field


@dataclass
class UserSession:
    """单个用户的会话状态."""
    username: str
    role: str = "operator"
    osc: object | None = None       # OscilloscopeBase 实例
    xls: object | None = None       # EasyExcel 实例
    rm: object | None = None        # PyVISA ResourceManager
    test_type: str = "sequence"
    row: int = 0
    total: int = 0
    current_item: str = ""
    pn_direction: str = "P"
    state: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    log_queue: asyncio.Queue = field(default_factory=asyncio.Queue)


class SessionManager:
    """全局单例 — 管理所有用户会话."""

    def __init__(self):
        self._sessions: dict[str, UserSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, username: str, role: str = "operator") -> UserSession:
        with self._lock:
            if username not in self._sessions:
                self._sessions[username] = UserSession(username=username, role=role)
            return self._sessions[username]

    def get(self, username: str) -> UserSession | None:
        with self._lock:
            return self._sessions.get(username)

    def remove(self, username: str):
        with self._lock:
            self._sessions.pop(username, None)


session_manager = SessionManager()
```

- [ ] **Step 5: 用 Vite 创建 React + TypeScript 前端项目**

```bash
cd web/client
npm create vite@latest . -- --template react-ts
npm install
npm install antd @ant-design/icons react-router-dom
```

- [ ] **Step 6: 验证脚手架 — 启动后端**

```bash
cd web/server
uvicorn main:app --host 0.0.0.0 --port 8000
# 浏览器打开 http://localhost:8000/api/health → {"status": "ok"}
```

- [ ] **Step 7: 验证前端启动**

```bash
cd web/client
npm run dev
# 浏览器打开 http://localhost:5173 → Vite 默认页面
```

- [ ] **Step 8: Commit**

```bash
git add web/ requirements.txt
git commit -m "feat(web): scaffold FastAPI backend + Vite React frontend"
```

---

### Task 2: 日志桥接 — WebSocket 日志管道

**Files:**
- Create: `web/server/log_bridge.py`
- Modify: `web/server/main.py`

**Interfaces:**
- Produces: `LogBridge.attach(session)` — 将日志重定向到指定用户会话的 WebSocket 队列

- [ ] **Step 1: 实现 LogBridge**

```python
# web/server/log_bridge.py
"""将 Python logging 消息桥接到 WebSocket 用户队列."""
import logging
import asyncio
import json
from datetime import datetime

from web.server.state import UserSession


class _WsLogHandler(logging.Handler):
    """自定义 logging Handler — 将日志推入用户队列."""

    def __init__(self, session: UserSession):
        super().__init__()
        self._session = session
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            entry = {
                "type": "log",
                "level": record.levelname.lower(),
                "message": msg,
                "ts": datetime.now().strftime("%H:%M:%S"),
            }
            # 用 call_soon_threadsafe 从任意线程推入 async queue
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(
                self._session.log_queue.put_nowait, json.dumps(entry)
            )
        except Exception:
            pass  # 日志失败不影响主流程


class LogBridge:
    """管理各用户日志 handler 的生命周期."""

    @staticmethod
    def attach(session: UserSession, logger_name: str = "core"):
        """将指定 logger 的输出桥接到用户会话."""
        handler = _WsLogHandler(session)
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        return handler

    @staticmethod
    def detach(handler: logging.Handler, logger_name: str = "core"):
        """移除 handler."""
        logging.getLogger(logger_name).removeHandler(handler)
```

- [ ] **Step 2: 验证 LogBridge**

```bash
python -c "
import logging, asyncio
from web.server.state import UserSession
from web.server.log_bridge import LogBridge

session = UserSession(username='test', role='operator')
handler = LogBridge.attach(session)
logging.getLogger('core').info('test log message')
LogBridge.detach(handler)
print('OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add web/server/log_bridge.py
git commit -m "feat(web): add LogBridge for per-user WebSocket log streaming"
```

---

### Task 3: 认证系统 — MAC 地址验证 + JWT

**Files:**
- Create: `web/server/auth/__init__.py`
- Create: `web/server/auth/mac_auth.py` (阶段 1: MAC 验证)
- Create: `web/server/auth/ldap.py` (阶段 3 预留)
- Create: `web/server/api/auth.py` (路由 + 用户管理)
- Create: `web/server/api/deps.py` (get_current_user 依赖)

**Interfaces:**
- Consumes: `web/server/state.py:session_manager`
- Produces: `get_current_user(token)` → `UserSession`, `POST /api/auth/login`, 用户 CRUD

- [ ] **Step 1: 实现 MAC 地址解析**

```python
# web/server/auth/mac_auth.py
"""阶段 1: 基于 MAC 地址的免密认证."""
import subprocess
import re
import json
import threading
from pathlib import Path

_ARP_CACHE: dict[str, str] = {}  # ip → mac 短期缓存
_ARP_LOCK = threading.Lock()

USER_PINS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "user_pins.json"


def get_mac_from_ip(ip: str) -> str | None:
    """通过 ARP 表解析 IP → MAC 地址（Windows）."""
    with _ARP_LOCK:
        cached = _ARP_CACHE.get(ip)
        if cached:
            return cached

    try:
        # 先 ping 预热 ARP
        subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            capture_output=True, timeout=2,
        )
        result = subprocess.run(
            ["arp", "-a", ip],
            capture_output=True, text=True, timeout=5,
        )
        match = re.search(
            r"([0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}"
            r"[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2})",
            result.stdout,
        )
        if match:
            mac = match.group(1).replace("-", ":").upper()
            with _ARP_LOCK:
                _ARP_CACHE[ip] = mac
            return mac
    except Exception:
        pass
    return None


def authenticate(username: str, client_ip: str) -> dict | None:
    """验证用户名 + 客户端 MAC.

    Returns:
        {"role": "operator", "display_name": username} 或 None
    """
    if not USER_PINS_PATH.exists():
        return None

    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)

    user = users.get(username)
    if not user:
        return None

    expected_macs = [m.upper() for m in user.get("mac_addresses", [])]
    if not expected_macs:
        return None

    actual_mac = get_mac_from_ip(client_ip)
    if actual_mac is None:
        # ARP 未命中 — 返回特殊标记让调用方重试
        return None  # caller should check get_mac_from_ip separately

    if actual_mac not in expected_macs:
        return None

    return {
        "role": user.get("role", "operator"),
        "display_name": user.get("display_name", username),
    }


def is_arp_miss(ip: str) -> bool:
    """检查是否因为 ARP 未命中导致 MAC 获取失败."""
    return get_mac_from_ip(ip) is None
```

- [ ] **Step 2: 实现 JWT 工具 + 依赖注入**

```python
# web/server/api/deps.py
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
```

- [ ] **Step 3: 实现认证路由**

```python
# web/server/api/auth.py
"""认证 API 路由."""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from web.server.auth.mac_auth import authenticate, is_arp_miss
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
    from datetime import datetime, timedelta
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
    import json
    from web.server.auth.mac_auth import USER_PINS_PATH
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
    import json
    from web.server.auth.mac_auth import USER_PINS_PATH
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
    import json
    from web.server.auth.mac_auth import USER_PINS_PATH
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
    import json
    from web.server.auth.mac_auth import USER_PINS_PATH
    if not USER_PINS_PATH.exists():
        raise HTTPException(status_code=404, detail="用户不存在")
    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    users.pop(username, None)
    with open(USER_PINS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True}
```

- [ ] **Step 4: 注册路由到 main.py**

在 `web/server/main.py` 的 `app` 创建之后、`CORS` 中间件之后添加：

```python
from web.server.api.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 5: 创建初始 user_pins.json**

```json
{
  "admin": {
    "role": "admin",
    "display_name": "管理员",
    "mac_addresses": ["00:00:00:00:00:00"]
  }
}
```

注：初始 MAC 地址为占位符，部署时由管理员替换为实际笔记本 MAC。

- [ ] **Step 6: 验证认证流程**

```bash
# 启动服务器
uvicorn web.server.main:app --host 0.0.0.0 --port 8000

# 测试登录（无匹配 MAC → 403）
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin"}'
# → {"detail": "当前设备未注册"}

# 用 admin token 添加用户（需要先临时给自己加 MAC）
# 手动编辑 user_pins.json，把 MAC 改成你当前的 MAC
# 再试登录 → 200 带 token
```

- [ ] **Step 7: Commit**

```bash
git add web/server/auth/ web/server/api/auth.py web/server/api/deps.py web/server/main.py user_pins.json
git commit -m "feat(web): add MAC address auth + JWT + user CRUD API"
```

---

### Task 4: 连接 API — VISA 扫描/连接/心跳

**Files:**
- Create: `web/server/api/connect.py`
- Modify: `web/server/main.py`

**Interfaces:**
- Consumes: `web/server/api/deps.py:get_current_user`, `web/server/state.py:session_manager`
- Produces: `POST /api/connect`, `DELETE /api/connect`, `GET /api/connect/status`

- [ ] **Step 1: 实现连接 API**

```python
# web/server/api/connect.py
"""示波器连接 API — 复用 core.instrument_manager."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from web.server.api.deps import get_current_user
from web.server.state import UserSession
from web.server.log_bridge import LogBridge

router = APIRouter(prefix="/api/connect", tags=["connect"])


class ConnectRequest(BaseModel):
    method: str  # "usb_gpib" | "ip"
    ip: str = ""
    port: int = 4000
    use_socket: bool = False


@router.post("")
async def connect(req: ConnectRequest, current: UserSession = Depends(get_current_user)):
    """连接示波器."""
    import logging
    log = logging.getLogger("core")

    if current.osc is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已有连接，请先断开")

    def _connect():
        if req.method == "usb_gpib":
            from core.instrument_manager import connect_usb_gpib
            return connect_usb_gpib()
        else:
            from core.instrument_manager import connect_ip
            return connect_ip(req.ip, req.port, req.use_socket)

    try:
        osc, model, addr, rm = await asyncio.to_thread(_connect)
        current.osc = osc
        current.rm = rm
        current.state["model"] = model
        current.state["addr"] = addr
        # 挂载日志桥
        LogBridge.attach(current, "core")
        return {"connected": True, "model": model, "addr": addr}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("")
async def disconnect(current: UserSession = Depends(get_current_user)):
    """断开示波器连接."""
    if current.osc is not None:
        try:
            await asyncio.to_thread(current.osc.write, "*RST")
        except Exception:
            pass
        current.osc = None
        current.rm = None
    return {"connected": False}


@router.get("/status")
async def status(current: UserSession = Depends(get_current_user)):
    """查询连接状态."""
    if current.osc is None:
        return {"connected": False}
    try:
        idn = await asyncio.to_thread(current.osc.query, "*IDN?")
        return {
            "connected": True,
            "model": current.state.get("model", ""),
            "addr": current.state.get("addr", ""),
        }
    except Exception:
        return {"connected": False}
```

- [ ] **Step 2: 注册路由**

在 `web/server/main.py` 中添加：

```python
from web.server.api.connect import router as connect_router
app.include_router(connect_router)
```

- [ ] **Step 3: Commit**

```bash
git add web/server/api/connect.py web/server/main.py
git commit -m "feat(web): add oscilloscope connect/disconnect/status API"
```

---

### Task 5: Excel API — 文件打开/读写/Sheet 切换

**Files:**
- Create: `web/server/api/excel.py`
- Modify: `web/server/main.py`

**Interfaces:**
- Consumes: `web/server/api/deps.py:get_current_user`
- Produces: `POST /api/excel/open`, `GET /api/excel/info`, `GET /api/excel/sheet-names`, etc.

- [ ] **Step 1: 实现 Excel API**

```python
# web/server/api/excel.py
"""Excel 操作 API — 复用 core.easy_excel.EasyExcel."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from web.server.api.deps import get_current_user
from web.server.state import UserSession

router = APIRouter(prefix="/api/excel", tags=["excel"])


class OpenRequest(BaseModel):
    file_path: str


class CellWrite(BaseModel):
    row: int
    col: int
    value: str


class ActivateSheet(BaseModel):
    sheet_name: str


@router.post("/open")
async def open_excel(req: OpenRequest, current: UserSession = Depends(get_current_user)):
    """打开 Excel 文件."""
    def _open():
        from core.easy_excel import EasyExcel
        return EasyExcel(req.file_path)

    try:
        xls = await asyncio.to_thread(_open)
        current.xls = xls
        current.state["file_path"] = req.file_path
        return {
            "file_path": req.file_path,
            "active_sheet": xls.ws.Name if hasattr(xls, 'ws') else "",
            "sheet_names": xls.get_sheet_names(),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/info")
async def excel_info(current: UserSession = Depends(get_current_user)):
    """获取当前 Excel 信息."""
    if current.xls is None:
        return {"file_path": "", "sheet_names": [], "active_sheet": ""}
    try:
        sheet_names = await asyncio.to_thread(current.xls.get_sheet_names)
        return {
            "file_path": current.state.get("file_path", ""),
            "sheet_names": sheet_names,
            "active_sheet": current.state.get("sheet_name", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/activate-sheet")
async def activate_sheet(req: ActivateSheet, current: UserSession = Depends(get_current_user)):
    """切换当前 Sheet."""
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")
    try:
        await asyncio.to_thread(current.xls.activate_sheet, req.sheet_name)
        current.state["sheet_name"] = req.sheet_name
        return {"active_sheet": req.sheet_name, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sheet-names")
async def sheet_names(current: UserSession = Depends(get_current_user)):
    """获取所有 Sheet 名称."""
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")
    try:
        names = await asyncio.to_thread(current.xls.get_sheet_names)
        return names
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/cell")
async def read_cell(row: int, col: int, current: UserSession = Depends(get_current_user)):
    """读取单元格."""
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")
    try:
        val = await asyncio.to_thread(current.xls.getCell, row, col)
        return {"row": row, "col": col, "value": str(val) if val is not None else ""}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/cell")
async def write_cell(req: CellWrite, current: UserSession = Depends(get_current_user)):
    """写入单元格."""
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")
    try:
        await asyncio.to_thread(current.xls.setCell, req.row, req.col, req.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
```

- [ ] **Step 2: 注册路由**

```python
from web.server.api.excel import router as excel_router
app.include_router(excel_router)
```

- [ ] **Step 3: Commit**

```bash
git add web/server/api/excel.py web/server/main.py
git commit -m "feat(web): add Excel open/read/write/sheet-switch API"
```

---

### Task 6: 测量 API — Sequence/Monotony + 导航

**Files:**
- Create: `web/server/api/measure.py`
- Modify: `web/server/main.py`

**Interfaces:**
- Consumes: `core.measurement`, `core.capture`, `core.test_manager`, `web/server/api/deps.py:get_current_user`
- Produces: `POST /api/measure/go|last|next|jump`, `GET /api/measure/status`, `PUT /api/measure/config`

- [ ] **Step 1: 实现测量 API**

```python
# web/server/api/measure.py
"""测量操作 API — 复用 core.measurement + core.capture + core.test_manager."""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from web.server.api.deps import get_current_user
from web.server.state import UserSession

router = APIRouter(prefix="/api/measure", tags=["measure"])
log = logging.getLogger("core")


class JumpRequest(BaseModel):
    target_row: int


class ConfigRequest(BaseModel):
    test_type: str = "sequence"
    init_row: int = 1
    # 信号配置
    signal1_enabled: bool = True
    signal2_enabled: bool = False
    signal3_enabled: bool = False
    signal4_enabled: bool = False
    signal1_col: str = "A"
    signal2_col: str = "B"
    signal3_col: str = "C"
    signal4_col: str = "D"
    # 通道标签
    ch1_label: str = ""
    ch2_label: str = ""
    ch3_label: str = ""
    ch4_label: str = ""
    ch1_enabled: bool = True
    ch2_enabled: bool = False
    ch3_enabled: bool = False
    ch4_enabled: bool = False
    # MSO 配置
    hor_mode: str = "AUTO"
    hor_scale: str = ""
    hor_pos: str = ""
    ch1_scale: str = ""
    ch2_scale: str = ""
    ch3_scale: str = ""
    ch4_scale: str = ""
    # P/N 方向
    pn_direction: int = 1
    # 列配置
    data_col: str = "A"
    seq_pic_col: str = "B"
    mono_p_pic_col: str = "B"
    mono_n_pic_col: str = "C"


def _measure_go(session: UserSession):
    """执行一次完整测量流程（阻塞，在 to_thread 中运行）."""
    state = session.state
    state.setdefault("test_type", session.test_type)
    state.setdefault("pn_direction", session.pn_direction)
    state.setdefault("row", session.row)

    from core.measurement import measure_sequence, measure_monotony, common_set, channel_Lable_set
    from core.capture import Capture_Pic
    from core.test_manager import go
    from core.easy_excel import EasyExcel

    osc = session.osc
    xls = session.xls

    # 公共设置
    common_set(osc, False, False)  # dpo7000, dpo5104b flags — MSO5 系列默认
    channel_Lable_set(
        osc,
        state.get("ch1_label", ""),
        state.get("ch2_label", ""),
        state.get("ch3_label", ""),
        state.get("ch4_label", ""),
    )

    # 执行测量配置
    if session.test_type == "sequence":
        measure_sequence(osc, True)  # mso5=True for MSO4/5/6
    else:
        measure_monotony(osc, True)

    # 截图 + 数据采集
    file_path = state.get("file_path", "")
    sheet_name = state.get("sheet_name", "")
    signals = [
        state.get("signal1_name", "CH1"),
        state.get("signal2_name", "CH2"),
        state.get("signal3_name", "CH3"),
        state.get("signal4_name", "CH4"),
    ]
    signal_enables = [
        state.get("signal1_enabled", True),
        state.get("signal2_enabled", False),
        state.get("signal3_enabled", False),
        state.get("signal4_enabled", False),
    ]

    Capture_Pic(osc, xls, sheet_name, signals, signal_enables, state)
    return go(file_path, state)


@router.post("/go")
async def go_measure(current: UserSession = Depends(get_current_user)):
    """执行一次测量."""
    if current.osc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先连接示波器")
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")

    try:
        result = await asyncio.to_thread(_measure_go, current)
        return {"status": "ok", "row": current.row, "item": current.current_item}
    except Exception as e:
        log.error(f"测量失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/last")
async def last(current: UserSession = Depends(get_current_user)):
    """上一条."""
    from core.test_manager import Last
    try:
        Last(current.state)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/next")
async def next(current: UserSession = Depends(get_current_user)):
    """下一条."""
    from core.test_manager import Next
    try:
        Next(current.state)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/jump")
async def jump(req: JumpRequest, current: UserSession = Depends(get_current_user)):
    """跳转到指定行."""
    from core.test_manager import jump as do_jump
    try:
        do_jump(current.state, req.target_row)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status")
async def measure_status(current: UserSession = Depends(get_current_user)):
    """查询当前测量状态."""
    return {
        "test_type": current.test_type,
        "row": current.state.get("row", 0),
        "total": current.state.get("total", 0),
        "current_item": current.state.get("current_item", ""),
        "pn_direction": current.state.get("pn_direction", "P"),
    }


@router.put("/config")
async def update_config(req: ConfigRequest, current: UserSession = Depends(get_current_user)):
    """更新测量配置."""
    current.test_type = req.test_type
    current.pn_direction = req.pn_direction
    current.row = req.init_row
    s = current.state
    s.update({
        "test_type": req.test_type,
        "init_row": req.init_row,
        "pn_direction": req.pn_direction,
        "signal1_name": "CH1", "signal2_name": "CH2",
        "signal3_name": "CH3", "signal4_name": "CH4",
        "signal1_col": req.signal1_col, "signal2_col": req.signal2_col,
        "signal3_col": req.signal3_col, "signal4_col": req.signal4_col,
        "signal1_enabled": req.signal1_enabled, "signal2_enabled": req.signal2_enabled,
        "signal3_enabled": req.signal3_enabled, "signal4_enabled": req.signal4_enabled,
        "ch1_label": req.ch1_label, "ch2_label": req.ch2_label,
        "ch3_label": req.ch3_label, "ch4_label": req.ch4_label,
        "ch1_enabled": req.ch1_enabled, "ch2_enabled": req.ch2_enabled,
        "ch3_enabled": req.ch3_enabled, "ch4_enabled": req.ch4_enabled,
        "hor_mode": req.hor_mode, "hor_scale": req.hor_scale, "hor_pos": req.hor_pos,
        "ch1_scale": req.ch1_scale, "ch2_scale": req.ch2_scale,
        "ch3_scale": req.ch3_scale, "ch4_scale": req.ch4_scale,
        "data_col": req.data_col, "seq_pic_col": req.seq_pic_col,
        "mono_p_pic_col": req.mono_p_pic_col, "mono_n_pic_col": req.mono_n_pic_col,
    })
    return {"ok": True}
```

- [ ] **Step 2: 注册路由**

```python
from web.server.api.measure import router as measure_router
app.include_router(measure_router)
```

- [ ] **Step 3: Commit**

```bash
git add web/server/api/measure.py web/server/main.py
git commit -m "feat(web): add measure go/last/next/jump/config API"
```

---

### Task 7: 配置管理 API + WebSocket 实时推送

**Files:**
- Create: `web/server/api/config.py`
- Create: `web/server/api/ws.py`
- Modify: `web/server/main.py`

**Interfaces:**
- Produces: `GET/POST /api/config/*`, `WebSocket /ws?token=<jwt>`

- [ ] **Step 1: 实现配置 API**

```python
# web/server/api/config.py
"""配置管理 API — 导入/导出 config.json."""
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from web.server.api.deps import get_current_user
from web.server.state import UserSession

router = APIRouter(prefix="/api/config", tags=["config"])
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config.json"


class ImportRequest(BaseModel):
    file_path: str


class ExportRequest(BaseModel):
    file_path: str


class ApplyRequest(BaseModel):
    sheet_name: str


@router.get("/current")
async def get_config(current: UserSession = Depends(get_current_user)):
    """获取当前会话的完整配置."""
    return current.config


@router.post("/import")
async def import_config(req: ImportRequest, current: UserSession = Depends(get_current_user)):
    """从 JSON 文件导入配置."""
    src = Path(req.file_path)
    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置文件不存在")
    try:
        def _load():
            with open(src, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await asyncio.to_thread(_load)
        current.config.update(data)
        return {"ok": True, "keys": list(data.keys())}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/export")
async def export_config(req: ExportRequest, current: UserSession = Depends(get_current_user)):
    """导出当前配置到 JSON 文件."""
    try:
        def _save():
            with open(req.file_path, "w", encoding="utf-8") as f:
                json.dump(current.config, f, ensure_ascii=False, indent=2)
        await asyncio.to_thread(_save)
        return {"ok": True, "path": req.file_path}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/apply")
async def apply_config(req: ApplyRequest, current: UserSession = Depends(get_current_user)):
    """应用某个 sheet 的保存配置."""
    key = f"{req.sheet_name}|{current.test_type}"
    sheet_cfg = current.config.get(key, {})
    if not sheet_cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"未找到 {key} 的配置")
    current.state.update(sheet_cfg)
    return {"ok": True, "applied": key}
```

- [ ] **Step 2: 实现 WebSocket 端点**

```python
# web/server/api/ws.py
"""WebSocket — 按用户隔离的实时推送."""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from jose import JWTError, jwt

from web.server.api.deps import SECRET_KEY, ALGORITHM
from web.server.state import session_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """按用户推送日志和状态."""
    # 验证 JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    session = session_manager.get(username)
    if session is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    # 心跳任务
    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(5)
                connected = session.osc is not None
                await websocket.send_json({
                    "type": "heartbeat",
                    "connected": connected,
                    "model": session.state.get("model", ""),
                    "scope_addr": session.state.get("addr", ""),
                })
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    # 日志推送
    try:
        while True:
            try:
                msg = await asyncio.wait_for(session.log_queue.get(), timeout=1.0)
                await websocket.send_text(msg)
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass
```

- [ ] **Step 3: 注册路由**

```python
from web.server.api.config import router as config_router
from web.server.api.ws import router as ws_router

app.include_router(config_router)
app.include_router(ws_router)
```

- [ ] **Step 4: Commit**

```bash
git add web/server/api/config.py web/server/api/ws.py web/server/main.py
git commit -m "feat(web): add config import/export API + per-user WebSocket"
```

---

### Task 8: 前端基础 — App Shell + 路由 + AuthContext

**Files:**
- Create: `web/client/src/services/auth.ts`
- Create: `web/client/src/contexts/AuthContext.tsx`
- Create: `web/client/src/layouts/AppLayout.tsx`
- Modify: `web/client/src/App.tsx`
- Modify: `web/client/src/main.tsx`
- Create: `web/client/.env`

**Interfaces:**
- Produces: `AuthContext` (login/user/token), `<AppLayout>` (sidebar + content + statusbar)

- [ ] **Step 1: API 服务层**

```typescript
// web/client/src/services/auth.ts
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface LoginResponse {
  token: string;
  expires_at: string;
  role: string;
  display_name: string;
}

export async function login(username: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  if (res.status === 425) {
    // ARP 未命中，等 2 秒重试
    await new Promise((r) => setTimeout(r, 2000));
    return login(username);
  }
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "登录失败");
  }
  return res.json();
}

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

export function logout(): void {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

export function getStoredUser(): { username: string; role: string; display_name: string } | null {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function setStoredUser(user: { username: string; role: string; display_name: string }): void {
  localStorage.setItem("user", JSON.stringify(user));
}

// 通用 fetch 封装（自动带 token）
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}
```

- [ ] **Step 2: AuthContext**

```typescript
// web/client/src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  login as apiLogin,
  logout as apiLogout,
  getToken,
  setToken,
  getStoredUser,
  setStoredUser,
  type LoginResponse,
} from "../services/auth";

interface AuthState {
  username: string | null;
  role: string | null;
  displayName: string | null;
  isAuthenticated: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  username: null,
  role: null,
  displayName: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = getToken();
    const user = getStoredUser();
    if (token && user) {
      setUsername(user.username);
      setRole(user.role);
      setDisplayName(user.display_name);
    }
  }, []);

  const login = async (username: string) => {
    const result: LoginResponse = await apiLogin(username);
    setToken(result.token);
    setStoredUser({ username, role: result.role, display_name: result.display_name });
    setUsername(username);
    setRole(result.role);
    setDisplayName(result.display_name);
    navigate("/connect");
  };

  const logout = () => {
    apiLogout();
    setUsername(null);
    setRole(null);
    setDisplayName(null);
    navigate("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        username,
        role,
        displayName,
        isAuthenticated: !!username,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
```

- [ ] **Step 3: AppLayout（侧边栏 + 内容区 + 底部状态栏）**

```typescript
// web/client/src/layouts/AppLayout.tsx
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Typography } from "antd";
import {
  LinkOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  BookOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";

const { Sider, Content, Footer } = Layout;

const menuItems = [
  { key: "/connect", icon: <LinkOutlined />, label: "连接" },
  { key: "/config", icon: <SettingOutlined />, label: "配置" },
  { key: "/measure", icon: <PlayCircleOutlined />, label: "测量" },
  { key: "/help", icon: <BookOutlined />, label: "手册" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { displayName, role, logout } = useAuth();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={180} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <div style={{ padding: "16px", textAlign: "center", fontWeight: 600, fontSize: 14 }}>
          ⚡ EE AutoTool
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
        <div style={{ position: "absolute", bottom: 0, width: "100%", padding: 12 }}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {displayName} ({role})
          </Typography.Text>
          <Menu
            mode="inline"
            items={[{ key: "logout", icon: <LogoutOutlined />, label: "退出" }]}
            onClick={({ key }) => key === "logout" && logout()}
            style={{ borderRight: 0 }}
          />
        </div>
      </Sider>
      <Layout>
        <Content style={{ padding: 24, background: "#fff", overflow: "auto" }}>
          <Outlet />
        </Content>
        <Footer style={{ textAlign: "center", padding: "4px 16px", fontSize: 12, background: "#FAFAFA" }}>
          EE Power On AutoTool Web V3.0 · Nettrix · liujch2
        </Footer>
      </Layout>
    </Layout>
  );
}
```

- [ ] **Step 4: 更新 App.tsx 路由**

```typescript
// web/client/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import AppLayout from "./layouts/AppLayout";
import LoginPage from "./pages/LoginPage";

// 占位页面
const Placeholder = ({ title }: { title: string }) => (
  <div style={{ padding: 40, textAlign: "center" }}><h2>{title}</h2><p>开发中…</p></div>
);

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/connect" element={<Placeholder title="连接" />} />
              <Route path="/config" element={<Placeholder title="配置" />} />
              <Route path="/measure" element={<Placeholder title="测量" />} />
              <Route path="/help" element={<Placeholder title="手册" />} />
            </Route>
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}
```

- [ ] **Step 5: 更新 main.tsx**

```typescript
// web/client/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "antd/dist/reset.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 6: 创建 .env**

```
VITE_API_BASE=http://localhost:8000
```

- [ ] **Step 7: 验证前端启动**

```bash
cd web/client && npm run dev
# 浏览器打开 http://localhost:5173 → 自动跳转到 /login
```

- [ ] **Step 8: Commit**

```bash
git add web/client/src/ web/client/.env
git commit -m "feat(web): add React app shell with AuthContext + sidebar layout + routing"
```

---

### Task 9: 登录页面

**Files:**
- Create: `web/client/src/pages/LoginPage/index.tsx`

**Interfaces:**
- Consumes: `AuthContext.login()`
- Produces: 登录 UI 页面

- [ ] **Step 1: 实现登录页面**

```typescript
// web/client/src/pages/LoginPage/index.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Form, Input, Button, Alert, Typography } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useAuth } from "../../contexts/AuthContext";

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 已登录则跳转
  if (isAuthenticated) {
    navigate("/connect", { replace: true });
    return null;
  }

  const handleSubmit = async (values: { username: string }) => {
    setError(null);
    setLoading(true);
    try {
      await login(values.username);
    } catch (e: any) {
      setError(e.message || "登录失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: 32, color: "#fff" }}>
        <Typography.Title level={2} style={{ color: "#fff", marginBottom: 4 }}>
          ⚡ EE Power On AutoTool
        </Typography.Title>
        <Typography.Text style={{ color: "rgba(255,255,255,0.8)", fontSize: 16 }}>
          示波器自动测量系统
        </Typography.Text>
      </div>

      <Card style={{ width: 400, borderRadius: 8 }}>
        <Form onFinish={handleSubmit} layout="vertical" size="large">
          <Form.Item
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入您的用户名"
              autoFocus
            />
          </Form.Item>

          {error && (
            <Alert
              type="error"
              message={error}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {loading ? "正在验证设备…" : "进  入"}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Typography.Text style={{ color: "rgba(255,255,255,0.5)", marginTop: 24, fontSize: 12 }}>
        如需开通权限，请联系管理员绑定笔记本
      </Typography.Text>
    </div>
  );
}
```

- [ ] **Step 2: 验证登录页面**

浏览器打开 → 输入用户名 → 显示错误提示（因 user_pins.json 无匹配 MAC）

- [ ] **Step 3: Commit**

```bash
git add web/client/src/pages/LoginPage/
git commit -m "feat(web): add login page with MAC auth retry"
```

---

### Task 10: 连接页面

**Files:**
- Create: `web/client/src/pages/ConnectPage/index.tsx`
- Create: `web/client/src/hooks/useWebSocket.ts`

**Interfaces:**
- Consumes: `apiFetch`, `AuthContext`
- Produces: 连接配置 UI、连接状态指示器、WebSocket hook

- [ ] **Step 1: WebSocket hook**

```typescript
// web/client/src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { getToken } from "../services/auth";

const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export function useWebSocket(onMessage: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);

  const connect = useCallback(() => {
    const token = getToken();
    if (!token) return;

    const ws = new WebSocket(`${WS_BASE}/ws?token=${token}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {}
    };
    ws.onclose = () => {
      reconnectTimer.current = window.setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, [onMessage]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  return wsRef;
}
```

- [ ] **Step 2: 连接页面**

```typescript
// web/client/src/pages/ConnectPage/index.tsx
import { useState, useEffect, useCallback } from "react";
import { Card, Form, Select, Input, Button, Badge, Descriptions, Space, message } from "antd";
import { ApiOutlined, DisconnectOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";
import { useWebSocket } from "../../hooks/useWebSocket";

interface ConnectStatus {
  connected: boolean;
  model?: string;
  addr?: string;
}

export default function ConnectPage() {
  const [status, setStatus] = useState<ConnectStatus>({ connected: false });
  const [connecting, setConnecting] = useState(false);

  const onWsMessage = useCallback((data: any) => {
    if (data.type === "heartbeat") {
      setStatus({ connected: data.connected, model: data.model, addr: data.scope_addr });
    }
  }, []);
  useWebSocket(onWsMessage);

  const fetchStatus = async () => {
    try {
      const res = await apiFetch("/api/connect/status");
      const data = await res.json();
      setStatus(data);
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleConnect = async (values: any) => {
    setConnecting(true);
    try {
      const res = await apiFetch("/api/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const data = await res.json();
      setStatus({ connected: true, model: data.model, addr: data.addr });
      message.success(`已连接 ${data.model}`);
    } catch (e: any) {
      message.error(e.message || "连接失败");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await apiFetch("/api/connect", { method: "DELETE" });
      setStatus({ connected: false });
      message.info("已断开");
    } catch {
      message.error("断开失败");
    }
  };

  return (
    <div>
      <Card title="示波器连接" style={{ maxWidth: 600, marginBottom: 16 }}>
        <Form
          layout="vertical"
          onFinish={handleConnect}
          initialValues={{ method: "usb_gpib", port: 4000, use_socket: false }}
        >
          <Form.Item name="method" label="连接方式">
            <Select
              options={[
                { value: "usb_gpib", label: "GPIB / USB（自动扫描）" },
                { value: "ip", label: "TCP/IP（手动输入 IP）" },
              ]}
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.method !== cur.method}>
            {({ getFieldValue }) =>
              getFieldValue("method") === "ip" ? (
                <>
                  <Form.Item name="ip" label="IP 地址" rules={[{ required: true }]}>
                    <Input placeholder="192.168.1.100" />
                  </Form.Item>
                  <Form.Item name="port" label="Port">
                    <Input type="number" />
                  </Form.Item>
                  <Form.Item name="use_socket" label="Socket 模式" valuePropName="checked">
                    <Select options={[{ value: false, label: "INSTR" }, { value: true, label: "SOCKET" }]} />
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={connecting} icon={<ApiOutlined />}>
              连接
            </Button>
            <Button danger onClick={handleDisconnect} disabled={!status.connected} icon={<DisconnectOutlined />}>
              断开
            </Button>
          </Space>
        </Form>
      </Card>

      <Card title="连接状态">
        <Descriptions column={2}>
          <Descriptions.Item label="状态">
            <Badge status={status.connected ? "success" : "default"} text={status.connected ? "已连接" : "未连接"} />
          </Descriptions.Item>
          <Descriptions.Item label="型号">{status.model || "-"}</Descriptions.Item>
          <Descriptions.Item label="地址" span={2}>{status.addr || "-"}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/client/src/pages/ConnectPage/ web/client/src/hooks/useWebSocket.ts
git commit -m "feat(web): add connect page with VISA connection UI + WebSocket hook"
```

---

### Task 11: 配置页面

**Files:**
- Create: `web/client/src/pages/ConfigPage/index.tsx`

**Interfaces:**
- Consumes: `apiFetch`
- Produces: 完整的信号配置 + MSO 配置 + 导航控制面板

- [ ] **Step 1: 实现配置页面**

```typescript
// web/client/src/pages/ConfigPage/index.tsx
import { useState, useEffect } from "react";
import { Card, Form, Select, InputNumber, Input, Button, Tabs, Space, message, Switch, Row, Col } from "antd";
import { SaveOutlined, UploadOutlined, DownloadOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";

export default function ConfigPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [excelInfo, setExcelInfo] = useState<any>({});

  useEffect(() => {
    apiFetch("/api/excel/info").then(r => r.json()).then(setExcelInfo).catch(() => {});
  }, []);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/measure/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      message.success("配置已保存");
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    try {
      const res = await apiFetch("/api/config/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: "config.json" }),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const data = await res.json();
      message.success(`已导入 ${data.keys?.length || 0} 项配置`);
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const tabItems = [
    {
      key: "signal",
      label: "信号配置",
      children: (
        <>
          <Form.Item name="test_type" label="测试类型">
            <Select options={[{ value: "sequence", label: "Sequence（时序）" }, { value: "monotony", label: "Monotony（单调性）" }]} />
          </Form.Item>
          <Form.Item name="init_row" label="起始行">
            <InputNumber min={1} />
          </Form.Item>
          <Form.Item name="pn_direction" label="P/N 方向">
            <Select options={[{ value: 1, label: "P（正向/Rise）" }, { value: 0, label: "N（反向/Fall）" }]} />
          </Form.Item>
          {[1, 2, 3, 4].map((n) => (
            <Row gutter={16} key={n}>
              <Col span={4}>
                <Form.Item name={`signal${n}_enabled`} label={`信号 ${n}`} valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name={`signal${n}_col`} label="数据列">
                  <Input placeholder="A" maxLength={2} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name={`ch${n}_label`} label={`CH${n} 标签`}>
                  <Input placeholder={`CH${n}`} />
                </Form.Item>
              </Col>
              <Col span={4}>
                <Form.Item name={`ch${n}_enabled`} label="启用" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          ))}
        </>
      ),
    },
    {
      key: "mso",
      label: "MSO 设置",
      children: (
        <>
          <Form.Item name="hor_mode" label="水平模式"><Input placeholder="AUTO" /></Form.Item>
          <Form.Item name="hor_scale" label="水平刻度"><Input placeholder="40ms" /></Form.Item>
          <Form.Item name="hor_pos" label="水平偏移"><Input placeholder="50%" /></Form.Item>
          {[1, 2, 3, 4].map((n) => (
            <Form.Item key={n} name={`ch${n}_scale`} label={`CH${n} 垂直刻度`}>
              <Input placeholder="1.0V" />
            </Form.Item>
          ))}
        </>
      ),
    },
    {
      key: "pic",
      label: "截图/数据列",
      children: (
        <>
          <Form.Item name="data_col" label="数据写入列"><Input placeholder="A" /></Form.Item>
          <Form.Item name="seq_pic_col" label="Sequence 截图列"><Input placeholder="B" /></Form.Item>
          <Form.Item name="mono_p_pic_col" label="Monotony P 截图列"><Input placeholder="B" /></Form.Item>
          <Form.Item name="mono_n_pic_col" label="Monotony N 截图列"><Input placeholder="C" /></Form.Item>
        </>
      ),
    },
  ];

  return (
    <div>
      <Card title="测量配置" extra={
        <Space>
          <Button icon={<UploadOutlined />} onClick={handleImport}>导入</Button>
          <Button icon={<DownloadOutlined />} onClick={() => message.info("请使用导出接口")}>导出</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleSave}
          initialValues={{ test_type: "sequence", init_row: 1, pn_direction: 1,
            signal1_enabled: true, signal2_enabled: false, signal3_enabled: false, signal4_enabled: false,
            signal1_col: "A", signal2_col: "B", signal3_col: "C", signal4_col: "D",
            ch1_enabled: true, ch2_enabled: false, ch3_enabled: false, ch4_enabled: false }}>
          <Tabs items={tabItems} />
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 路由**

```typescript
import ConnectPage from "./pages/ConnectPage";
import ConfigPage from "./pages/ConfigPage";
// 替换 Placeholder:
<Route path="/connect" element={<ConnectPage />} />
<Route path="/config" element={<ConfigPage />} />
```

- [ ] **Step 3: Commit**

```bash
git add web/client/src/pages/ConfigPage/ web/client/src/App.tsx
git commit -m "feat(web): add config page with signal/MSO/pic settings"
```

---

### Task 12: 测量页面 + 手册页面

**Files:**
- Create: `web/client/src/pages/MeasurePage/index.tsx`
- Create: `web/client/src/pages/HelpPage/index.tsx`

**Interfaces:**
- Consumes: `apiFetch`, `useWebSocket`
- Produces: 测量控制面板 + 实时日志 + 在线手册

- [ ] **Step 1: 测量页面**

```typescript
// web/client/src/pages/MeasurePage/index.tsx
import { useState, useCallback, useEffect } from "react";
import { Card, Button, Space, InputNumber, Timeline, Tag, Statistic, Row, Col, message, Descriptions } from "antd";
import { PlayCircleOutlined, LeftOutlined, RightOutlined, FastForwardOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";
import { useWebSocket } from "../../hooks/useWebSocket";

interface LogEntry {
  ts: string;
  level: string;
  message: string;
}

const levelColors: Record<string, string> = { info: "blue", warning: "orange", error: "red" };

export default function MeasurePage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<any>({});
  const [jumpTarget, setJumpTarget] = useState<number>(0);
  const [running, setRunning] = useState(false);

  const onWsMessage = useCallback((data: any) => {
    if (data.type === "log") {
      setLogs((prev) => [...prev.slice(-99), { ts: data.ts, level: data.level, message: data.message }]);
    } else if (data.type === "heartbeat") {
      setStatus((prev: any) => ({ ...prev, connected: data.connected, model: data.model }));
    } else if (data.type === "progress") {
      setStatus((prev: any) => ({ ...prev, current: data.current, total: data.total, item: data.item }));
    }
  }, []);
  useWebSocket(onWsMessage);

  const fetchStatus = async () => {
    try {
      const res = await apiFetch("/api/measure/status");
      setStatus(await res.json());
    } catch {}
  };
  useEffect(() => { fetchStatus(); }, []);

  const doAction = async (endpoint: string, body?: any) => {
    setRunning(true);
    try {
      const res = await apiFetch(endpoint, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      fetchStatus();
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="当前行" value={status.row || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="总条目" value={status.total || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="当前条目" value={status.current_item || "-"} /></Card></Col>
        <Col span={6}><Card>
          <Statistic title="连接状态" value={status.connected ? "已连接" : "未连接"}
            valueStyle={{ color: status.connected ? "#52c41a" : "#ff4d4f" }} />
        </Card></Col>
      </Row>

      <Card title="导航控制" style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Button icon={<LeftOutlined />} onClick={() => doAction("/api/measure/last")} disabled={running}>
            上一条
          </Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => doAction("/api/measure/go")} loading={running}>
            GO
          </Button>
          <Button icon={<RightOutlined />} onClick={() => doAction("/api/measure/next")} disabled={running}>
            下一条
          </Button>
          <InputNumber min={1} value={jumpTarget} onChange={(v) => setJumpTarget(v || 0)} placeholder="目标行" />
          <Button icon={<FastForwardOutlined />} onClick={() => doAction("/api/measure/jump", { target_row: jumpTarget })} disabled={running}>
            Jump
          </Button>
        </Space>
      </Card>

      <Card title="实时日志" bodyStyle={{ maxHeight: 400, overflow: "auto" }}>
        <Timeline
          items={logs.map((l, i) => ({
            key: i,
            color: levelColors[l.level] || "gray",
            children: <><Tag>{l.ts}</Tag> {l.message}</>,
          }))}
        />
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: 手册页面**

```typescript
// web/client/src/pages/HelpPage/index.tsx
import { useState, useEffect } from "react";
import { Layout, Tree, Typography } from "antd";
import type { DataNode } from "antd/es/tree";
import ReactMarkdown from "react-markdown";

const { Sider, Content } = Layout;

// 内嵌 Markdown 手册内容（与 Doc/用户操作手册.md 同步）
const MANUAL_MD = `# EE Power On AutoTool V2.0 — 用户操作手册

## 1. 环境准备

### 1.1 硬件需求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| 示波器 | Tektronix MSO4/5/6、DPO7000、DPO5000 系列 |

### 1.2 软件依赖

需要安装 NI-VISA 驱动。

## 2. 操作流程

1. 连接示波器
2. 打开 Excel 文件
3. 配置信号参数
4. 开始测量
`;

interface Chapter {
  title: string;
  anchor: string;
  children?: Chapter[];
}

function extractChapters(md: string): Chapter[] {
  const chapters: Chapter[] = [];
  for (const line of md.split("\n")) {
    if (line.startsWith("## ") && !line.startsWith("### ")) {
      const title = line.slice(3).trim();
      if (title === "目录") continue;
      chapters.push({ title, anchor: title.replace(/\s/g, "-"), children: [] });
    } else if (line.startsWith("### ") && chapters.length > 0) {
      const title = line.slice(4).trim();
      chapters[chapters.length - 1].children!.push({ title, anchor: title.replace(/\s/g, "-") });
    }
  }
  return chapters;
}

function chaptersToTreeData(chapters: Chapter[]): DataNode[] {
  return chapters.map((ch) => ({
    title: ch.title,
    key: ch.anchor,
    children: ch.children?.map((sub) => ({ title: sub.title, key: sub.anchor, isLeaf: true })),
  }));
}

export default function HelpPage() {
  const chapters = extractChapters(MANUAL_MD);
  const treeData = chaptersToTreeData(chapters);

  const scrollTo = (keys: any[]) => {
    if (keys.length > 0) {
      const el = document.getElementById(keys[0] as string);
      el?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <Layout style={{ background: "#fff" }}>
      <Sider width={220} theme="light" style={{ borderRight: "1px solid #f0f0f0", padding: 8 }}>
        <Tree treeData={treeData} onSelect={scrollTo} defaultExpandAll />
      </Sider>
      <Content style={{ padding: "0 24px", maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
        <ReactMarkdown>{MANUAL_MD}</ReactMarkdown>
      </Content>
    </Layout>
  );
}
```

- [ ] **Step 3: 更新路由**

```typescript
import MeasurePage from "./pages/MeasurePage";
import HelpPage from "./pages/HelpPage";
// 替换:
<Route path="/measure" element={<MeasurePage />} />
<Route path="/help" element={<HelpPage />} />
```

- [ ] **Step 4: 安装 react-markdown**

```bash
cd web/client && npm install react-markdown
```

- [ ] **Step 5: Commit**

```bash
git add web/client/src/pages/MeasurePage/ web/client/src/pages/HelpPage/ web/client/src/App.tsx
git commit -m "feat(web): add measure control page + help manual page"
```

---

### Task 13: 集成 — 生产静态文件服务 + 部署脚本

**Files:**
- Modify: `web/server/main.py` (静态文件挂载)
- Create: `web/start.py` (一键启动脚本)
- Create: `web/README.md`

**Interfaces:**
- 开发模式：Vite dev server (`:5173`) + FastAPI (`:8000`)
- 生产模式：FastAPI 直接服务 React 构建产物

- [ ] **Step 1: 更新 main.py 静态文件挂载**

在 `web/server/main.py` 末尾添加：

```python
import os
from fastapi.staticfiles import StaticFiles

# 生产模式：服务 React 构建产物
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```

- [ ] **Step 2: 创建启动脚本**

```python
# web/start.py
"""一键启动 Web 服务器（开发模式或生产模式）."""
import sys
import subprocess
import webbrowser
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000


def start_dev():
    """开发模式 — 同时启动 Vite + FastAPI."""
    import uvicorn
    # 前端由用户手动 npm run dev，或在这里自动启动
    print(f"[web] 开发模式 — http://localhost:{SERVER_PORT}")
    print(f"[web] 前端请手动: cd web/client && npm run dev")
    webbrowser.open(f"http://localhost:{SERVER_PORT}/api/health")
    uvicorn.run(
        "web.server.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        reload_dirs=[str(WEB_DIR / "server")],
    )


def start_prod():
    """生产模式 — 仅启动 FastAPI（需先 npm run build）."""
    import uvicorn
    dist_dir = WEB_DIR / "client" / "dist"
    if not dist_dir.exists():
        print("[web] 前端未构建。请先: cd web/client && npm run build")
        sys.exit(1)
    print(f"[web] 生产模式 — http://{SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        "web.server.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
    )


if __name__ == "__main__":
    if "--prod" in sys.argv:
        start_prod()
    else:
        start_dev()
```

- [ ] **Step 3: 创建 web/README.md**

```markdown
# EE Power On AutoTool — Web 版

## 快速开始（开发）

### 1. 启动后端
```bash
pip install -r requirements.txt
python web/start.py
```

### 2. 启动前端
```bash
cd web/client
npm install
npm run dev
```

### 3. 访问
浏览器打开 http://localhost:5173

## 生产部署

```bash
cd web/client && npm run build
python web/start.py --prod
# 浏览器打开 http://<服务器IP>:8000
```

## 用户管理

编辑项目根目录的 `user_pins.json` 添加用户和对应笔记本 MAC 地址。
```

- [ ] **Step 4: 验证完整流程**

```bash
# 终端 1: 后端
python web/start.py

# 终端 2: 前端
cd web/client && npm run dev

# 浏览器: http://localhost:5173
# 1. 输入用户名 → 登录
# 2. 连接页 → 选择连接方式
# 3. 配置页 → 设置参数
# 4. 测量页 → 查看日志
# 5. 手册页 → 浏览文档
```

- [ ] **Step 5: Commit**

```bash
git add web/start.py web/README.md web/server/main.py
git commit -m "feat(web): add startup script + static file serving + README"
```

---

## Plan Completion Checklist

- [x] 所有 spec 需求有对应 task
- [x] 无 TBD/TODO/placeholder
- [x] 类型签名跨 task 一致 (`UserSession`, `get_current_user`, `AuthContext`)
- [x] 每个 task 以 commit 结尾
- [x] `core/` 层零修改
