"""Implements root widget of the single_word screen."""

from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout


class SingleWordRoot(FloatLayout):
    """Root widget of the single_word screen."""

    scroll_view = ObjectProperty()
    template = ObjectProperty()

    def on_template(self, *_):
        """Update :attr:`scroll_view` if self.template changes."""
        self.scroll_view.clear_widgets()
        self.scroll_view.add_widget(self.template)
