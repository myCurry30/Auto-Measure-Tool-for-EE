"""测量操作 API — 复用 core.measurement + core.capture + core.test_manager.

Adapted from plan code to match actual core signatures:
- Capture_Pic: 20+ params (not 6) — requires test_type, flag_monotony_direction,
  m (row), mso5, pic_path, project_name, column numbers, etc.
- common_set: 3 params (osc, dpo7000, dpo5104b) — model flags derived from state.
- channel_Lable_set: up to 7 params — label_x/label_y have defaults, omitted.
- measure_sequence / measure_monotony: 2 params each (osc, mso5).
- go / Last / Next / jump: signatures match plan, but go reads state['xls'].
"""
import os
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from web.server.api.deps import get_current_user
from web.server.state import UserSession

router = APIRouter(prefix="/api/measure", tags=["measure"])
log = logging.getLogger("core")


# ── Request models ──────────────────────────────────────────────────────────

class JumpRequest(BaseModel):
    target_row: int


class ConfigRequest(BaseModel):
    test_type: str = "sequence"
    init_row: int = 8
    # 信号配置
    signal1_enabled: bool = True
    signal2_enabled: bool = False
    signal3_enabled: bool = False
    signal4_enabled: bool = False
    signal1_name: str = "CH1"
    signal2_name: str = "CH2"
    signal3_name: str = "CH3"
    signal4_name: str = "CH4"
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
    ch2_enabled: bool = True
    ch3_enabled: bool = True
    ch4_enabled: bool = True
    # MSO 配置
    hor_mode: str = "AUTO"
    hor_scale: str = ""
    hor_pos: str = ""
    ch1_scale: str = ""
    ch2_scale: str = ""
    ch3_scale: str = ""
    ch4_scale: str = ""
    # P/N 方向
    pn_direction: str = "P"
    # 截图路径
    pic_path: str = ""
    project_name: str = ""
    # 列配置（字母形式，内部转为数字）
    data_col: str = "G"
    seq_pic_col: str = "B"
    mono_p_pic_col: str = "B"
    mono_n_pic_col: str = "C"
    mono_p_top_col: str = "I"
    mono_p_base_col: str = "J"
    mono_p_max_col: str = "K"
    mono_p_min_col: str = "L"
    mono_n_top_col: str = "M"
    mono_n_base_col: str = "N"
    mono_n_max_col: str = "O"
    mono_n_min_col: str = "P"
    # 数据保存开关
    save_pic: bool = True
    save_data: bool = True
    save_to_excel: bool = True
    save_to_scope: bool = False
    save_to_local: bool = True


# ── Helpers ─────────────────────────────────────────────────────────────────

def _col_letter_to_num(col: str) -> int:
    """Convert column letter(s) to 1-based number: A→1, Z→26, AA→27."""
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - ord('A') + 1)
        if n <= 0:
            return 1
    return max(n, 1)


def _derive_model_flags(model_str: str) -> dict:
    """Derive model booleans from the model name string stored in state.

    connect.py stores e.g. "MSO4/5/6", "DPO7000C", "DPO5104B".
    """
    if not model_str:
        return {"mso5": False, "dpo7000": False, "dpo5104b": False}
    model_upper = model_str.upper()
    return {
        "mso5": "MSO" in model_upper,
        "dpo7000": "DPO7" in model_upper,
        "dpo5104b": "DPO5" in model_upper,
    }


