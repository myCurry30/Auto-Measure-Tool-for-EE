"""Help dialog — embedded user manual with chapter-index navigation."""
import os
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QSplitter,
                                QTreeWidget, QTreeWidgetItem, QTextBrowser,
                                QPushButton, QWidget, QFileDialog)
from PySide6.QtCore import Qt


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown → HTML converter (handles the manual's formatting)
# ═══════════════════════════════════════════════════════════════════════════════

def md_to_html(text: str) -> str:
    """Convert a minimal Markdown subset to HTML."""
    lines = text.split('\n')
    html = []
    in_table = False
    in_ul = False
    in_ol = False
    in_code_block = False
    code_lines = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            html.append('</ul>')
            in_ul = False
        if in_ol:
            html.append('</ol>')
            in_ol = False

    def flush_table():
        nonlocal in_table
        if in_table:
            html.append('</tbody></table>')
            in_table = False

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                html.append(f'<pre><code>{"".join(code_lines)}</code></pre>')
                code_lines = []
                in_code_block = False
            else:
                flush_list()
                flush_table()
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line + '\n')
            continue

        # Horizontal rule
        if line.strip() == '---':
            flush_list()
            flush_table()
            html.append('<hr>')
            continue

        # Table
        if '|' in line and line.strip().startswith('|'):
            flush_list()
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(c.replace('-', '').replace(':', '').strip() == '' for c in cells):
                continue  # separator row
            tag = 'th' if not in_table else 'td'
            row_html = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            if not in_table:
                html.append('<table border="1" cellpadding="4" cellspacing="0">'
                            '<thead>' + row_html + '</thead><tbody>')
                in_table = True
            else:
                html.append(row_html)
            continue
        else:
            if in_table:
                # Table ended — check if next line is also a table row or not
                # Simple heuristic: if not starting with |, table ended
                flush_table()

        # Headings
        stripped = line.strip()
        if stripped.startswith('### '):
            flush_list()
            html.append(f'<h3 id="{_anchor_id(stripped[4:])}">{_inline(stripped[4:])}</h3>')
            continue
        if stripped.startswith('## '):
            flush_list()
            html.append(f'<h2 id="{_anchor_id(stripped[3:])}">{_inline(stripped[3:])}</h2>')
            continue
        if stripped.startswith('# '):
            flush_list()
            html.append(f'<h1>{_inline(stripped[2:])}</h1>')
            continue

        # Checkbox list
        cb_match = re.match(r'^- \[(.)\] (.+)', stripped)
        if cb_match:
            if not in_ul:
                flush_list()
                html.append('<ul class="checklist">')
                in_ul = True
            checked = cb_match.group(1) != ' '
            chk = '☑' if checked else '☐'
            html.append(f'<li class="checklist">{chk} {_inline(cb_match.group(2))}</li>')
            continue

        # Unordered list
        ul_match = re.match(r'^- (.+)', stripped)
        if ul_match:
            if not in_ul:
                flush_list()
                html.append('<ul>')
                in_ul = True
            html.append(f'<li>{_inline(ul_match.group(1))}</li>')
            continue

        # Ordered list
        ol_match = re.match(r'^\d+\. (.+)', stripped)
        if ol_match:
            if not in_ol:
                flush_list()
                html.append('<ol>')
                in_ol = True
            html.append(f'<li>{_inline(ol_match.group(1))}</li>')
            continue

        # Empty line — close lists
        if not stripped:
            flush_list()
            html.append('<p>')
            continue

        # Regular paragraph
        flush_list()
        html.append(f'<p>{_inline(stripped)}</p>')

    # Flush any remaining open structures
    flush_list()
    flush_table()
    if in_code_block:
        html.append(f'<pre><code>{"".join(code_lines)}</code></pre>')

    return '\n'.join(html)


