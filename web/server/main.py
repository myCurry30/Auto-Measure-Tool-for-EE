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
app.include_router(auth_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
