# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('views/ui/*.ui', 'views/ui'),
        ('assets', 'assets'),
    ],
    hiddenimports=['PyQt6'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='SGC',
    debug=False,
    console=False,
    onefile=True,
    icon='sgc_logo.ico',
)
