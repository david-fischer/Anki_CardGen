# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from kivymd import hooks_path as kivymd_hooks_path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

sys.setrecursionlimit(5000)

kivymd_hidden_imports = ["kivymd.vendor.circularTimePicker"]
spacy_hidden_imports = collect_submodules("spacy") + [
    "spacy.kb",
    "spacy.lexeme",
    "spacy.matcher._schemas",
    "spacy.morphology",
    "spacy.parts_of_speech",
    "spacy.syntax._beam_utils",
    "spacy.syntax._parser_model",
    "spacy.syntax.arc_eager",
    "spacy.syntax.ner",
    "spacy.syntax.nn_parser",
    "spacy.syntax.stateclass",
    "spacy.syntax.transition_system",
    "spacy.tokens._retokenize",
    "spacy.tokens.morphanalysis",
    "spacy.tokens.underscore",
    "spacy.cli",
    "blis",
    "blis.py",
    "cymem",
    "cymem.cymem",
    "murmurhash",
    "preshed.maps",
    "srsly.msgpack.util",
    "thinc.extra.search",
    "thinc.linalg",
    "thinc.neural._aligned_alloc",
    "thinc.neural._custom_kernels",
]
# from kivy_deps import sdl2, glew

datas = [("pyproject.toml", ".")]
for module in ["thinc", "spacy.lang", "spacy.lookups", "pt_core_news_sm"]:
    datas.extend(collect_data_files(module, include_py_files=True))

path = os.path.abspath(".")

a = Analysis(
    ["main.py"],
    pathex=[path],
    datas=datas,
    hiddenimports=[
        "pony.orm.dbproviders.sqlite",
        "templates",
        "lxml",
        "soupsieve",
        "kivy.uix.recycleview",
    ]
    + kivymd_hidden_imports
    + spacy_hidden_imports,
    hookspath=[kivymd_hooks_path],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# trees = [
#     Tree(folder, prefix=folder)
#     for folder in ["screens", "custom_widgets", "assets", "anki-templates"]
# ]

exe = EXE(
    pyz,
    a.scripts,
    [],
    # Tree("acg"),  #    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    exclude_binaries=True,
    bootloader_ignore_signals=False,
    debug=False,
    strip=False,
    upx=True,
    name="AnkiCardGen",
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree("acg", prefix="acg"),
    # Tree("acg"),
    #    *trees,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AnkiCardGen",
)
