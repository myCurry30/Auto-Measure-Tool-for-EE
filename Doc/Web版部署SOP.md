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

**方式 B: 拷贝最小文件集（推荐）**

Web 部署只需要以下文件，不需要整个项目：

```
目标路径: C:\EE_POWER_ON_Tool_WEB\autotool-web\

core/              ✅ 示波器驱动 / 数据采集 / Excel 操作
web/               ✅ FastAPI 后端 + React 前端源码
requirements.txt   ✅ Python 依赖清单
user_pins.json     ✅ 用户 MAC 绑定配置
config.json        ✅ 配置（如有）
```

> 桌面版代码（`app/`、`widgets/`、`dialogs/`、`main.py`、`My_ui.py` 等）和开发目录（`.claude/`、`.agents/`、`installer/`、`Doc/`）**不需要**拷贝。

**打包方式：**

在源机器项目根目录下：

```bash
# 打包为 zip（Windows）
powershell Compress-Archive -Path core,web,requirements.txt,user_pins.json,config.json -DestinationPath autotool-web.zip

# 或打包为 tar.gz（Git Bash）
tar -czf autotool-web.tar.gz core/ web/ requirements.txt user_pins.json config.json
```

将 `autotool-web.zip` 拷贝到目标机器 → 解压到 `C:\EE_POWER_ON_Tool_WEB\autotool-web\`。

---

### 2.2 安装依赖

```bash
# 进入项目目录
cd "C:\EE_POWER_ON_Tool_WEB\autotool-web"

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

`web\client\.env` 已预置默认值：

```
VITE_API_BASE=http://10.31.133.57:8200
```

如果服务器 IP 或端口有变动，编辑此文件修改地址后重新 `npm run build` 即可。

> 提交到代码仓库的默认值避免了每次更新被覆盖为 `localhost`。

#### 2.3.3 配置用户和 MAC 地址

编辑项目根目录的 `user_pins.json`：

```json
{
  "admin": {
    "role": "admin",
    "display_name": "管理员",
    "mac_addresses": ["00-11-22-33-44-55"]
  },
  "张三": {
    "role": "operator",
    "display_name": "张三",
    "mac_addresses": ["AA-BB-CC-DD-EE-FF"]
  },
  "李四": {
    "role": "operator",
    "display_name": "李四",
    "mac_addresses": ["11-22-33-44-55-66", "FF-EE-DD-CC-BB-AA"]
  }
}
```

**如何获取工程师笔记本的 MAC 地址：**

在工程师的笔记本上，打开 cmd，输入：

```bash
ipconfig /all
```

找到正在使用的网络适配器（有线或无线），记录 "物理地址" 或 "Physical Address"，格式为 `XX-XX-XX-XX-XX-XX`。

直接复制 `ipconfig /all` 中的物理地址填入即可，支持 `00-1A-2B-3C-4D-5E` 或 `00:1A:2B:3C:4D:5E` 两种格式。

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

**保持运行**：不要关闭 cmd 窗口。下面配置为系统服务实现开机自启。

#### 2.5.1 配置开机自启（计划任务 — 推荐）

先创建启动脚本。两种方式任选：

**方式一：PowerShell 直接生成**

```powershell
@"
@echo off
cd /d C:\EE_POWER_ON_Tool_WEB\autotool-web
python web\start.py --prod
"@ | Out-File -FilePath "C:\EE_POWER_ON_Tool_WEB\autotool-web\start_server.bat" -Encoding ASCII
```

**方式二：记事本手动创建**

打开记事本 → 粘贴以下 3 行 → 保存到 `C:\EE_POWER_ON_Tool_WEB\autotool-web\start_server.bat`：

```batch
@echo off
cd /d C:\EE_POWER_ON_Tool_WEB\autotool-web
python web\start.py --prod
```

然后以**管理员身份**打开 PowerShell，执行：

```powershell
# 创建计划任务：开机自动启动，后台运行
$action = New-ScheduledTaskAction -Execute "C:\EE_POWER_ON_Tool_WEB\autotool-web\start_server.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "EE AutoTool Web" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

# 立即触发一次（不需要重启生效）
Start-ScheduledTask -TaskName "EE AutoTool Web"
```

