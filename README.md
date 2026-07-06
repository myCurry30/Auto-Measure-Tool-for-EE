# EE Power On AutoTool V2.1

硬件工程师自动化测试工具 | 示波器 Sequence & Monotony 自动测量

liujch2

---

## 功能

- **示波器支持**：Tektronix MSO4/5/6、DPO7000、DPO5000 系列（GPIB/USB/TCPIP）
- **测试类型**：Sequence（时序）、Monotony（单调性，支持 P/N 翻转）
- **Excel 自动读写**：信号读取、数据写入、截图插入
- **一键配置示波器**：自动设置通道、测量项、触发、标签
- **CH Label Naming**：按通道标签命名截图，无需 Excel
- **Rise/Fall Time**：Monotony 模式下可选 Rise Time / Fall Time 测量
- **MSO 配置**：按测试类型独立保存，触发通道/边沿/电平可配置
- **配置管理**：自动保存/加载，支持跨机器部署（config_default.json）
- **Light/Dark 主题**

## 安装

### 免安装版
下载 `EE_Power_On_AutoTool_V2.1.0.exe`，双击运行。

### 安装包
下载 `EE_Power_On_AutoTool_V2.1.0_Setup.exe`，按向导安装。

### 系统要求
- Windows 10/11 64 位
- NI-VISA 驱动
- Microsoft Excel 2016+

## Web 版

`feature/web-version` 分支提供浏览器访问的 Web 版本，支持局域网多人使用。详见 `Doc/Web版部署SOP.md`。

## 文档

- [用户操作手册](Doc/用户操作手册.md)
- [用户操作手册 PDF](Doc/用户操作手册.pdf)
- [Web 版部署 SOP](Doc/Web版部署SOP.md)

## 分支

| 分支 | 说明 |
|------|------|
| `main` | 桌面版 V2.1.0 |
| `feature/web-version` | Web 版（FastAPI + React） |

## 技术栈

**桌面版**：Python 3.12 / PySide6 / PyVISA / win32com / PyInstaller

**Web 版**：FastAPI / React 18 / TypeScript / Ant Design / JWT / WebSocket
