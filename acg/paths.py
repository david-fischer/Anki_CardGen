"""This module defines constants for the different paths used in the application."""

import os

MAIN_DIR = os.path.abspath(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(MAIN_DIR, "assets")
ANKI_DIR = os.path.join(MAIN_DIR, "anki-templates")
SCREEN_DIR = os.path.join(MAIN_DIR, "screens")
CUSTOM_WIDGET_DIR = os.path.join(MAIN_DIR, "custom_widgets")
