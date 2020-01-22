# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None
specpath = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(['dcs_wp_manager.py'],
             pathex=['C:\\Users\\mcdel\\dcs-wp-magic'],
             binaries=[],
             datas=[("icon.ico", ".")],
             hiddenimports=["flask"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='dcs_wp_manager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False, icon=os.path.join(specpath, 'icon.ico'))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='dcs_wp_manager')
