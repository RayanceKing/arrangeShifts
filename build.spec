# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['arrangeShiftsGUI.py'],  # 你的主程序文件名
    pathex=[],
    binaries=[],
    datas=[
        # 添加资源文件（如图标、样式表）
        ('assets/*.ico', 'assets'),
        ('assets/*.icns', 'assets'),
    ],
    hiddenimports=[
        'pandas', 
        'numpy',      # pandas 依赖
        'openpyxl',   # Excel 处理
        'PyQt5.sip'   # PyQt5 必须
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScheduleApp',  # 程序名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # 使用UPX压缩
    runtime_tmpdir=None,
    console=False,      # 不显示控制台窗口
    icon='assets/app.ico',     # Windows 下使用的图标（ico格式）
)

import sys
if sys.platform == "darwin":
    # macOS 平台下，使用 BUNDLE 生成 .app 应用程序包
    app = BUNDLE(
        exe,
        name="ScheduleApp.app",
        icon='assets/app.icns',  # macOS 下使用的图标（icns格式）
        bundle_identifier="com.example.scheduleapp",
        info_plist={
            "CFBundleDisplayName": "ScheduleApp",
            "CFBundleName": "ScheduleApp",
            "CFBundleExecutable": "ScheduleApp",
            "CFBundleIdentifier": "com.example.scheduleapp",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            # 如果希望应用在启动后不显示 Dock 图标，可设置为 True
            "LSUIElement": False
        }
    )
