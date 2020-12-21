"""This module defines constants for the different paths used in the application."""


import os

from kivy import platform

if platform == "android":

    from android.storage import primary_external_storage_path

MAIN_DIR = os.path.abspath(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(MAIN_DIR, "assets")
ANKI_DIR = os.path.join(MAIN_DIR, "anki-templates")
SCREEN_DIR = os.path.join(MAIN_DIR, "screens")
CUSTOM_WIDGET_DIR = os.path.join(MAIN_DIR, "custom_widgets")

ROOT_DATA_DIR = (
    primary_external_storage_path()
    if platform == "android"
    else os.path.expanduser("~")
)
