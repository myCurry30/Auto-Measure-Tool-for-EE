# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for EE Power On AutoTool V2.2.2

Build command:
    pyinstaller installer/EE_Power_On_AutoTool.spec --clean --noconfirm

Output:
    dist/EE_Power_On_AutoTool.exe  (single-file executable)
"""

import os
import sys
from pathlib import Path

# ── Project root (SPECPATH = installer/ dir, so parent is project root) ──
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPECPATH))

# ── Collect all project .py modules to include ──
def collect_project_modules():
    """Walk project dirs and collect .py files as (src, dest_dir) tuples."""
    src_dirs = ['app', 'core', 'dialogs', 'widgets', 'tools', 'debug']
    modules = []
    for d in src_dirs:
        full = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(full):
            for root, _, files in os.walk(full):
                for f in files:
                    if f.endswith('.py'):
                        src = os.path.join(root, f)
                        rel = os.path.relpath(root, PROJECT_ROOT)
                        modules.append((src, rel))
    return modules

# ── Data files to bundle ──
datas = [
    # Icons / images
    (os.path.join(PROJECT_ROOT, 'resources', 'app_icon.ico'), 'resources'),
    (os.path.join(PROJECT_ROOT, 'resources', 'NC.ico'), 'resources'),
    (os.path.join(PROJECT_ROOT, 'resources', 'NC logo.png'), 'resources'),
    # Qt Designer UI files
    (os.path.join(PROJECT_ROOT, 'layout.ui'), '.'),
    (os.path.join(PROJECT_ROOT, 'layout_new.ui'), '.'),
    # No runtime config bundled — starts with defaults, auto-generates on first close
]

# ── Hidden imports that PyInstaller may miss ──
hiddenimports = [
    # PySide6 / Qt
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtUiTools',
    # PyVISA backends
    'pyvisa',
    'pyvisa_py',
    'pyvisa_py.tcpip',
    'pyvisa_py.usb',
    'pyvisa_py.gpib',
    'pyvisa_py.serial',
    # win32com (Excel COM automation)
    'win32com',
    'win32com.client',
    'pythoncom',
    # misc
    'json',
    're',
    'abc',
]

# ── Exclude bloated packages we don't need ──
excludes = [
    'tkinter',
    'unittest',
    'xmlrpc',
    'pydoc',
    'test',
    'setuptools',
    'distutils',
]

block_cipher = None

# ── Analysis ────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas + collect_project_modules(),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── Filter duplicate PySide6 DLLs to reduce size ──
# PySide6 often ships redundant copies; keep only what's needed.
import re as _re
_dll_filter = _re.compile(
    r'.*[\\/](opengl32sw|d3dcompiler_47|libEGL|libGLESv2)\.dll$',
    _re.IGNORECASE
)
a.binaries = [
    (name, path, typ) for (name, path, typ) in a.binaries
    if not _dll_filter.match(path)
]

# ── PYZ ─────────────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ─────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EE_Power_On_AutoTool_V2.2.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # Windows GUI app (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'resources', 'app_icon.ico'),
    version=os.path.join(PROJECT_ROOT, 'installer', 'version_info.txt'),
)