def _inline(text: str) -> str:
    """Convert inline markdown to HTML."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    return text


def _anchor_id(heading: str) -> str:
    """Generate anchor ID from heading text (e.g. '1. 环境准备' → '1-环境准备')."""
    # Remove leading digits+dot+space, replace spaces with hyphens
    h = re.sub(r'^\d+\.\s*', '', heading)
    return h.replace(' ', '-')


# ═══════════════════════════════════════════════════════════════════════════════
# Chapter extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_chapters(md_text: str) -> list[dict]:
    """Extract H2 and H3 headings with their anchor IDs from markdown.

    Returns list of {level, title, anchor}.
    """
    chapters = []
    for line in md_text.split('\n'):
        line = line.strip()
        if line.startswith('## ') and not line.startswith('### '):
            title = line[3:].strip()
            # Skip "目录" TOC section
            if title == '目录':
                continue
            chapters.append({
                'level': 2,
                'title': title,
                'anchor': _anchor_id(title),
                'children': []
            })
        elif line.startswith('### '):
            title = line[4:].strip()
            if chapters:
                chapters[-1]['children'].append({
                    'level': 3,
                    'title': title,
                    'anchor': _anchor_id(title),
                })
    return chapters


# ═══════════════════════════════════════════════════════════════════════════════
# Embedded user manual (bundled in code, no external file needed)
# ═══════════════════════════════════════════════════════════════════════════════

_EMBEDDED_MANUAL = r"""# EE Power On AutoTool V2.2 — 用户操作手册

硬件工程师自动化测试工具 | 示波器 Sequence & Monotony 自动测量

liujch2

---

## 目录

