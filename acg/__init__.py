import os
import pathlib
import sys
from importlib import metadata

import toml
import toolz
from appdirs import AppDirs
from kivy.factory import Factory

try:
    META = dict(metadata.metadata(__name__))
    __author__ = META["Author"]
    __version__ = META["Version"]
except metadata.PackageNotFoundError:
    pyproject_toml_path = toolz.first(
        pathlib.Path(__file__).parent.parent.glob("**/pyproject.toml")
    )
    with open(pyproject_toml_path) as file:
        pyproject_toml = toml.load(file)
    __author__ = pyproject_toml["tool"]["poetry"]["authors"][0]
    __version__ = pyproject_toml["tool"]["poetry"]["version"]


dirs = AppDirs(appname=__name__, appauthor=__author__, version=__version__)

sys.path.append(os.path.dirname(__file__))

CONFIG_DIR = pathlib.Path(dirs.user_config_dir)
CONFIG_PATH = CONFIG_DIR / "config.ini"
APP_DIR = pathlib.Path(dirs.user_data_dir)
HOME = pathlib.Path.home()
USER = HOME.stem
BASE_PATH = pathlib.Path(__file__).parent.absolute()
ASSETS_DIR = BASE_PATH / "assets"
ANKI_DIR = BASE_PATH / "anki-templates"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(APP_DIR, exist_ok=True)
