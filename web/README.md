# EE Power On AutoTool — Web 版

基于 React (Vite) + FastAPI 的仪器自动测量 Web 控制台。

## 快速开始（开发）

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端

```bash
python web/start.py
```

后端运行在 `http://localhost:8000`，支持热重载。

### 3. 启动前端

```bash
cd web/client
npm install
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，API 请求通过 Vite proxy 转发到后端。

### 4. 访问

浏览器打开 http://localhost:5173

## 生产部署

```bash
# 1. 构建前端
cd web/client && npm run build

# 2. 启动生产服务器（FastAPI 直接服务 React 构建产物）
python web/start.py --prod
```

浏览器打开 `http://<服务器IP>:8000` 即可访问。

## 用户管理

编辑项目根目录的 `user_pins.json` 添加用户和对应笔记本 MAC 地址：

```json
{
  "username": {
    "role": "admin",
    "display_name": "显示名称",
    "mac_addresses": ["AA:BB:CC:DD:EE:FF"]
  }
}
```

## 项目结构

```
web/
├── start.py              # 一键启动脚本
├── README.md             # 本文件
├── server/               # FastAPI 后端
│   ├── main.py           # 入口 + 静态文件挂载
│   ├── state.py          # 全局状态管理
│   └── api/              # API 路由
│       ├── auth.py       # 认证（MAC + JWT）
│       ├── config.py     # 配置导入/导出
│       ├── connect.py    # 仪器连接管理
│       ├── excel.py      # Excel 操作
│       ├── measure.py    # 测量执行
│       └── ws.py         # WebSocket 实时推送
└── client/               # React 前端
    ├── src/
    │   ├── App.tsx       # 路由入口
    │   ├── main.tsx      # 前端入口
    │   ├── contexts/     # React Context
    │   ├── layouts/      # 布局组件
    │   ├── pages/        # 页面组件
    │   └── services/     # API 调用封装
    └── dist/             # 生产构建产物
```
