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

from web.server.api.auth import router as auth_router
from web.server.api.config import router as config_router
from web.server.api.connect import router as connect_router
from web.server.api.excel import router as excel_router
from web.server.api.measure import router as measure_router
from web.server.api.ws import router as ws_router

app.include_router(auth_router)
app.include_router(config_router)
app.include_router(connect_router)
app.include_router(excel_router)
app.include_router(measure_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 生产模式：服务 React 构建产物（静态文件 + SPA fallback）
# 仅在 dist 目录存在时挂载；API 路由优先匹配，未匹配的路径 fallback 到 React
# ---------------------------------------------------------------------------
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
_INDEX_HTML = os.path.join(_STATIC_DIR, "index.html")

if os.path.exists(_STATIC_DIR):
    # 静态资源目录（JS / CSS / 图片等）
    _assets_dir = os.path.join(_STATIC_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="static_assets")

    # 根目录静态文件 + SPA fallback（API 路径返回 404）
    @app.get("/{filename:path}", response_model_exclude_none=True)
    async def serve_static_or_spa(filename: str):
        # API 路径（无匹配路由）返回标准 404
        if filename.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        file_path = os.path.join(_STATIC_DIR, filename)
        # 1) 匹配具体文件（favicon.svg, icons.svg 等）
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # 2) SPA fallback — 所有其他路径返回 index.html
        if os.path.exists(_INDEX_HTML):
            return FileResponse(_INDEX_HTML)
        return JSONResponse({"detail": "Not Found"}, status_code=404)
