# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from glob import glob

kv_hidden_imports = [py_name[:-3].replace("/", ".") for py_name in glob("screens/*.py")]
kivymd_hidden_imports = ["kivymd.vendor.circularTimePicker"]
print(kv_hidden_imports)
#from kivy_deps import sdl2, glew

from kivymd import hooks_path as kivymd_hooks_path

path = os.path.abspath(".")

a = Analysis(
    ["main.py"],
    pathex=[path],
    hiddenimports=["pony.orm.dbproviders.sqlite", "templates"]
    + kv_hidden_imports
    + kivymd_hidden_imports,
    hookspath=[kivymd_hooks_path],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree("screens"),
    Tree("custom_widgets"),
#    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    debug=False,
    strip=False,
    upx=True,
    name="AnkiCardGen",
    console=True,
)
