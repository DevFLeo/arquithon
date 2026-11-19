# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# O ícone do .exe é gerado na hora a partir do desenho em ui/icon.py.
sys.path.insert(0, SPECPATH)
from ui.icon import write_ico

os.makedirs(os.path.join(SPECPATH, 'build'), exist_ok=True)
ICON_PATH = os.path.join(SPECPATH, 'build', 'arquithon.ico')
write_ico(ICON_PATH)

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Arquithon-2.1v',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)
