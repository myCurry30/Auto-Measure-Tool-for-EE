"""一键启动 Web 服务器（开发模式或生产模式）."""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，以便 uvicorn 能加载 web.server.main:app
_WEB_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _WEB_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8200


def start_dev() -> None:
    """开发模式 — 同时启动 Vite + FastAPI（前端需手动 npm run dev）."""
    import webbrowser

    import uvicorn

    print(f"[web] 开发模式 — http://localhost:{SERVER_PORT}")
    print("[web] 前端请手动: cd web/client && npm run dev")
    webbrowser.open(f"http://localhost:{SERVER_PORT}/api/health")
    uvicorn.run(
        "web.server.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        reload_dirs=[str(_WEB_DIR / "server")],
    )


def start_prod() -> None:
    """生产模式 — 仅启动 FastAPI（需先 npm run build）."""
    import uvicorn

    dist_dir = _WEB_DIR / "client" / "dist"
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
