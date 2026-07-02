# EE Power On AutoTool Web 版 — 部署 SOP

**适用版本**: V3.0 Web  
**目标机器**: Windows 10/11 64 位，需安装 NI-VISA + Excel  
**最后更新**: 2026-07-02

---

## 一、前置检查（目标机器）

### 1.1 硬件/系统

| 项目 | 要求 | 检查命令 |
|------|------|---------|
| 操作系统 | Windows 10/11 64 位 | `winver` |
| 内存 | ≥ 8GB | 任务管理器 → 性能 |
| 磁盘可用 | ≥ 500MB | 资源管理器 |
| 固定 IP | 局域网固定 IP，与工程师 PC 同子网 | `ipconfig` |

### 1.2 软件依赖

```
[ ] NI-VISA 驱动已安装
    验证: 打开 NI MAX → "设备和接口" 可看到 GPIB/USB 设备
    未安装: https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html

[ ] Microsoft Excel 已安装（2016 或更新）
    验证: 开始菜单搜索 Excel，能正常打开

[ ] Python 3.12+
    验证: cmd → python --version

[ ] Node.js 18+
    验证: cmd → node --version
```

---

## 二、部署步骤

### 2.1 获取代码

**方式 A: 从 Git 仓库拉取（推荐）**

```bash
git clone <仓库地址>
cd "EE_Power_on_AutoTool_VER2.0"
git checkout feature/web-version
```

**方式 B: 拷贝文件夹**

将整个项目文件夹（`EE_Power_on_AutoTool_VER2.0`）拷贝到目标机器任意路径，例如 `D:\AutoTool\`。

---

### 2.2 安装依赖

```bash
# 进入项目目录
cd "D:\AutoTool\EE_Power_on_AutoTool_VER2.0"

# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd web\client
npm install
cd ..\..
```

---

### 2.3 配置

#### 2.3.1 获取服务器 IP

```bash
ipconfig
```

找到 "以太网适配器" 或 "无线局域网适配器" 下的 **IPv4 地址**，例如 `192.168.1.50`。

确保此 IP 是**固定 IP**（非 DHCP 自动获取）。如果不是，在 Windows 网络设置中改为固定 IP。

#### 2.3.2 配置前端 API 地址

编辑 `web\client\.env`：

```
VITE_API_BASE=http://192.168.1.50:8000
```

> ⚠️ 把 `192.168.1.50` 换成你的实际服务器 IP

#### 2.3.3 配置用户和 MAC 地址

编辑项目根目录的 `user_pins.json`：

```json
{
  "admin": {
    "role": "admin",
    "display_name": "管理员",
    "mac_addresses": ["00:11:22:33:44:55"]
  },
  "张三": {
    "role": "operator",
    "display_name": "张三",
    "mac_addresses": ["AA:BB:CC:DD:EE:FF"]
  },
  "李四": {
    "role": "operator",
    "display_name": "李四",
    "mac_addresses": ["11:22:33:44:55:66", "FF:EE:DD:CC:BB:AA"]
  }
}
```

**如何获取工程师笔记本的 MAC 地址：**

在工程师的笔记本上，打开 cmd，输入：

```bash
ipconfig /all
```

找到正在使用的网络适配器（有线或无线），记录 "物理地址" 或 "Physical Address"，格式为 `XX-XX-XX-XX-XX-XX`。

填入 `user_pins.json` 时把 `-` 改为 `:`，例如 `00-1A-2B-3C-4D-5E` → `"00:1A:2B:3C:4D:5E"`。

每个用户的 `mac_addresses` 数组可填多个 MAC（如有线 + 无线两张网卡）。

#### 2.3.4 （建议）设置 JWT 密钥

```powershell
# PowerShell
$env:JWT_SECRET = "生成一个随机字符串"
# 或在 cmd
set JWT_SECRET=生成一个随机字符串
```

如果跳过此步，系统使用默认密钥（安全性较低，但局域网内可接受）。

---

### 2.4 构建前端

```bash
cd web\client
npm run build
cd ..\..
```

构建完成后 `web\client\dist\` 目录应存在，内含 `index.html` 和 `assets/` 文件夹。

---

### 2.5 启动服务器

**生产模式（推荐）：**

```bash
python web\start.py --prod
```

看到以下输出表示启动成功：

```
[web] 生产模式 — http://0.0.0.0:8000
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**保持运行**：不要关闭 cmd 窗口。建议配置为 Windows 服务或计划任务自动启动。

