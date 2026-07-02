# EE Power On AutoTool — Web 版设计文档

**日期**: 2026-07-02
**分支**: `feature/web-version`
**状态**: 设计完成，待实施

---

## 1. 目标与范围

将现有 PySide6 桌面应用改造为 Web 架构，用户在浏览器中完成示波器自动测量工作。桌面版保持不动，Web 版在新分支独立开发。

**使用场景**: 局域网多人使用 — 一台 Windows 服务器部署后端（需安装 NI-VISA + Excel），绑定固定 LAN IP。工程师在各自 PC 的浏览器中访问同一地址，各自输入示波器 IP/GPIB 连接到不同的示波器。

**范围**:
- 完整移植现有功能：示波器连接、Sequence/Monotony 测量、Excel 读写、配置管理、用户手册
- 多人并发使用（每人独立会话，独立示波器连接 + 独立 Excel 实例）
- PIN 码登录认证
- 不新增测量类型或示波器型号
- 不改变 `core/` 层业务逻辑

**不做**:
- 数据库持久化（配置仍用 JSON 文件，用户 PIN 用配置文件）
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
局域网 ─────────────────────────────────────────────────────────────
│
│  工程师 A (PC)              工程师 B (PC)
│  ├─ 浏览器                   ├─ 浏览器
│  │  http://192.168.1.50      │  http://192.168.1.50
│  │  连接 → 示波器 A           │  连接 → 示波器 B
│  │                              │
│  │       ┌──────────────────────┘
│  │       ▼
│  ┌──────────────────────────────────────────────┐
│  │  服务器 PC (固定 LAN IP: 192.168.1.50)        │
│  │  Windows + NI-VISA + Excel                    │
│  │                                                │
│  │  FastAPI 后端 (bind 0.0.0.0:8000)              │
│  │  ├─ SessionManager   ← 每用户独立会话          │
│  │  │   ├─ 用户 A: osc_A + xls_A                 │
│  │  │   └─ 用户 B: osc_B + xls_B                 │
│  │  ├─ /api/auth         → 登录/PIN 管理          │
│  │  ├─ /api/connect      → VISA 连接/断开/心跳     │
│  │  ├─ /api/measure      → 测量 + 采集            │
│  │  ├─ /api/excel        → Excel 读写             │
│  │  ├─ /api/config       → 配置导入/导出           │
│  │  └─ WebSocket /ws     → 实时推送（按用户隔离）   │
│  │                                                │
│  │  core/ 业务层（复用现有代码）                    │
│  │  每个用户会话持有独立的 osc + xls 实例          │
│  │                                                │
│  └──────────────────────────────────────────────┘
│              │                    │
│      VISA/TCPIP            GPIB/USB
│              │                    │
│       示波器 A              示波器 B
│
└──────────────────────────────────────────────────────────────────
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

**前端**: React Context + useReducer 管理全局状态（连接态、测量进度、配置），WebSocket 按用户推送。

**后端**: `SessionManager` 单例维护 `{username → UserSession}` 字典：

```python
class UserSession:
    osc: OscilloscopeBase | None    # 当前连接的示波器驱动实例
    xls: EasyExcel | None           # 当前打开的 Excel 实例
    rm: ResourceManager | None      # 此用户的 VISA 资源管理器
    test_type: str                  # "sequence" | "monotony"
    row: int                        # 当前测量行
    state: dict                     # 测量上下文（signal*, ch*, pn_direction...）
    config: dict                    # 用户当前配置
    log_queue: asyncio.Queue        # 此用户的日志队列（推送到 WS）
```

每个工程师登录后获得独立会话。连接到哪个示波器、打开哪个 Excel，完全隔离，互不影响。

---

## 5. API 设计

### 5.1 REST 端点

除 `/api/auth/login` 外，所有端点需要在 Header 中携带 `Authorization: Bearer <token>`。
token 过期时间默认 8 小时，可通过环境变量配置。

