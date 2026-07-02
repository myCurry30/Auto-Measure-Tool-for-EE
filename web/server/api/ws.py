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
