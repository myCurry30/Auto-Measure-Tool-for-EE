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


def _model_from_flags(flags: dict) -> str:
    """Derive a human-readable model name from instrument flags."""
    if flags.get("dpo7000"):
        return "DPO7000C"
    elif flags.get("mso5"):
        return "MSO4/5/6"
    elif flags.get("dpo5104b"):
        return "DPO5104B"
    return "Unknown"


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
        # connect_usb_gpib / connect_ip both return (osc, rm, model_flags, message)
        osc, rm, model_flags, message = await asyncio.to_thread(_connect)

        if osc is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        current.osc = osc
        current.rm = rm

        model = _model_from_flags(model_flags)
        addr = req.ip if req.method == "ip" else "GPIB/USB"

        current.state["model"] = model
        current.state["addr"] = addr

        # 挂载日志桥
        LogBridge.attach(current, "core")
        return {"connected": True, "model": model, "addr": addr}
    except HTTPException:
        raise
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
