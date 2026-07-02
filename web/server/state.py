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
