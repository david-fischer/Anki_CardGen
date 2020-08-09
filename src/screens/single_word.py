"""Implements root widget of the single_word screen."""
import pydoc

from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp

from db import get_template


class SingleWordMain(FloatLayout):
    """Root widget of the single_word screen."""

    scroll_view = ObjectProperty()

    def __init__(self, **kwargs):
        super(SingleWordMain, self).__init__(**kwargs)
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *_):
        app = MDApp.get_running_app()
        current_template = app.current_template
        template_cls_name = get_template(current_template).cls_name
        template_cls = pydoc.locate(template_cls_name)
        template = template_cls()
        template.add_field_widgets()
        self.scroll_view.add_widget(template)
