"""Implements root widget of the single_word screen."""

from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from utils import set_screen


class SingleWordRoot(FloatLayout):
    """Root widget of the single_word screen."""

    scroll_view = ObjectProperty()
    template = ObjectProperty()

    def on_template(self, *_):
        """Update :attr:`scroll_view` if self.template changes."""
        self.scroll_view.clear_widgets()
        if self.template.parent:
            self.template.parent.remove_widget(self.template)
        self.scroll_view.add_widget(self.template)

    @staticmethod
    def back_to_queue(*_):
        """Set screen to ``"queue"``."""
        set_screen("queue")

    def proceed(self, *_):
        """Accept data and set screen to ``"queue"``."""
        self.template.get_results()
        set_screen("queue")

    def refresh(self, *_):
        """Crawl data and update database."""
        self.template.set_data_from_parsers()
        self.template.update_fields()
        self.template.save_base_data_to_db()
