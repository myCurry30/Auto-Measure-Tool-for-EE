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
        # Store the active sheet name from the newly opened workbook.
        # EasyExcel does not expose a `ws` attribute; use ActiveSheet.Name.
        active_sheet = xls.xlBook.ActiveSheet.Name if hasattr(xls, 'xlBook') else ""
        current.state["sheet_name"] = active_sheet
        sheet_names = await asyncio.to_thread(xls.get_sheet_names)
        return {
            "file_path": req.file_path,
            "active_sheet": active_sheet,
            "sheet_names": sheet_names,
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
    sheet_name = current.state.get("sheet_name", "")
    if not sheet_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有激活的 Sheet")
    try:
        # EasyExcel.getCell(sheet, row, col) — sheet name is the first argument.
        val = await asyncio.to_thread(current.xls.getCell, sheet_name, row, col)
        return {"row": row, "col": col, "value": str(val) if val is not None else ""}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/cell")
async def write_cell(req: CellWrite, current: UserSession = Depends(get_current_user)):
    """写入单元格."""
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先打开 Excel")
    sheet_name = current.state.get("sheet_name", "")
    if not sheet_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有激活的 Sheet")
    try:
        # EasyExcel.setCell(sheet, row, col, value) — sheet name is the first argument.
        await asyncio.to_thread(current.xls.setCell, sheet_name, req.row, req.col, req.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
