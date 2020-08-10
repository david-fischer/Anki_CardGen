"""Implements root widget of the single_word screen."""

from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout


class SingleWordRoot(FloatLayout):
    """Root widget of the single_word screen."""

    scroll_view = ObjectProperty()
