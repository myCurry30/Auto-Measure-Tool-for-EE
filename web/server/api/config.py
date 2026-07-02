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