1. [环境准备](#环境准备)
2. [程序安装](#程序安装)
3. [界面总览](#界面总览)
4. [操作流程](#操作流程)
5. [功能详解](#功能详解)
6. [配置参考](#配置参考)
7. [常见问题](#常见问题)

---

## 1. 环境准备

### 1.1 硬件需求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| 内存 | 建议 8GB 以上 |
| 磁盘 | 200MB 可用空间 |
| 示波器 | Tektronix MSO4/5/6、DPO7000、DPO5000 系列 |
| 连接线 | GPIB 线缆 / USB 线缆 / 网线（任选其一） |

### 1.2 软件依赖（必须安装）

目标设备需要以下两项系统级软件，PyInstaller 打包的 exe 无法包含它们：

#### NI-VISA 驱动（连接示波器必需）

**下载地址**：https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html

**安装步骤**：
1. 打开上述网址，搜索 "NI-VISA"
2. 选择最新版本
3. 下载完整安装包（约 200–400 MB）
4. 以**管理员身份**运行安装程序
5. 按默认选项完成安装
6. **重启设备**使驱动生效

> **备选方案**：如果无法安装 NI-VISA，程序内置了 pyvisa-py（纯 Python 后端），仅支持 TCPIP 连接，部分示波器功能可能受限。

#### Microsoft Excel（读写 Excel 必需）

**获取方式**：

| 版本 | 链接 | 说明 |
|------|------|------|
| Microsoft 365（推荐） | https://www.microsoft.com/microsoft-365 | 订阅制，持续更新 |
| Office 2021 买断版 | https://www.microsoft.com/microsoft-365/buy/compare-all-microsoft-365-products | 一次性购买 |

> 如果仅需要查看保存的截图文件，不需要在设备上操作 Excel，可以跳过此项。

### 1.3 检查清单

在开始使用前，逐项确认：

- [ ] NI-VISA 已安装并重启过设备
- [ ] Microsoft Excel 已安装
- [ ] 示波器已开机并通过 GPIB/USB/网线连接到电脑
- [ ] 已经准备好 Excel 测试报告模板文件

---

## 2. 程序安装

### 2.1 从安装包安装（推荐）

1. 双击 `EE_Power_On_AutoTool_V2.2.0_Setup.exe`
2. 点击 **Next**，阅读许可协议
3. 选择安装目录（默认 `C:\Program Files\EE Power On AutoTool\`）
4. 点击 **Install**，等待完成
5. 桌面和开始菜单会自动创建快捷方式

### 2.2 绿色免安装版

直接复制 `EE_Power_On_AutoTool.exe` 到目标设备，双击运行即可。无需安装，无需 Python。

### 2.3 卸载

- **通过安装包安装的**：开始菜单 → EE Power On AutoTool → Uninstall
- **绿色免安装版**：直接删除 `.exe` 文件即可

> 卸载时会询问是否保留用户数据（`outputs/` 截图文件夹 和 `logs/` 日志文件夹）。

---

## 3. 界面总览

```
+----------------------------------------------------------+
|  File  Settings                         <IP info>         |
|  Toolbar with quick actions                              |
+----------------------------------------------------------+
|  +---------------------+  +--------------------------+   |
|  |  FILE PATHS         |  |  SETTINGS                |   |
|  |  Excel: [______]    |  |  Sheet: [v Sheet1    ]   |   |
|  |  Pic:   [______]    |  |  Type:  [v Sequence  ]   |   |
|  |                     |  |  Init R: [21]            |   |
|  |                     |  |  Signal1: [x] R:[21] C:[4]|  |
|  |                     |  |  Signal2: [ ] R:[21] C:[2]|  |
|  |                     |  |  Signal3: [ ] R:[21] C:[2]|  |
|  |                     |  |  Signal4: [ ] R:[21] C:[2]|  |
|  +---------------------+  +--------------------------+   |
|  +---------------------+  +--------------------------+   |
|  |  MSO CHANNEL        |  |  ACTIONS                 |   |
|  |  CH1: [x] Pos:[_] V/div:[_] |  [ Set Label ]      |   |
|  |  CH2: [ ] Pos:[_] V/div:[_] |  [ Set MSO  ]       |   |
|  |  CH3: [ ] Pos:[_] V/div:[_] |  [ Save Pic ]       |   |
|  |  CH4: [ ] Pos:[_] V/div:[_] |  [ Save Data ]      |   |
|  |                     |  [ Save Pic+Data ]           |   |
|  |                     |  +--------------------+      |   |
|  |                     |  |Save: [x]Local [x]Excel|  |   |
|  |                     |  |      [ ]Scope          |  |   |
|  |                     |  |  [x] Free Save    |  |   |
|  |                     |  +--------------------+      |   |
|  +---------------------+  +--------------------------+   |
|  +--------------------------------------------------+   |
|  |  < Last    Jump:[___] ^v    Next >               |   |
|  +--------------------------------------------------+   |
|  +--------------------------------------------------+   |
|  |  [Log Output Area]                               |   |
|  +--------------------------------------------------+   |
+----------------------------------------------------------+
|  Status Bar                                    Theme     |
+----------------------------------------------------------+
```

### 界面元素说明

| 编号 | 区域 | 说明 |
|------|------|------|
| (1) | 菜单栏 | File（保存/重新加载/导入导出配置）、Settings（各项参数配置）、主题切换 |
| (2) | 工具栏 | 快捷按钮：保存Excel、连接、重连、重新加载Excel |
| (3) | 连接指示灯 | 绿色=已连接，灰色=未连接 |
| (4) | File Paths 卡片 | Excel 文件路径、截图保存路径 |
| (5) | Settings 卡片 | 工作表选择、测试类型、起始行、信号行列配置 |
| (6) | MSO Channel 卡片 | 4通道使能、垂直位置、电压档位 |
| (7) | Actions 卡片 | 操作按钮：设置标签、一键配置示波器、保存截图/数据 |
| (8) | 导航栏 | 上一项 / 下一项 / 跳转到指定行 |
| (9) | 日志区 | 实时显示操作日志和错误信息 |
| (10) | 状态栏 | 当前状态信息 + 深浅主题切换按钮 |

---

## 4. 操作流程

### 4.1 典型工作流程

```
[连接示波器] -> [加载Excel] -> [选择工作表] -> [配置参数] -> [逐项测试]
```

### 4.2 分步操作

#### 步骤 1：连接示波器

1. 点击工具栏 **连接** 按钮
2. 在弹窗中选择连接方式：

   | 方式 | 说明 | 适用场景 |
   |------|------|----------|
   | **GPIB / USB（自动检测）** | 自动扫描所有 VISA 资源 | 使用 GPIB 线缆或 USB 直连 |
   | **Ethernet / IP（手动）** | 输入 IP 地址和端口 | 通过网络远程连接 |

3. 如果选择 IP 连接，输入示波器的 IP 地址和端口号（默认 4000）
4. 点击 **OK**，等待连接建立
5. 成功后在工具栏右上角看到 **绿色圆点** 和 IP 信息

#### 步骤 2：加载 Excel 测试报告

1. 在 **File Paths** 卡片中，点击 Excel 行右侧的 **浏览** 按钮
2. 选择项目的 Excel 测试报告文件（`.xlsx` 格式）
3. 同样点击 Pic 行的 **浏览**，选择截图保存文件夹

#### 步骤 3：选择工作表和配置

1. 在 **Settings** 卡片中，从 **Sheet** 下拉列表选择当前要测试的工作表
2. 选择 **Type** 测试类型：

   | 类型 | 用途 | 测量项 |
   |------|------|--------|
   | **Sequence** | 时序测量 | CH1到CH2 上升沿延时（90%/10%） |
   | **Monotony** | 单调性测量 | 每通道 TOP/BASE/MAX/MIN（支持 P/N 翻转） |

3. 设置 **Init R** 起始行号（测试数据从该行开始）
4. 勾选需要测试的信号通道，设置每通道的 Excel 行号（R:）和列号（C:）

#### 步骤 4：配置示波器参数

1. 在 **MSO Channel** 卡片中勾选需要启用的通道（CH1–CH4）
2. 设置每通道的垂直位置（Pos）和电压灵敏度（V/div）
3. 通过菜单 **Settings → MSO Horizontal** 设置水平时基、触发通道/边沿/电平
4. 通过菜单 **Settings → Set Label Position** 设置通道标签位置
5. 通过菜单 **Settings → Delay Config** 设置 DELAY 测量参数（Sequence 模式）
6. 通过菜单 **Settings → Rise/Fall Time Config** 设置 Rise/Fall Time 参数（Monotony 模式）

#### 步骤 5：执行测试

1. 点击 **Set MSO** 按钮一键配置示波器（自动设置测量项、通道、触发等）
2. 点击 **Set Label** 设置通道标签
3. 根据需要点击操作按钮：

   | 按钮 | 功能 |
   |------|------|
   | **Save Pic** | 仅保存截图（可选：存本地/插入Excel/存示波器） |
   | **Save Data** | 仅保存测量数据到 Excel |
   | **Save Pic+Data** | 同时保存截图和数据 |

4. 使用 **Last** / **Next** 导航到上一个/下一个测试项
5. 或使用 Jump 输入框直接跳转到指定行号

---

## 5. 功能详解

### 5.1 连接管理

程序支持以下示波器型号，连接后自动识别：

| 系列 | 型号举例 | 识别方式 |
|------|----------|----------|
| MSO4/5/6 | MSO44, MSO54, MSO64 | 查询 `*IDN?` 返回含 "MSO" |
| DPO7000 | DPO7104C, DPO7254C | 查询 `*IDN?` 返回含 "DPO7000" |
| DPO5000 | DPO5104B | 查询 `*IDN?` 返回含 "DPO5000" |

**断线重连**：程序每 5 秒自动检测连接状态。连续 2 次检测失败后弹出断线提示，点击 **重连** 即可恢复。

### 5.2 测试类型详解

#### Sequence（时序测量）

测量两通道间信号的时序关系：
- CH1 TOP/BASE（90%/10% 参考电平）
- CH2 TOP/BASE
- CH1到CH2 RISE-RISE 延时
- CH1/CH2 MAX/MIN

#### Monotony（单调性测量）

每个启用的通道测量 4 个参数：
- TOP（顶端值）
- BASE（底端值）
- MAX（最大值）
- MIN（最小值）

支持 P/N 方向翻转：同一行数据在 P（上升沿触发）和 N（下降沿触发）之间切换。

### 5.3 导航系统

| 操作 | Sequence 行为 | Monotony 行为 |
|------|--------------|---------------|
| **Next** | 行号 +1 | P到N（同行翻转）到 行号 +1 到 P |
| **Last** | 行号 -1 | N到P（同行翻转）到 行号 -1 到 N |
| **Jump** | 直接跳到指定行 | 跳到指定行，方向置为 P |

> 键盘快捷操作：在 Jump 输入框按 **上/下** 方向键可微调行号（+1/-1）。

### 5.4 保存选项

截图和数据可以分别选择保存目标：

| 选项 | 说明 |
|------|------|
| **Local** | 保存截图到本地文件夹（Pic 路径） |
| **Excel** | 将截图插入 Excel 指定列，数据写入指定列 |
| **Scope** | 将截图保存到示波器内部存储 |

> Excel 列号配置：通过菜单 **Settings → Set Data Columns** 和 **Settings → Set Picture Columns** 分别设置数据和图片的写入列。

#### 5.4.1 自由保存图片模式（按通道标签命名截图）

勾选 Actions 卡片中的 **Free Save** 复选框后：

| 自动行为 | 说明 |
|----------|------|
| Save to Excel | 自动关闭 |
| Save to Scope | 自动关闭 |
| Save to Local | 强制打开 |
| Save Data 按钮 | 禁用 |
| Save Pic+Data 按钮 | 禁用 |

**截图命名规则**：

| 测试类型 | 命名格式 | 示例 |
|----------|----------|------|
| Sequence / CH 标签模式 | `标签1 TO 标签2.PNG` | `VCCIN TO VCCIO.PNG` |
| 仅单个 CH 启用 | `标签.PNG` | `VCCIN.PNG` |
| Monotony P 方向 | `标签_R.PNG` | `VCCIN_R.PNG` |
| Monotony N 方向 | `标签_F.PNG` | `VCCIN_F.PNG` |

**保存路径**：直接保存在 Pic 路径下，不含 Sheet 子目录。

> 此模式不需要加载 Excel 文件，适用于仅需截图、不需要写入 Excel 的场景。

### 5.5 配置导入/导出

- **File → Export Config**：将当前所有设置（通道、行列、示波器参数等）导出为 JSON 文件
- **File → Import Config**：从 JSON 文件恢复设置

适用于：多项目切换、配置备份、团队共享。

> MSO 示波器设置（Horizontal、Channel Setup、Label Position、触发）按测试类型保存，不区分 Sheet。

#### 5.5.1 Rise Time / Fall Time（Monotony 专属）

Monotony 模式下可通过 Settings → Set Data Columns 单独启用：

| 参数 | 位置 | 默认列 | 默认状态 |
|------|------|--------|----------|
| Rise Time | Monotony P 区域 | A | 不启用 |
| Fall Time | Monotony N 区域 | B | 不启用 |

启用后 P 方向自动保存 Rise Time，N 方向自动保存 Fall Time。测量值取自示波器 MEAN（平均值）。

#### 5.5.2 配置管理

关闭时自动保存全部配置到 config.json，启动时自动恢复。同时生成 config_default.json 在 exe 同级目录，复制到其他机器可自动导入。

### 5.6 主题切换

点击状态栏右侧的 **太阳/月亮** 按钮切换 Light/Dark 主题，或通过 **Settings 菜单** 选择。

### 5.7 日志系统

- 所有操作实时显示在底部日志区域
- 日志自动保存到 `logs/` 文件夹（`log_YYYYMMDD_HHMMSS.txt`）
- 自动保留最近 20 个日志文件，超出自动删除

---

## 6. 配置参考

### 6.1 MSO Horizontal（水平时基）

| 参数 | 范围 | 说明 |
|------|------|------|
| Mode | AUTO / MANUAL | 水平扫描模式 |
| Scale | 1 – 99999 | 时基刻度，可选择 ns/μs/ms/s 单位 |
| Position | 0 – 100 % | 水平位置百分比 |
| Trig Channel | CH1 / CH2 / CH3 / CH4 | 触发信号源 |
| Trig Edge | RISE / FALL / BOTH | 触发边沿类型 |
| Trig Level | 1 – 99999 | 触发电平，可选择 mV/V 单位 |

### 6.2 MSO Channel Setup（通道设置）

| 参数 | 范围 | 说明 |
|------|------|------|
| Position | -20.0 – 20.0 div | 垂直位置 |
| Scale | 0.001 – 100.0 V/div | 电压灵敏度 |

### 6.3 Label Position（标签位置）

| 参数 | 范围 | 说明 |
|------|------|------|
| X | 0 – 999 | 标签水平位置 |
| Y | 0 – 9999 | 标签垂直位置 |

### 6.4 Excel 列配置

所有列号范围为 1–99，对应 Excel 的 A–CU 列。

### 6.5 DELAY 测量参数（Sequence）

| 参数 | 范围 | 说明 |
|------|------|------|
| Source 1 | CH1–CH4 | 测量源通道 1 |
| Source 2 | CH1–CH4 | 测量源通道 2 |
| Edge 1 | RISE / FALL | 源 1 触发边沿 |
| Edge 2 | RISE / FALL | 源 2 触发边沿 |
| Ref High | 1–99 % | 参考电平高值 |
| Ref Low | 1–99 % | 参考电平低值 |

### 6.6 Rise/Fall Time 测量参数（Monotony）

| 参数 | 范围 | 说明 |
|------|------|------|
| Rise Source | CH1–CH4 | Rise Time 测量源通道 |
| Rise Ref High | 1–99 % | Rise 参考电平高值 |
| Rise Ref Low | 1–99 % | Rise 参考电平低值 |
| Fall Source | CH1–CH4 | Fall Time 测量源通道 |
| Fall Ref High | 1–99 % | Fall 参考电平高值 |
| Fall Ref Low | 1–99 % | Fall 参考电平低值 |

---

## 7. 常见问题

### 连接不到示波器

**GPIB/USB 模式**：
1. 确认 NI-VISA 驱动已安装并重启
2. 检查线缆物理连接是否牢固
3. 检查示波器是否已开机
4. 打开 NI MAX（Measurement & Automation Explorer）确认设备可见

**IP 模式**：
1. 确认电脑和示波器在同一网络
2. 用 `ping <示波器IP>` 测试网络连通性
3. 确认防火墙未阻止端口（默认 4000）
4. 如直连失败，勾选 "Use Socket" 尝试 Socket 模式

### Excel 进程残留

如果程序关闭后任务管理器仍有 EXCEL.EXE 运行：
1. 打开任务管理器（Ctrl+Shift+Esc）
2. 找到 EXCEL.EXE 进程
3. 右键 → 结束任务

程序已经做了 COM 对象释放处理，此问题通常只在异常退出时出现。

### 打包后运行闪退

1. 确认目标设备已安装 NI-VISA 驱动
2. 检查 `logs/` 文件夹查看错误日志
3. 确认不是杀毒软件拦截（PyInstaller 打包可能被误报）

### 截图未插入 Excel

1. 确认 Excel 文件已打开且工作表正确
2. 确认 Save 选项中的 "Excel" 已勾选
3. 检查 Picture Columns 设置中的列号是否正确
4. 确认该列未被合并单元格阻挡

### 工作表格式要求

Excel 测试报告建议格式：
- 信号名称所在列按 Settings 中配置的 C: 列号
- 每行一个测试项，行号从 Init R 开始
- Monotony 模式需要 P/N 两个方向的独立数据列

---

> 技术支持：liujch2
>
> 版本：V2.2.0 | 2026年7月
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Help Dialog
# ═══════════════════════════════════════════════════════════════════════════════

class HelpDialog(QDialog):
    """Resizable dialog with sidebar chapter tree and HTML content viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户操作手册 — EE Power On AutoTool V2.2")
        self.setMinimumSize(900, 640)
        self.resize(960, 700)

        # ── Load and parse manual ──────────────────────────────────────────
        self._md_text = self._load_manual()
        # Strip the document title block (H1 + subtitle + author + first HR)
        # — the Windows title bar already identifies the manual
        md_text = self._strip_title_block(self._md_text)
        self._html = md_to_html(md_text)
        self._chapters = extract_chapters(md_text)

        self._setup_ui()

    # ── Title block stripping ────────────────────────────────────────────
    @staticmethod
    def _strip_title_block(text: str) -> str:
        """Remove the document title block (H1 + metadata lines up to first HR).

        The Windows title bar already shows "用户操作手册 — EE Power On
        AutoTool V2.2", so the H1 heading, subtitle, and author lines in
        the markdown are redundant and would waste vertical space.
        """
        lines = text.split('\n')
        # Find the first heading (`# `) and the first `---` after it
        h1_idx = None
        hr_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if h1_idx is None and stripped.startswith('# ') and not stripped.startswith('## '):
                h1_idx = i
            if h1_idx is not None and stripped == '---':
                hr_idx = i
                break
        if h1_idx is not None and hr_idx is not None and hr_idx > h1_idx:
            # Remove from h1_idx through hr_idx (inclusive), plus any blank
            # lines immediately after the HR
            end = hr_idx + 1
            while end < len(lines) and lines[end].strip() == '':
                end += 1
            return '\n'.join(lines[:h1_idx] + lines[end:])
        return text

    # ── File loading ───────────────────────────────────────────────────────
    def _load_manual(self) -> str:
        """Return the embedded manual (bundled in the code, no file needed)."""
        return _EMBEDDED_MANUAL

    # ── UI ─────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Splitter: sidebar + content ───────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # -- Sidebar --
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(4, 6, 4, 4)
        sidebar_layout.setSpacing(4)

        # -- Save button --
        save_btn = QPushButton("💾 另存为…")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F7;
                border: 1px solid #E5E5E7;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                color: #1D1D1F;
            }
            QPushButton:hover {
                background: #EBEBED;
                border-color: #D1D1D6;
            }
        """)
        save_btn.clicked.connect(self._save_as)
        sidebar_layout.addWidget(save_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(18)
        self.tree.setRootIsDecorated(True)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # suppress focus rect on click
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background: #FAFAFA;
                font-size: 13px;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 5px 8px;
                border-radius: 4px;
                color: #1D1D1F;
            }
            QTreeWidget::item:hover {
                background-color: rgba(0, 122, 255, 0.08);
            }
            QTreeWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
            QTreeWidget::item:has-children {
                font-weight: 600;
            }
            QTreeWidget::item:focus {
                outline: none;
                border: none;
            }
        """)

        # Populate tree
        for ch in self._chapters:
            parent = QTreeWidgetItem(self.tree, [ch['title']])
            parent.setData(0, Qt.UserRole, ch['anchor'])
            parent.setExpanded(True)
            for sub in ch['children']:
                child = QTreeWidgetItem(parent, [sub['title']])
                child.setData(0, Qt.UserRole, sub['anchor'])

        self.tree.itemClicked.connect(self._on_chapter_clicked)
        sidebar_layout.addWidget(self.tree)
        sidebar_widget.setMinimumWidth(180)
        sidebar_widget.setMaximumWidth(260)
        splitter.addWidget(sidebar_widget)

        # -- Content --
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: white;
                padding: 20px 32px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        self.browser.setHtml(self._html_with_style())
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 720])

        layout.addWidget(splitter)

    def _html_with_style(self, body_html: str | None = None) -> str:
        if body_html is None:
            body_html = self._html
        css = """
        <style>
            body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; color: #1D1D1F; line-height: 1.8; }
            h1 { font-size: 22px; margin-top: 0; padding-bottom: 8px; border-bottom: 2px solid #E5E5E7; }
            h2 { font-size: 18px; margin-top: 28px; padding-bottom: 4px; border-bottom: 1px solid #E5E5E7; }
            h3 { font-size: 15px; margin-top: 20px; color: #333; }
            table { border-collapse: collapse; width: 100%; margin: 12px 0; }
            table th { background: #F5F5F7; text-align: left; padding: 6px 10px; font-weight: 600; }
            table td { padding: 6px 10px; border-bottom: 1px solid #E5E5E7; }
            code { background: #F0F0F4; padding: 1px 5px; border-radius: 3px; font-size: 13px; }
            pre { background: #F5F5F7; padding: 12px 16px; border-radius: 6px; overflow-x: auto; }
            pre code { background: none; padding: 0; }
            a { color: #007AFF; text-decoration: none; }
            hr { border: none; border-top: 1px solid #E5E5E7; margin: 24px 0; }
            ul.checklist { list-style: none; padding-left: 0; }
            li.checklist { padding: 2px 0; }
            b { color: #1D1D1F; }
            img { max-width: 100%; }
        </style>
        """
        return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{body_html}</body></html>"

    def _on_chapter_clicked(self, item, column):
        anchor = item.data(0, Qt.UserRole)
        if anchor:
            self.browser.scrollToAnchor(anchor)

    # ── Save As ──────────────────────────────────────────────────────────
    def _save_as(self):
        """Export the manual as a standalone HTML or Markdown file."""
        path, fmt = QFileDialog.getSaveFileName(
            self,
            "另存为用户操作手册",
            "用户操作手册.html",
            "HTML 文件 (*.html);;Markdown 文件 (*.md)",
        )
        if not path:
            return  # user cancelled

        try:
            if path.lower().endswith('.md'):
                # Save original markdown
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self._md_text)
            else:
                # Render full markdown (with title block) as styled HTML
                full_html = md_to_html(self._md_text)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self._html_with_style(full_html))
        except OSError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "保存失败", f"无法写入文件：\n{e}")