---

### 2.6 防火墙放行

首次启动时 Windows 防火墙可能弹出拦截提示，**点击"允许访问"**。

如果被拦截，手动添加规则：

```powershell
netsh advfirewall firewall add rule name="EE AutoTool Web" dir=in action=allow protocol=TCP localport=8000
```

---

## 三、验证

### 3.1 服务器本机验证

浏览器打开 `http://localhost:8000`：

- [ ] 看到登录页面（渐变色背景 + 用户名输入框）
- [ ] 输入正确用户名 → 点击"进入" → 成功跳转主界面
- [ ] 左侧边栏有：连接 / 配置 / 测量 / 手册

### 3.2 局域网验证

在工程师笔记本浏览器打开 `http://192.168.1.50:8000`（替换为实际 IP）：

- [ ] 登录成功
- [ ] 连接页 → 选择连接方式 → 连接示波器 → 看到状态变为"已连接"
- [ ] 配置页 → 修改参数 → 保存配置 → 提示成功
- [ ] 测量页 → 点击 GO → 实时日志有输出
- [ ] 手册页 → 点击左侧章节能跳转

---

## 四、常见问题

### Q1: 浏览器打开一片空白或无法访问

- 检查服务器 IP 是否可达：在工程师 PC 上 `ping 192.168.1.50`
- 检查防火墙是否放行 8000 端口
- 检查 `npm run build` 是否执行成功（`web/client/dist/` 目录是否存在）

### Q2: 登录提示"当前设备未注册"

- 工程师笔记本的 MAC 地址不在 `user_pins.json` 中
- 重新获取 MAC 地址并更新配置文件
- 配置文件修改后无需重启，下次登录自动生效

### Q3: 登录提示"正在获取设备信息，请重试"但一直重试

- ARP 表未命中，服务器和客户端不在同一子网
- 在服务器上手动 ping 一次客户端 IP：`ping 192.168.1.xxx`
- 然后再试登录

### Q4: 连接示波器失败

- 确认服务器上已安装 NI-VISA
- 确认示波器已开机且线缆连接正常
- 如果是 IP 连接：确认示波器 IP 和服务器 IP 互通
- 如果是 GPIB/USB：确认线缆插入服务器 USB 口

### Q5: Excel 操作失败

- 确认服务器上已安装 Microsoft Excel
- 确认 Excel 文件未被其他程序独占打开
- 检查文件路径是否包含中文或特殊字符

### Q6: 如何添加/删除用户

管理员登录后，通过 API 管理（或在服务器上直接编辑 `user_pins.json`）：

```bash
# 列出所有用户
curl http://localhost:8000/api/auth/users -H "Authorization: Bearer <admin_token>"

# 或者直接编辑文件
notepad user_pins.json

# 修改后无需重启
```

### Q7: 如何更新代码

```bash
cd "D:\AutoTool\EE_Power_on_AutoTool_VER2.0"
git pull                         # 拉取最新代码
pip install -r requirements.txt  # 更新 Python 依赖
cd web\client && npm install && npm run build  # 更新前端
# 重启 python web\start.py --prod
```

---

## 五、快速参考

| 项目 | 值 |
|------|-----|
| 服务器固定 IP | `________.________.________.________` |
| 端口 | `8000` |
| 工程师访问地址 | `http://________:8000` |
| 管理员姓名 | ________ |
| 工程师姓名 | ________ |
| 项目路径 | ________ |
| JWT 密钥 | ________ |

> 部署完成后填写此表，贴到服务器旁边。