```
# 认证（无需 token）
POST   /api/auth/login           body: {username: "zhangsan"}
  → 200 {token: "eyJ...", expires_at: "2026-07-02T22:00:00", role: "operator", display_name: "张三"}
  → 401 {detail: "用户名不存在"}
  → 403 {detail: "当前设备未注册，MAC 地址不匹配"}
  → 425 {detail: "正在获取设备信息，请重试"}  ← ARP 未命中，前端自动重试

# 用户管理（需 admin role）
GET    /api/auth/users           → 列出所有用户及其 MAC 绑定
POST   /api/auth/users           body: {username, role, display_name, mac_addresses}
PUT    /api/auth/users/{name}    body: {role?, display_name?, mac_addresses?}
DELETE /api/auth/users/{name}    → 删除用户

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

### 5.2 WebSocket (`/ws?token=<jwt>`)

连接时传 JWT 参数，后端按 `username` 路由到对应用户的日志队列。每个用户只收到自己操作的推送：

```json
{"type": "log", "level": "info", "message": "测量完成: VCCIN_1.8V", "ts": "14:32:01"}
{"type": "heartbeat", "connected": true, "model": "MSO58", "scope_addr": "TCPIP0::192.168.1.100::INSTR"}
{"type": "progress", "current": 12, "total": 45, "item": "VCCIN_1.8V", "status": "ok"}
{"type": "excel", "event": "cell_updated", "row": 15, "col": "D"}
```

### 5.3 后端状态模型

`SessionManager` 是全局单例，维护 `{username → UserSession}` 字典。每个 `UserSession` 独立持有：

- 连接状态: `connected`, `osc` 实例（可以是不同型号的驱动）
- Excel 状态: `xls` 实例, `file_path`, `sheet_name`（各自打开不同的 Excel 文件）
- 测量状态: `test_type`, `row`, `total`, `current_item`, `pn_direction`
- 配置: 所有 `ConfigPanel` 对应的设置项

**并发安全**：
- 每个 `UserSession` 内部操作是串行的（单用户单线程）
- 不同 `UserSession` 之间完全独立，VISA 连接和 Excel 实例互不冲突
- 全局配置文件和 `user_pins.json` 的读写用 `threading.Lock` 保护
- 测量操作用 `asyncio.to_thread()` 包装，防止阻塞事件循环

---

## 6. 认证设计（阶段 1: PIN 码 → 阶段 3: LDAP/AD）

### 6.1 设计原则

前后端只通过 JWT token 通信，前端完全不感知后端如何验证身份。将来从 PIN 切换到 LDAP/AD 时，前端零改动。

### 6.2 阶段 1：用户名 + MAC 地址自动验证

**管理方式**：管理员预设用户名和对应笔记本的 MAC 地址到 `user_pins.json`。用户无需记 PIN，只需输入用户名即可登录。

```json
// user_pins.json — 管理员维护在服务器上
{
  "zhangsan": {
    "role": "operator",
    "mac_addresses": ["00:1A:2B:3C:4D:5E"]
  },
  "lisi": {
    "role": "operator",
    "mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
  },
  "admin": {
    "role": "admin",
    "mac_addresses": ["00:11:22:33:44:55"]
  }
}
```

每个用户可绑定多个 MAC 地址（如笔记本有线 + 无线网卡）。

**登录流程**：

```
工程师浏览器                         服务器
  │                                  │
  │  POST /api/auth/login            │
  │  {username: "zhangsan"}          │
  │ ───────────────────────────────→ │
  │                                  │ 1. 从 TCP 连接取客户端 IP
  │                                  │    client_ip = request.client.host
  │                                  │
  │                                  │ 2. 查 ARP 表获取 MAC
  │                                  │    arp -a <client_ip>
  │                                  │    → "00-1a-2b-3c-4d-5e"
  │                                  │
  │                                  │ 3. 双重校验:
  │                                  │    ✓ user_pins.json 中有 "zhangsan"
  │                                  │    ✓ MAC 在 mac_addresses 列表中
  │                                  │
  │  200 {token, expires_at,         │
  │        role: "operator",         │
  │        display_name: "张三"}     │
  │ ←─────────────────────────────── │
  │                                  │
  │  后续请求 Header:                 │
  │  Authorization: Bearer xxx       │
  │ ───────────────────────────────→ │ 验证 JWT → 注入 username → SessionManager
```

**ARP 解析实现**（后端用 `subprocess` 调系统命令，不走前端）：

```python
import subprocess, re