**管理命令**：

```powershell
Get-ScheduledTask -TaskName "EE AutoTool Web"    # 查看状态
Start-ScheduledTask -TaskName "EE AutoTool Web"  # 手动启动
Stop-ScheduledTask -TaskName "EE AutoTool Web"   # 手动停止
Unregister-ScheduledTask -TaskName "EE AutoTool Web" -Confirm:$false  # 删除
```

#### 2.5.2 备选方案：NSSM 注册为 Windows 服务

如果希望像系统服务一样通过 `services.msc` 管理，可以用 NSSM：

```powershell
# 1. 下载 nssm.exe（单文件，无需安装）
# https://nssm.cc/download → 解压 nssm.exe 到 C:\Windows\System32\

# 2. 注册服务
nssm install "EE AutoTool Web" "C:\Path\To\python.exe" "C:\EE_POWER_ON_Tool_WEB\autotool-web\web\start.py --prod"
nssm set "EE AutoTool Web" AppDirectory "C:\EE_POWER_ON_Tool_WEB\autotool-web"
nssm set "EE AutoTool Web" Start SERVICE_AUTO_START

# 3. 启动
nssm start "EE AutoTool Web"
```

> NSSM 会自动重启崩溃的进程，比计划任务更健壮，但需要下载第三方工具。

#### 2.5.3 服务日常管理

> 以下命令均在服务器上以**管理员身份** PowerShell 执行。

**恢复服务（CMD 窗口被误关、重启后手动拉起）：**

```powershell
Start-ScheduledTask -TaskName "EE AutoTool Web"
```

等几秒后工程师即可访问。

**停止服务：**

```powershell
Stop-ScheduledTask -TaskName "EE AutoTool Web"
```

**查看服务状态：**

```powershell
Get-ScheduledTask -TaskName "EE AutoTool Web"
```

关键看 `State` 字段 — `Ready`（已就绪，未运行）、`Running`（正在运行）、`Disabled`（已禁用）。

**验证开机自启：**

选人少时重启服务器测试：

```powershell
Restart-Computer -Force
```

重启后在工程师笔记本浏览器访问 `http://<服务器IP>:8000`，能打开登录页即说明自启生效。

> 计划任务后台运行**不弹 CMD 窗口**，不会误关。日常启停用上述 PowerShell 命令，不要再手动 `python web\start.py --prod`。

---

### 2.6 防火墙放行

> 在**服务器**上以**管理员身份**执行：Win+R → `powershell` → Ctrl+Shift+Enter

```powershell
netsh advfirewall firewall add rule name="EE AutoTool Web" dir=in action=allow protocol=TCP localport=8000
```

输出 `确定。` 即生效。

> 如果之前启动服务器时已经弹出过防火墙拦截提示并点击了"允许访问"，此步可跳过。此命令是手动补加规则，适用于未弹窗的情况。

**验证**：在工程师笔记本浏览器访问 `http://<服务器IP>:8000`，看到登录页面则防火墙配置正确。

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

**如果是 git clone 部署的：**

```bash
cd "C:\EE_POWER_ON_Tool_WEB\autotool-web"
git pull
pip install -r requirements.txt
cd web\client && npm install && npm run build
# 重启服务
```

**如果是 zip 包部署的（无 .git 目录）：**

在**源机器**（有 git 的机器）上拉取最新代码，重新打包：

```bash
# 源机器
git pull
powershell Compress-Archive -Path core,web,requirements.txt,user_pins.json,config.json -DestinationPath autotool-web.zip -Force
```

将 `autotool-web.zip` 传到服务器 → 解压覆盖原目录（`user_pins.json` 会被覆盖，注意先备份）：

