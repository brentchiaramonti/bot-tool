# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['botbotgui.py'],
             pathex=['C:\\Users\\bchiaramonti\\Desktop\\bot-tool\\officite-migration-script-master\\botbot'],
             binaries=[],
             datas=[('C:\\Users\\bchiaramonti\\.virtualenvs\\botbot-j3e8Wcol\\Lib\\site-packages\\wordninja\\wordninja_words.txt.gz', 'wordninja'),
		    ('.\\settings.py','.'),
		    ('C:\\Users\\bchiaramonti\\.virtualenvs\\botbot-j3e8Wcol\\Lib\\site-packages\\tldextract\\', 'tldextract')],
             hiddenimports=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='B.O.T. Bot Plus',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon='.\\images\\main_icon_plus.ico' )