def _measure_go(session: UserSession):
    """Execute one complete measurement cycle (blocking, runs in to_thread).

    Adapted from plan: Capture_Pic requires 11+ positional args, not 6.
    Model flags are derived from state['model'] instead of hardcoded.
    """
    state = session.state

    # ── Ensure basic state fields exist ────────────────────────────────
    state.setdefault("test_type", session.test_type)
    state.setdefault("pn_direction", session.pn_direction)
    state.setdefault("row", session.row)
    state.setdefault("init_row", 8)
    state.setdefault("flag_monotony_direction",
                     1 if str(session.pn_direction).upper() != "N" else 0)

    # go() reads xls from state dict — keep in sync with session
    if session.xls is not None:
        state["xls"] = session.xls

    from core.measurement import (measure_sequence, measure_monotony,
                                  common_set, channel_Lable_set)
    from core.capture import Capture_Pic
    from core.test_manager import go

    osc = session.osc
    xls = session.xls

    # ── Derive model flags from stored connection info ──────────────────
    model_flags = _derive_model_flags(state.get("model", ""))
    mso5 = model_flags["mso5"]
    dpo7000 = model_flags["dpo7000"]
    dpo5104b = model_flags["dpo5104b"]

    # ── Common oscilloscope setup ──────────────────────────────────────
    # Actual signature: common_set(osc, dpo7000, dpo5104b)
    common_set(osc, dpo7000, dpo5104b)

    # Actual signature: channel_Lable_set(osc, ch1..ch4, label_x=None, label_y=None)
    channel_Lable_set(
        osc,
        state.get("ch1_label", ""),
        state.get("ch2_label", ""),
        state.get("ch3_label", ""),
        state.get("ch4_label", ""),
    )

    # ── Measurement configuration ──────────────────────────────────────
    test_type = session.test_type
    if test_type == "sequence":
        measure_sequence(osc, mso5)
    else:
        measure_monotony(osc, mso5)

    # ── Gather Capture_Pic parameters from state ───────────────────────
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
    ch_enables = [
        state.get("ch1_enabled", True),
        state.get("ch2_enabled", True),
        state.get("ch3_enabled", True),
        state.get("ch4_enabled", True),
    ]

    flag_monotony_direction = state.get("flag_monotony_direction", 1)

    # Current Excel row — go() sets excel_row; for first call fall back to row/init_row
    m = int(state.get("excel_row",
             state.get("row",
             state.get("init_row", 8))))

    # Derive pic_path and project_name from Excel file path if not explicitly set
    file_path = state.get("file_path", "")
    pic_path = state.get("pic_path", "")
    if not pic_path and file_path:
        pic_path = os.path.dirname(file_path)
    project_name = state.get("project_name", "")
    if not project_name and file_path:
        project_name = os.path.splitext(os.path.basename(file_path))[0]

    # Convert column letters to 1-based numbers for Capture_Pic
    data_col = _col_letter_to_num(state.get("data_col", "G"))
    seq_pic_col = _col_letter_to_num(state.get("seq_pic_col", "B"))
    mono_p_pic_col = _col_letter_to_num(state.get("mono_p_pic_col", "B"))
    mono_n_pic_col = _col_letter_to_num(state.get("mono_n_pic_col", "C"))
    mono_p_cols = [
        _col_letter_to_num(state.get("mono_p_top_col", "I")),
        _col_letter_to_num(state.get("mono_p_base_col", "J")),
        _col_letter_to_num(state.get("mono_p_max_col", "K")),
        _col_letter_to_num(state.get("mono_p_min_col", "L")),
    ]
    mono_n_cols = [
        _col_letter_to_num(state.get("mono_n_top_col", "M")),
        _col_letter_to_num(state.get("mono_n_base_col", "N")),
        _col_letter_to_num(state.get("mono_n_max_col", "O")),
        _col_letter_to_num(state.get("mono_n_min_col", "P")),
    ]

    save_pic = state.get("save_pic", True)
    save_data = state.get("save_data", True)
    save_to_excel = state.get("save_to_excel", True)
    save_to_scope = state.get("save_to_scope", False)
    save_to_local = state.get("save_to_local", True)

    # ── Screenshot + data acquisition ──────────────────────────────────
    # Actual Capture_Pic signature (required positional args):
    #   osc, xls, sheet_name, signals, signal_enables,
    #   test_type, flag_monotony_direction, m, mso5,
    #   pic_path, project_name,
    #   [kwargs: save_pic, save_data, save_to_excel, save_to_scope,
    #    save_to_local, data_col, mono_p_cols, mono_n_cols,
    #    pic_cols, ch_enables, seq_data_en, mono_p_data_en, mono_n_data_en]
    delay_time, value_top, value_base, value_max, value_min = Capture_Pic(
        osc, xls, sheet_name, signals, signal_enables,
        test_type, flag_monotony_direction, m, mso5,
        pic_path, project_name,
        save_pic=save_pic,
        save_data=save_data,
        save_to_excel=save_to_excel,
        save_to_scope=save_to_scope,
        save_to_local=save_to_local,
        data_col=data_col,
        mono_p_cols=mono_p_cols,
        mono_n_cols=mono_n_cols,
        pic_cols=(seq_pic_col, mono_p_pic_col, mono_n_pic_col),
        ch_enables=ch_enables,
        seq_data_en=True,
        mono_p_data_en=[True, True, True, True],
        mono_n_data_en=[True, True, True, True],
    )

    # ── Advance state (go initializes row tracking for next measurement) ──
    # Actual signature: go(file_path, state) — file_path param is unused internally
    go(file_path, state)

    return {
        "delay_time": delay_time,
        "value_top": value_top,
        "value_base": value_base,
        "value_max": value_max,
        "value_min": value_min,
    }


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/go")
async def go_measure(current: UserSession = Depends(get_current_user)):
    """Execute one measurement (Sequence or Monotony based on test_type)."""
    if current.osc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="请先连接示波器")
    if current.xls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="请先打开 Excel")

    try:
        # Wraps all VISA + COM calls in asyncio.to_thread()
        result = await asyncio.to_thread(_measure_go, current)
        return {
            "status": "ok",
            "row": current.state.get("row", 0),
            "item": current.state.get("current_item", 0),
            "results": result,
        }
    except Exception as e:
        log.error(f"测量失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.post("/last")
async def last(current: UserSession = Depends(get_current_user)):
    """Go to previous item (Sequence: row-1; Monotony: N→P or P→row-1→N)."""
    from core.test_manager import Last
    try:
        Last(current.state)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.post("/next")
async def next(current: UserSession = Depends(get_current_user)):
    """Go to next item (Sequence: row+1; Monotony: P→N or N→row+1→P)."""
    from core.test_manager import Next
    try:
        Next(current.state)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.post("/jump")
async def jump(req: JumpRequest, current: UserSession = Depends(get_current_user)):
    """Jump to a specific row (Sequence: target row; Monotony: target row, P)."""
    from core.test_manager import jump as do_jump
    try:
        do_jump(current.state, req.target_row)
        return {"status": "ok", "row": current.state.get("row", 0)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.get("/status")
async def measure_status(current: UserSession = Depends(get_current_user)):
    """Query current measurement state."""
    return {
        "test_type": current.test_type,
        "row": current.state.get("row", 0),
        "total": current.state.get("total", 0),
        "current_item": current.state.get("current_item", 0),
        "pn_direction": current.state.get("pn_direction", "P"),
    }


@router.put("/config")
async def update_config(req: ConfigRequest,
                        current: UserSession = Depends(get_current_user)):
    """Update measurement configuration."""
    current.test_type = req.test_type
    current.pn_direction = req.pn_direction
    current.row = req.init_row
    s = current.state
    s.update({
        "test_type": req.test_type,
        "init_row": req.init_row,
        "pn_direction": req.pn_direction,
        "flag_monotony_direction": 1 if req.pn_direction.upper() != "N" else 0,
        "signal1_name": req.signal1_name,
        "signal2_name": req.signal2_name,
        "signal3_name": req.signal3_name,
        "signal4_name": req.signal4_name,
        "signal1_col": req.signal1_col,
        "signal2_col": req.signal2_col,
        "signal3_col": req.signal3_col,
        "signal4_col": req.signal4_col,
        "signal1_enabled": req.signal1_enabled,
        "signal2_enabled": req.signal2_enabled,
        "signal3_enabled": req.signal3_enabled,
        "signal4_enabled": req.signal4_enabled,
        "ch1_label": req.ch1_label,
        "ch2_label": req.ch2_label,
        "ch3_label": req.ch3_label,
        "ch4_label": req.ch4_label,
        "ch1_enabled": req.ch1_enabled,
        "ch2_enabled": req.ch2_enabled,
        "ch3_enabled": req.ch3_enabled,
        "ch4_enabled": req.ch4_enabled,
        "hor_mode": req.hor_mode,
        "hor_scale": req.hor_scale,
        "hor_pos": req.hor_pos,
        "ch1_scale": req.ch1_scale,
        "ch2_scale": req.ch2_scale,
        "ch3_scale": req.ch3_scale,
        "ch4_scale": req.ch4_scale,
        "pic_path": req.pic_path,
        "project_name": req.project_name,
        "data_col": req.data_col,
        "seq_pic_col": req.seq_pic_col,
        "mono_p_pic_col": req.mono_p_pic_col,
        "mono_n_pic_col": req.mono_n_pic_col,
        "mono_p_top_col": req.mono_p_top_col,
        "mono_p_base_col": req.mono_p_base_col,
        "mono_p_max_col": req.mono_p_max_col,
        "mono_p_min_col": req.mono_p_min_col,
        "mono_n_top_col": req.mono_n_top_col,
        "mono_n_base_col": req.mono_n_base_col,
        "mono_n_max_col": req.mono_n_max_col,
        "mono_n_min_col": req.mono_n_min_col,
        "save_pic": req.save_pic,
        "save_data": req.save_data,
        "save_to_excel": req.save_to_excel,
        "save_to_scope": req.save_to_scope,
        "save_to_local": req.save_to_local,
    })
    return {"ok": True}