```powershell
# 服务器上
Stop-ScheduledTask -TaskName "EE AutoTool Web"
# 备份 user_pins.json
copy C:\EE_POWER_ON_Tool_WEB\autotool-web\user_pins.json C:\EE_POWER_ON_Tool_WEB\autotool-web\user_pins.json.bak
# 解压覆盖
Expand-Archive -Path autotool-web.zip -DestinationPath C:\EE_POWER_ON_Tool_WEB\autotool-web -Force
# 恢复 user_pins.json
copy C:\EE_POWER_ON_Tool_WEB\autotool-web\user_pins.json.bak C:\EE_POWER_ON_Tool_WEB\autotool-web\user_pins.json
# 重建前端
cd C:\EE_POWER_ON_Tool_WEB\autotool-web\web\client
npm run build
# 重启
Start-ScheduledTask -TaskName "EE AutoTool Web"
```

> 如果只改了后端 `web/server/` 下的文件，无需 `npm run build`，直接重启服务即可。

---

## 附：纯内网部署（目标机器无外网）

如果部署的服务器只能访问局域网，无法下载任何东西，需要提前在一台**有外网的机器**上准备好以下文件，再拷贝过去。

### A. 提前下载清单

| # | 文件 | 下载方式 | 大小约 |
|---|------|---------|--------|
| 1 | Python 3.12 安装包 | https://www.python.org/downloads/ | ~25MB |
| 2 | Node.js 18+ 安装包 | https://nodejs.org/ | ~30MB |
| 3 | NI-VISA 驱动 | https://www.ni.com → 搜索 NI-VISA | ~400MB |
| 4 | Python 依赖离线包（见步骤 B） | `pip download` | ~50MB |
| 5 | 前端 node_modules（见步骤 C） | 从源机器直接拷贝 | ~200MB |

### B. Python 依赖离线包

在**有外网的机器**上（和服务器同 Windows 版本、同 Python 版本）：

```bash
# 进入项目目录
cd "C:\EE_POWER_ON_Tool_WEB\autotool-web"

# 创建离线包目录
mkdir pip_offline

# 下载所有依赖的 .whl 文件（不下载 pywin32，它是预装的系统扩展）
pip download -r requirements.txt -d pip_offline

# 把整个 pip_offline 文件夹拷到目标机器
```

在**目标机器（无外网）**上：

```bash
cd "C:\EE_POWER_ON_Tool_WEB\autotool-web"
pip install --no-index --find-links=pip_offline -r requirements.txt
```

### C. 前端依赖

**方式一（推荐）：从源机器直接拷贝 node_modules**

在那台有外网的机器上，项目路径下：

```bash
cd web\client
npm install               # 会生成 node_modules 文件夹
```

把整个 `web\client\node_modules` 文件夹（约 200MB）拷贝到目标机器的相同位置。

目标机器上**不再需要执行 `npm install`**，直接可以 `npm run build`。

**方式二：离线打包**

```bash
# 有外网的机器上
cd web\client
npm pack node_modules      # 生成 .tgz 文件（不推荐，不如直接拷文件夹）

# 或者用 npm ci --prefer-offline 配合缓存（需要预填充 npm cache）
```

### D. 纯内网部署完整流程

```
有外网的机器（提前准备）:

1. 下载 Python 安装包 → 拷到 U 盘
2. 下载 Node.js 安装包 → 拷到 U 盘  
3. 下载 NI-VISA 安装包 → 拷到 U 盘
4. 创建项目目录 && mkdir pip_offline
5. 拷贝最小文件（core/, web/, requirements.txt, user_pins.json, config.json）到项目目录
6. pip download -r requirements.txt -d pip_offline
7. cd web\client && npm install
8. 把项目目录（含 pip_offline + node_modules）打包拷到 U 盘

目标机器（无外网）:
         ↓ 从 U 盘拷入

1. 安装 Python（运行安装包）
2. 安装 Node.js（运行安装包）
3. 安装 NI-VISA（运行安装包）
4. 解压项目到目标路径
5. pip install --no-index --find-links=pip_offline -r requirements.txt
6. cd web\client && npm run build
7. 编辑 user_pins.json（用户 + MAC）
8. 编辑 web\client\.env（服务器 IP）
9. python web\start.py --prod
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
