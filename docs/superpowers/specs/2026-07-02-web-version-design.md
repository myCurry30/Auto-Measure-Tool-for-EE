# EE Power On AutoTool — Web 版设计文档

**日期**: 2026-07-02
**分支**: `feature/web-version`
**状态**: 设计完成，待实施

---

## 1. 目标与范围

将现有 PySide6 桌面应用改造为 Web 架构，用户在浏览器中完成示波器自动测量工作。桌面版保持不动，Web 版在新分支独立开发。

**使用场景**: 单机本地使用 — 后端跑在工程师本机，浏览器访问 `localhost`，VISA 和 Excel COM 操作均在本机完成。

**范围**:
- 完整移植现有功能：示波器连接、Sequence/Monotony 测量、Excel 读写、配置管理、用户手册
- 不新增测量类型或示波器型号
- 不改变 `core/` 层业务逻辑

**不做**:
- 远程/多用户访问
- 数据库持久化（配置仍用 JSON 文件）
- Excel COM 以外的替代方案

---

## 2. 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 前端 | React 18 + TypeScript | SPA，组件化，生态丰富 |
| UI 组件库 | Ant Design 5 | 表格/表单/步骤条等开箱即用，适合工具类应用 |
| 构建工具 | Vite | 快速 HMR，零配置起步 |
| 后端 | FastAPI (Python 3.12) | 异步支持、WebSocket 原生、自动 OpenAPI 文档 |
| 认证 | JWT (python-jose) + bcrypt | 当前阶段 PIN 码，预留 LDAP/AD 扩展点 |
| 实时通信 | WebSocket | 日志推送、心跳、测量进度 |
| Excel | win32com（复用现有 EasyExcel） | 单机 Windows 环境，COM 仍然最优 |
| 示波器通信 | PyVISA（复用现有驱动） | 不变，直接 import 现有 core/ 模块 |

---

## 3. 整体架构

```
工程师本机 (Windows)
│
├─ 浏览器 (localhost:5173)     ← React + Ant Design SPA
│   ├─ 连接配置面板
│   ├─ 测量控制面板 (Last/Next/Jump)
│   ├─ 信号与通道配置
│   ├─ 实时日志/状态
│   └─ 用户操作手册
│
├─ FastAPI 后端 (localhost:8000)
│   ├─ /api/connect        → VISA 连接/断开/心跳
│   ├─ /api/measure        → 触发测量 + 采集
│   ├─ /api/excel          → Excel 读写状态
│   ├─ /api/config         → 配置导入/导出
│   └─ WebSocket /ws       → 实时推送（测量进度、心跳、日志）
│
├─ core/ 业务层（复用现有代码）
│   ├─ instrument_manager  → VISA 扫描/连接/识别
│   ├─ osc_*.py            → 示波器驱动
│   ├─ measurement.py      → measure_sequence / measure_monotony
│   ├─ capture.py          → Capture_Pic / savepic
│   ├─ easy_excel.py       → win32com Excel 操作
│   └─ test_manager.py     → 导航逻辑
│
└─ 系统依赖
    ├─ Excel.exe           ← win32com 操控
    └─ NI-VISA              ← PyVISA 后端
```

---

## 4. 前端页面结构

### 4.1 布局

```
┌──────────────────────────────────────────────────┐
│  App Shell                                        │
│  ┌──────────┬────────────────────────────────────│
│  │ Sidebar  │ Page Content                        │
│  │          │                                     │
│  │ 📡 连接  │  ┌──────────────────────────────┐  │
│  │ ⚙️ 配置  │  │ 根据菜单项切换对应页面        │  │
│  │ ▶ 测量  │  │                              │  │
│  │ 📊 数据  │  └──────────────────────────────┘  │
│  │ 📖 手册  │                                     │
│  │          │  ┌──────────────────────────────┐  │
│  │          │  │ 底部状态栏 (StatusBar)        │  │
│  │          │  │ 🟢 已连接 MSO58 | 第 12/45   │  │
│  └──────────┴──└──────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 4.2 页面拆解

| 页面 | 路径 | 对应桌面版 | 核心 Ant Design 组件 |
|---|---|---|---|---|
| 登录页 | `/login` | 无（新增） | Form, Input, Button, Alert |
| 连接页 | `/connect` | ConnectDialog + ActionBar | Form, Select, Input, Button, Badge, Alert |
| 配置页 | `/config` | ConfigPanel + SignalSetupDialog + NavBar | Card, Form, Select, InputNumber, Button.Group, Tabs |
| 测量页 | `/measure` | 控制面板 + 日志 + MSO 设置 | Table, Button, Timeline, Progress, Modal |
| 手册页 | `/help` | HelpDialog | Tree, Typography, Anchor |

### 4.3 状态管理

- **React Context** 管理全局状态: 连接态、当前测量进度、配置
- **useReducer** 处理复杂状态转换（连接中 → 已连接 → 断开中）
- **WebSocket Context** 提供日志流和实时通知，各页面按需消费

---

## 5. API 设计

### 5.1 REST 端点

除 `/api/auth/login` 外，所有端点需要在 Header 中携带 `Authorization: Bearer <token>`。
token 过期时间默认 8 小时，可通过环境变量配置。

```
# 认证（无需 token）
POST   /api/auth/login           body: {pin: "xxxx"}
  → 200 {token: "eyJ...", expires_at: "2026-07-02T22:00:00"}
  → 401 {detail: "PIN 不正确"}

