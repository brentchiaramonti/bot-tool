# -*- mode: python -*-

import gooey
gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')
a = Analysis(['botbotgui.py'],
             pathex=['/Users/BSAdmin/.local/share/virtualenvs/officite-migration-script-Y8sOHYc5/bin'],
             hiddenimports=['botbot.spiders.spider'],
             hookspath=['./hooks/'],
             runtime_hooks=None,
             datas=[('./spiders/','./spiders/'), ('./settings.py','.'), ('./scrapy.cfg','.'),
                    ('./items.py','.'), ('./itemloaders.py','.'), ('./middlewares.py','.'),
                    ('./pipelines.py','.')]
             )
pyz = PYZ(a.pure)

options = [('u', None, 'OPTION'), ('u', None, 'OPTION'), ('u', None, 'OPTION')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          gooey_languages, # Add them in to collected files
          gooey_images, # Same here.
          name='BOT_Bot_GUI',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          windowed=True,
         )

app = BUNDLE(exe,
         name='BOTBotGUI.app',
         icon='/Users/BSAdmin/projects/botbot/botbot_resources/iconbuilder.icns',
         bundle_identifier=None
         )


