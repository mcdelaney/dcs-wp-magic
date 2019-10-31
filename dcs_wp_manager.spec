# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None
specpath = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(['dcs_wp_manager.py'],
             pathex=['C:\\Users\\mcdel\\dcs-wb-magic'],
             binaries=[],
             datas=[("icon.ico", ".")],
             hiddenimports=['dcs'],
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
          upx=True,
          console=False , icon=os.path.join(specpath, 'icon.ico'))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='dcs_wp_manager')