# 连接管理
POST   /api/connect              body: {method, ip?, port?, use_socket?}
DELETE /api/connect
GET    /api/connect/status       → {connected, model, resource, last_heartbeat}

# Excel 操作
GET    /api/excel/info           → {file_path, sheet_names, active_sheet, pic_path}
POST   /api/excel/open           body: {file_path}
POST   /api/excel/activate-sheet body: {sheet_name}
GET    /api/excel/sheet-names    → string[]
GET    /api/excel/cell           query: row, col → {value}
POST   /api/excel/cell           body: {row, col, value}

# 测量操作（每个请求返回后通过 WS 推送进度）
POST   /api/measure/go           → {row, total, item, status: "ok"|"error"}
POST   /api/measure/last
POST   /api/measure/next
POST   /api/measure/jump         body: {target_row}
GET    /api/measure/status       → {test_type, row, total, current_item, pn_direction}
PUT    /api/measure/config       body: {test_type, init_row, signal*, mso*, ...}

# 配置管理
GET    /api/config/current       → {全量当前配置 JSON}
POST   /api/config/import        body: {file_path}  → 从 JSON 文件导入
POST   /api/config/export        body: {file_path}  → 导出到 JSON 文件
POST   /api/config/apply         body: {sheet_name} → 应用某 sheet 的保存配置
```

### 5.2 WebSocket (`/ws`)

服务器主动推送事件，JSON 格式：

```json
{"type": "log", "level": "info", "message": "测量完成: VCCIN_1.8V", "ts": "14:32:01"}
{"type": "heartbeat", "connected": true, "model": "MSO58"}
{"type": "progress", "current": 12, "total": 45, "item": "VCCIN_1.8V", "status": "ok"}
{"type": "excel", "event": "cell_updated", "row": 15, "col": "D"}
```

### 5.3 后端状态模型

后端维护单例 `AppState`（从现有 `app/state.py` 简化而来，去掉 Qt 信号，改用普通属性 + 锁）：

- 连接状态: `connected`, `osc_model`, `osc` 实例
- Excel 状态: `xls` 实例, `file_path`, `sheet_name`
- 测量状态: `test_type`, `row`, `total`, `current_item`, `pn_direction`
- 配置: 所有 `ConfigPanel` 对应的设置项

所有状态变更通过 WebSocket 广播到前端，确保 UI 始终与后端同步。

---

## 6. 认证设计（阶段 1: PIN 码 → 阶段 3: LDAP/AD）

### 6.1 设计原则

前后端只通过 JWT token 通信，前端完全不感知后端如何验证身份。将来从 PIN 切换到 LDAP/AD 时，前端零改动。

### 6.2 阶段 1：PIN 码认证

```
前端                          后端
  │                            │
  │  POST /api/auth/login      │
  │  {pin: "888888"}           │
  │ ─────────────────────────→ │
  │                            │ config.json.pin_hash = bcrypt(pin)
  │                            │ 比对 → 通过
  │  200 {token, expires_at}   │
  │ ←───────────────────────── │
  │                            │
  │  后续所有请求               │
  │  Authorization: Bearer xxx │
  │ ─────────────────────────→ │ 验证 JWT 签名 + 过期时间
```

- PIN 的 bcrypt hash 存在 `config.json` 中（初始值写死在代码里，用户可在配置页修改）
- JWT payload: `{sub: "local_user", role: "admin", iat, exp}`
- 单机单用户，role 固定为 `admin`

### 6.3 阶段 3 扩展：LDAP/AD

后端改动范围仅为 `POST /api/auth/login` 的实现：

```python
# 阶段 1: web/server/api/auth.py
class PinAuth:
    def authenticate(self, pin: str) -> str | None:
        # bcrypt 比对 config.json 中的 pin_hash

# 阶段 3: web/server/api/auth.py  （替换实现）
class LdapAuth:
    def __init__(self, server, domain, group_map):
        ...
    def authenticate(self, username: str, password: str) -> str | None:
        # ldap3 验证 AD 账号
        # 根据 AD group 映射 role: Domain Admins→admin, Engineers→operator
        # 返回 None 表示失败
