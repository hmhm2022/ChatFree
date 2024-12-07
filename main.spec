# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('linuxdo.ico', '.'),
        ('ai_api.py', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.constants',
        'keyboard',
        'win32clipboard',
        'requests',
        'winreg',
        'urllib3',
        'certifi',
        'idna',
        'charset_normalizer',
        'pywin32',
        'PIL',
        'pystray',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['*'],
    noarchive=False
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ChatFree',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='linuxdo.ico'
) 
