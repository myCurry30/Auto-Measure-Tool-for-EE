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