```

JWT payload 随之扩展：
```json
// 阶段 1
{"sub": "local_user", "role": "admin"}
// 阶段 3
{"sub": "zhangsan@nettrix.com", "role": "operator", "display_name": "张三"}
```

前端路由守卫只需判断 `role`，三个阶段逻辑不变：
```typescript
// 路由守卫 — 始终不变
{role === 'admin' && <ConfigPage />}
{role !== 'viewer' && <MeasureGoButton />}
```

### 6.4 目录结构补充

```
web/server/api/
├─ auth.py        ← FastAPI 路由 + Depends(get_current_user)
├─ auth/
│   ├─ pin.py     ← 阶段 1: PinAuth
│   └─ ldap.py    ← 阶段 3: LdapAuth（预留接口，暂时 pass）
└─ deps.py        ← get_current_user 依赖注入
```

### 6.5 前端改动

```
web/client/src/
├─ contexts/AuthContext.tsx   ← 登录态、token 管理、路由守卫
├─ pages/LoginPage/           ← PIN 输入表单
└─ services/auth.ts           ← login() / logout() / getToken()
```

未登录时所有路由自动重定向到 `/login`。token 存 localStorage，页面刷新不丢失。

---

## 7. 项目目录结构

```
EE_Power_on_AutoTool_VER2.0/
├─ core/              ← 现有业务逻辑，不改动
├─ dialogs/           ← 现有桌面对话框，保留不动
├─ widgets/           ← 现有桌面组件，保留不动
├─ app/               ← 现有桌面应用层，保留不动
├─ web/               ← [新增] Web 版
│   ├─ server/        ← FastAPI 后端
│   │   ├─ main.py    ← FastAPI app 入口 + 生命周期
│   │   ├─ api/       ← 路由模块
│   │   │   ├─ connect.py
│   │   │   ├─ measure.py
│   │   │   ├─ excel.py
│   │   │   ├─ config.py
│   │   │   ├─ ws.py
│   │   │   └─ auth.py      ← get_current_user 依赖 + 路由
│   │   ├─ auth/            ← 可插拔认证后端
│   │   │   ├─ pin.py       ← 阶段 1: PinAuth
│   │   │   └─ ldap.py      ← 阶段 3: LdapAuth (预留)
│   │   └─ state.py   ← 后端 AppState（无 Qt 依赖）
│   ├─ client/        ← React + Vite 前端
│   │   ├─ src/
│   │   │   ├─ layouts/
│   │   │   ├─ pages/
│   │   │   │   ├─ LoginPage/     ← PIN 登录
│   │   │   │   ├─ ConnectPage/
│   │   │   │   ├─ ConfigPage/
│   │   │   │   ├─ MeasurePage/
│   │   │   │   └─ HelpPage/
│   │   │   ├─ components/  ← 共享组件
│   │   │   ├─ contexts/
│   │   │   │   └─ AuthContext.tsx   ← 登录态 + 路由守卫
│   │   │   ├─ hooks/       ← 自定义 hooks
│   │   │   └─ services/
│   │   │       └─ auth.ts   ← login() / logout() / getToken()
│   │   └─ package.json
│   └─ README.md
├─ main.py            ← 现有桌面版入口，不动
├─ requirements.txt   ← 补充 web 依赖
└─ Doc/               ← 现有文档，不动
```

---

## 8. 关键技术决策

### 7.1 为何复用 core/ 而不是重写

`core/` 层已经抽象得很好：`instrument_manager` 负责连接，`osc_*.py` 是驱动，`measurement.py` 是测量过程，`capture.py` 是采集保存，`easy_excel.py` 是 Excel 操作。每层通过 dict 传递状态，不依赖 Qt。FastAPI 后端只需要：

1. 把 API 请求映射到 core 函数调用
2. 把 `log.info/warn/error` 重定向到 WebSocket
3. 用 `asyncio.to_thread()` 包装 VISA 阻塞调用

### 7.2 日志捕获

现有 `core/logger.py` 的 `log` 实例通过 `LogStream` 写入 QPlainTextEdit。Web 版需要新增一个 `WebSocketHandler`（Python `logging.Handler`）把日志转发到 `/ws`。需要修改 `logger.py` 支持多 handler，或新建 `web/server/log_bridge.py`。

### 7.3 截图传输

桌面板截图保存在本地路径，Excel COM 直接插入。Web 版后端截图流程不变（VISA → 本地文件），但前端需要预览截图时，后端提供一个 `/api/screenshot/<filename>` 的静态文件路由。

### 7.4 线程安全

FastAPI 默认在事件循环中运行，但 VISA 和 COM 操作都是阻塞调用。所有 core 函数调用用 `asyncio.to_thread()` 包装，确保不阻塞事件循环。AppState 的读写用 `threading.Lock` 保护。

---

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| VISA/COM 阻塞导致 WebSocket 断连 | `asyncio.to_thread()` 隔离阻塞操作；WS 心跳独立于测量线程 |
| Excel COM 在无 GUI 环境下异常 | 后端启动时确保 Excel 以 Visible 模式打开 |
| 前端打包复杂（npm + Python 双构建） | 开发阶段 Vite dev server 独立运行；生产打包用 PyInstaller 将 React 产物嵌入 FastAPI 静态文件服务 |
| `logger.py` 修改影响桌面版 | 不修改 logger.py，新增 `web/server/log_bridge.py` 独立管理 WebSocket 日志管道 |

---

## 10. 预设：不做的事情

- ❌ ~~用户登录/权限系统~~（已纳入，见第 6 节）
- ❌ 数据库（SQLite/PostgreSQL）
- ❌ Docker 容器化
- ❌ 远程访问（SSH 隧道是目前最简方案，不需要内网穿透）
- ❌ Excel COM 以外的备选后端（openpyxl）
- ❌ 移动端适配