def get_mac_from_ip(ip: str) -> str | None:
    """通过 ARP 表解析 IP → MAC 地址（Windows）。"""
    try:
        result = subprocess.run(
            ['arp', '-a', ip],
            capture_output=True, text=True, timeout=5
        )
        # Windows 输出: "192.168.1.100    00-1a-2b-3c-4d-5e    dynamic"
        match = re.search(
            r'([0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}'
            r'[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2})',
            result.stdout
        )
        if match:
            return match.group(1).replace('-', ':').upper()
    except Exception:
        pass
    return None
```

**容错说明**：
- 用户只需输入用户名，无需任何密码——拿着注册过的笔记本就是凭证
- 用户换了笔记本需要找管理员更新 `mac_addresses` 列表
- ARP 表只能解析**同一子网**内的 IP（局域网天然满足）
- DHCP 分配导致 IP 变化不影响，MAC 不变
- ARP 缓存未命中时返回 425，前端自动重试

- JWT payload: `{sub: "zhangsan", role: "operator", display_name: "张三", iat, exp}`
- 每个用户的示波器连接、Excel 实例、测量进度完全隔离
- token 过期默认 8 小时，可通过环境变量配置

### 6.3 阶段 3 扩展：LDAP/AD

后端改动范围仅为 `POST /api/auth/login` 的实现：

```python
# 阶段 1: web/server/api/auth/pin.py
class PinAuth:
    def authenticate(self, username: str, pin: str) -> dict | None:
        # 从 user_pins.json 读取 {pin_hash, role}
        # bcrypt 比对 → 返回 {"role": "operator"} 或 None

# 阶段 3: web/server/api/auth/ldap.py  （替换实现）
class LdapAuth:
    def __init__(self, server, domain, group_map):
        ...
    def authenticate(self, username: str, password: str) -> dict | None:
        # ldap3 验证 AD 账号
        # 根据 AD group 映射 role: Domain Admins→admin, Engineers→operator
        # 返回 {"role": "operator", "display_name": "张三"} 或 None
```

- 登录接口签名不变：`POST /api/auth/login {username, pin/password}`
- 前端登录表单始终是 **单个用户名输入框**（阶段 1 无需密码；阶段 3 再加密码字段）
- JWT payload 随之扩展：
```json
// 阶段 1
{"sub": "zhangsan", "role": "operator"}
// 阶段 3
{"sub": "zhangsan@nettrix.com", "role": "operator", "display_name": "张三"}
```

前端路由守卫只需判断 `role`，两个阶段逻辑不变：
```typescript
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
| 多人同时连接不同示波器，VISA 资源冲突 | PyVISA ResourceManager 线程安全，每个 UserSession 独立创建 ResourceManager |
| Excel COM 多实例同时运行 | `win32com.Dispatch()` 每次调用创建独立 Excel 进程，各用户互不干扰 |
| VISA/COM 阻塞导致 WebSocket 断连 | `asyncio.to_thread()` 隔离阻塞操作；WS 心跳独立于测量线程 |
| Excel COM 在无 GUI 环境下异常 | 后端启动时确保 Excel 以 Visible 模式打开 |
| 前端打包复杂（npm + Python 双构建） | 开发阶段 Vite dev server 独立运行；生产打包用 PyInstaller 将 React 产物嵌入 FastAPI 静态文件服务 |
| `logger.py` 修改影响桌面版 | 不修改 logger.py，新增 `web/server/log_bridge.py` 独立管理 WebSocket 日志管道 |
| 服务器单点故障（所有工程师依赖同一台服务器） | 服务器宕机期间工程师可临时用桌面版；Web 版与桌面版共享 core/ 层，互不影响 |
| ARP 缓存未命中导致 MAC 验证失败（首次登录或 ARP 过期） | 后端返回 425 状态码，前端自动重试（最多 3 次 × 2s 间隔）；后端可先 ping 目标 IP 预热 ARP |
| 客户端 IP 跨子网导致 ARP 解析不到 MAC | 约束服务器和所有工程师 PC 必须在同一 VLAN/子网（企业内网环境天然满足） |

---

## 10. 预设：不做的事情

- ❌ 数据库（SQLite/PostgreSQL）—— 配置仍用 JSON 文件
- ❌ Docker 容器化
- ❌ Excel COM 以外的备选后端（openpyxl）
- ❌ 移动端适配
- ❌ 跨 VLAN/子网部署（ARP MAC 检测依赖同一子网）
- ❌ 自动发现局域网内的示波器（仍由用户手动输入地址）
