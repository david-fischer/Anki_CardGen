"""
Implementation of :class:`Template` class and sub-classes.

To add a new template, inherit from Template or a subclass and define the :attr:`parsers` and :attr:`fields` attributes.
See e.g. the definition of :class:`PtTemplate`.
"""
from functools import partial
from pprint import pprint
from typing import Dict, List

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from pony.orm import db_session

from custom_widgets.scroll_widgets import ScrollBox
from custom_widgets.selection_widgets import ImageCarousel
from db import get_template, new_template
from fields import (
    CheckChipOptionsField,
    DualLongTextField,
    Field,
    ImgField,
    MediaField,
    TextInputField,
    TransChipOptionsField,
    translator,
)
from parsers import (
    DicioParser,
    GoogleImagesParser,
    LingueeParser,
    Parser,
    ReversoParser,
)
from utils import smart_dict_merge


class Template(BoxLayout):
    """Main class handling the data for the card-generation, database-access and user-selection."""

    fields: List[Field] = None
    """Each field can have individual pre- and post-process functions and an optional widget so the user can make a
    selection between multiple options."""
    parsers: Dict[str, Parser] = None
    """Each parser fetches data as a dict. The union of all these dicts will be collected in :attr:`data`."""
    data: Dict = None
    """: : Base data to generate card from. Dict of the form ``{"key": ["list","of","options"]}`` or
    ``{"key":"single_value"}``."""
    content: Dict = None
    """: : Dict of the form ``{"field_on_anki_card": "content"}``."""
    search_term: str = None
    # TODO: is this necessary?
    name: str = None
    """Name of the template as saved in database."""
    sort_field: str = None
    """The field that should be unique on all cards. For language cards e.g. the word to learn."""

    def __init__(self, **kwargs):
        super(Template, self).__init__(**kwargs)
        self.parsers = self.parsers or {}
        self.fields = self.fields or []

    def template_db(self):
        """If existent, get entry in the database by name, else create new one."""
        return get_template(self.name) or new_template(self)

    def current_card_db(self):
        """If existent get card by name, else create new one."""
        t_db = self.template_db()
        return t_db.get_card(self.search_term) or t_db.add_card(self)

    def set_data_from_parsers(self):
        """Collect all data obtained by the :class:`parsers.parser` in :attr:`data`."""
        self.data = {self.sort_field: self.search_term}
        for parser in self.parsers.values():
            parser_res_dict = parser.result_dict(self.search_term)
            self.data = smart_dict_merge(self.data, parser_res_dict)

    def update_fields(self):
        """Update all fields."""
        for field in self.fields:
            field.update()

    def add_field_widgets(self):
        """For all :class:`fields.Field` with a widget, add it to the :class:`Template` itself."""
        for field in self.fields:
            if field.widget:
                self.add_widget(field.widget)

    def get_content_from_fields(self):
        r"""
        Iterate through :class:`fields.Field`\ s in :attr:`fields` to obtain the processed data and user selection.

        Return result as merged dict from all :class:`fields.Field`\\ s.
        """
        res_dict = {}
        for field in self.fields:
            field_content = field.get_content()
            res_dict = smart_dict_merge(res_dict, field_content)
        self.content = res_dict

    def post_process(self):
        """Placeholder-function."""

    @db_session
    def add_content_to_db(self):
        """Write content to card."""
        self.current_card_db().fields = self.content

    def get_results(self):
        """Get final results for the card fields as dictionary."""
        self.get_content_from_fields()
        self.post_process()
        self.add_content_to_db()
        pprint(self.content)
        return self.content

    def search(self, search_term):
        """
        Look up card with name ``search_term`` in data-base.

        Try to load data from card, if not possible use :meth:`set_data_from_parsers` to fetch data and save it to
        data-base.
        """
        self.search_term = search_term
        with db_session:
            template_db = get_template(self.name)
            current_card = template_db.get_card(search_term) or template_db.add_card(
                search_term
            )
            if current_card.base_data:
                self.data = current_card.base_data
                try:
                    self.update_fields()
                except ValueError:
                    print("Could not load previously saved data. Request data anew...")
                    self.set_data_from_parsers()
                    current_card.base_data = self.data
            else:
                self.set_data_from_parsers()
                current_card.base_data = self.data


class PtTemplate(Template):
    """Template to generate vocabulary cards for brazilian portuguese."""

    name = "Portuguese Vocab"
    sort_field = "word"
    from_lang: str = "pt"
    to_lang: str = "de"

    def __init__(self, **kwargs):
        super(PtTemplate, self).__init__(**kwargs)
        parser_attrs = {
            "from_lang": self.from_lang,
            "to_lang": self.to_lang,
        }
        self.parsers = {
            "linguee": LingueeParser(**parser_attrs),
            "dicio": DicioParser(**parser_attrs),
            "reverso": ReversoParser(**parser_attrs),
            "image": GoogleImagesParser(**parser_attrs),
        }
        self.fields = [
            TextInputField(field_name="word", callback=self.search, template=self),
            TextInputField(
                field_name="image_search_keywords",
                callback=partial(self.update_from_single_parser, parser_key="image"),
                template=self,
            ),
            ImgField(field_name="image", file_type="jpg", template=self),
            CheckChipOptionsField(field_name="translation", template=self),
            TransChipOptionsField(
                src_field="synonym", target_field="synonym_trans", template=self,
            ),
            TransChipOptionsField(
                src_field="antonym", target_field="antonym_trans", template=self,
            ),
            DualLongTextField(
                src_field="explanation",
                target_field="explanation_trans",
                template=self,
            ),
            DualLongTextField(
                src_field="example", target_field="example_trans", template=self
            ),
            MediaField(field_name="audio", file_type="mp3", template=self),
            Field(field_name="additional_info", template=self),
            Field(field_name="conjugation_table", template=self),
        ]
        self.add_field_widgets()

    def update_from_single_parser(self, search_term, parser_key):
        """Use only a single parser to update :attr`data`."""
        result_dict = self.parsers[parser_key].result_dict(search_term)
        self.data.update(result_dict)
        self.update_fields()

    def translate(self, string):
        """Translate string from :attr:`from_lang` to :attr:`to_lang`."""
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text


Builder.load_string(
    """
<Template>:
    orientation: "vertical"
    size_hint:1,None
    height: self.minimum_height
    padding: 10
    spacing: 10
"""
)

# pylint: disable = W,C,R,I
if __name__ == "__main__":
    from kivymd.app import MDApp

    Factory.register("ImageCarousel", ImageCarousel)
    Factory.register("ScrollBox", ScrollBox)

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            template = Builder.load_string(
                """#
PtTemplate:
    MDFlatButton:
        text: "Get Results"
        on_press: app.root.get_results()"""
            )
            # print(template.fields)
            template.add_field_widgets()
            return template

    _TestApp().run()
