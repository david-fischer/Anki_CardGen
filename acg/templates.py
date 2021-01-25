"""
Implementation of :class:`Template` class and sub-classes.

To add a new template, inherit from Template or a subclass and define the :attr:`parsers` and :attr:`fields` attributes.
See e.g. the definition of :class:`PtTemplate`.
"""
from functools import partial
from pprint import pprint
from typing import Dict, List

import attr
from googletrans import Translator
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.toast import toast
from pony.orm import commit, db_session
from utils import async_get_results

from .custom_widgets.selection_widgets import SeparatorWithHeading
from .db import db
from .design_patterns.factory import CookBook
from .fields import (
    CheckChipOptionsField,
    DualLongTextField,
    Field,
    ImgField,
    MediaField,
    TextInputField,
    TransChipOptionsField,
    field_cookbook,
)
from .language_processing import tag_word_in_sentence
from .parsers import AsyncParser, NoMatchError, Parser, parser_cookbook
from .utils import app_busy, smart_dict_merge

template_cookbook = CookBook()
translator = Translator()


@attr.s(auto_attribs=True)
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
    field_cookbook: CookBook = field_cookbook
    parser_cookbook: CookBook = parser_cookbook
    parser_kwargs: dict = None
    _parser_names: list = None

    def __attrs_post_init__(self):
        self.data = self.data or {}
        self.fields = self.fields or []
        self.parser_kwargs = self.parser_kwargs or {}
        if self._parser_names:
            self._init_parsers(self._parser_names)
        super().__init__()

    def _init_parsers(self, parser_names):
        self.parsers = {}
        for parser_name in parser_names:
            self.add_parser(parser_name, **self.parser_kwargs)

    # def _init_fields(self, field_dict):
    #     self.fields = []
    #     for field_type, kwargs in field_dict.items():
    #         self.add_field(field_type, **kwargs)
    #     self.add_field_widgets()
    #
    # def add_field(self, field_type, **kwargs):
    #     field = self.field_cookbook.cook(field_type, template=self, **kwargs)
    #     self.fields.append(field)

    def add_parser(self, parser_name, **kwargs):
        """Add a parser to :attr:`parsers` by construction from parser_cookbook."""
        self.parsers[parser_name] = self.parser_cookbook.cook(parser_name, **kwargs)

    def template_db(self):
        """If existent, get entry in the database by name, else create new one."""
        return db.Template.get(name=self.name) or db.Template(name=self.name)

    def current_card_db(self):
        """If existent get card by name, else create new one."""
        t_db = self.template_db()
        return t_db.get_card(self.search_term) or t_db.add_card(self.search_term)

    def set_data_from_parsers(self):
        """Collect all data obtained by the :class:`parsers.parser` in :attr:`data`."""
        async_parsers = [
            async_parser
            for async_parser in self.parsers.values()
            if isinstance(async_parser, AsyncParser)
        ]
        self.data = async_get_results(async_parsers, self.search_term)
        self.data[self.sort_field] = self.search_term
        sync_parsers = [
            parser for parser in self.parsers.values() if isinstance(parser, Parser)
        ]
        self.data = smart_dict_merge(
            self.data, *(p.result_dict(self.search_term) for p in sync_parsers)
        )

    def update_fields(self):
        """Update all fields."""
        for field in self.fields:
            field.update()

    def add_field_widgets(self):
        """For all :class:`fields.Field` with a widget, add it to the :class:`Template` itself."""
        for field in self.fields:
            if field.widget:
                if field.heading:
                    self.add_widget(SeparatorWithHeading(heading=field.heading))
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
        commit()

    @db_session
    def save_base_data_to_db(self):
        """Save base_data to card."""
        self.current_card_db().base_data = self.data
        commit()

    @app_busy
    def get_results(self):
        """Get final results for the card fields as dictionary."""
        self.get_content_from_fields()
        self.post_process()
        self.add_content_to_db()
        pprint(self.content)
        return self.content

    def update_from_single_parser(self, search_term, parser_key):
        """Use only a single parser to update :attr`data`."""
        result_dict = self.parsers[parser_key].result_dict(search_term)
        self.data.update(result_dict)
        self.update_fields()

    @db_session
    def search(self, search_term, make_suggestion=False):
        """
        Look up card with name ``search_term`` in data-base.

        Try to load data from card, if not possible use :meth:`set_data_from_parsers` to fetch data and save it to
        data-base.
        """
        self.search_term = search_term
        template_db = db.Template.get(name=self.name)
        current_card = template_db.get_card(search_term) or template_db.add_card(
            search_term
        )
        if current_card.base_data:
            self.data = current_card.base_data
            try:
                self.update_fields()
                current_card.base_data = self.data
                return
            except ValueError:
                print("Could not load previously saved data. Request data anew...")
        try:
            self.set_data_from_parsers()
            self.update_fields()
            self.save_base_data_to_db()
        except NoMatchError:
            current_card.state = "error"
            toast(f"Could not obtain data for {search_term}.")
            if make_suggestion:
                # choose suggestion dialog here.
                pass

    @app_busy
    def manual_search(self, search_term):
        """Call :meth:`search` but with ``make_suggestion=True`` and @app_busy-decorator."""
        self.search(search_term, make_suggestion=True)


@template_cookbook.register(
    "Portuguese Vocabulary (en)",
    name="Portuguese Vocabulary (en)",
    from_lang="pt",
    to_lang="en",
)
@template_cookbook.register(
    "Portuguese Vocabulary (de)",
    name="Portuguese Vocabulary (de)",
    from_lang="pt",
    to_lang="de",
)
class VocabTemplate(Template):
    """Template to generate vocabulary cards for brazilian portuguese."""

    from_lang = None
    to_lang = None

    def __init__(self, from_lang, to_lang, **kwargs):
        self.from_lang = from_lang
        self.to_lang = to_lang

        super().__init__(
            sort_field="word",
            parser_names=[
                "async_linguee",
                "async_dicio",
                "async_reverso",
                "async_google_images",
            ],
            parser_kwargs={"from_lang": from_lang, "to_lang": to_lang},
            **kwargs,
        )
        self.fields = [
            TextInputField(
                field_name="word", callback=self.manual_search, template=self
            ),
            TextInputField(
                field_name="image_search_keywords",
                callback=partial(
                    self.update_from_single_parser, parser_key="async_google_images"
                ),
                template=self,
            ),
            ImgField(field_name="image", file_type="jpg", template=self),
            CheckChipOptionsField(
                field_name="translation", heading="Translations", template=self
            ),
            TransChipOptionsField(
                src_field="synonym",
                heading="Synonyms",
                target_field="synonym_trans",
                template=self,
            ),
            TransChipOptionsField(
                src_field="antonym",
                heading="Antonyms",
                target_field="antonym_trans",
                template=self,
            ),
            DualLongTextField(
                src_field="explanation",
                heading="Explanations",
                target_field="explanation_trans",
                template=self,
            ),
            DualLongTextField(
                src_field="example",
                heading="Examples",
                target_field="example_trans",
                template=self,
            ),
            MediaField(field_name="audio", file_type="mp3", template=self),
            Field(field_name="additional_info", template=self),
            Field(field_name="conjugation_table", template=self),
        ]
        self.add_field_widgets()

    def translate(self, string):
        """Translate string from :attr:`from_lang` to :attr:`to_lang`."""
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text

    def post_process(self):
        """Tag :attr:`search_term` in ``"explanation"`` and ``"example"`` fields."""
        for field in ["explanation", "example"]:
            self.content[field] = tag_word_in_sentence(
                self.content[field], self.search_term
            )


@template_cookbook.register(
    "English Vocabulary",
    name="English Vocabulary",
    from_lang="en",
    to_lang="de",
)
class VocabTemplateTwo(Template):
    """Template to generate vocabulary cards for brazilian portuguese."""

    from_lang = None
    to_lang = None

    def __init__(self, from_lang, to_lang, **kwargs):
        self.from_lang = from_lang
        self.to_lang = to_lang

        super().__init__(
            sort_field="word",
            parser_names=[
                "async_linguee",
                "english_parser",
                "async_reverso",
                "async_google_images",
            ],
            parser_kwargs={"from_lang": from_lang, "to_lang": to_lang},
            **kwargs,
        )
        self.fields = [
            TextInputField(
                field_name="word", callback=self.manual_search, template=self
            ),
            TextInputField(
                field_name="image_search_keywords",
                callback=partial(
                    self.update_from_single_parser, parser_key="async_google_images"
                ),
                template=self,
            ),
            ImgField(field_name="image", file_type="jpg", template=self),
            CheckChipOptionsField(
                field_name="translation", heading="Translations", template=self
            ),
            TransChipOptionsField(
                src_field="synonym",
                heading="Synonyms",
                target_field="synonym_trans",
                template=self,
            ),
            TransChipOptionsField(
                src_field="antonym",
                heading="Antonyms",
                target_field="antonym_trans",
                template=self,
            ),
            DualLongTextField(
                src_field="explanation",
                heading="Explanations",
                target_field="explanation_trans",
                template=self,
            ),
            DualLongTextField(
                src_field="example",
                heading="Examples",
                target_field="example_trans",
                template=self,
            ),
            MediaField(field_name="audio", file_type="mp3", template=self),
            Field(field_name="additional_info", template=self),
            Field(field_name="conjugation_table", template=self),
        ]
        self.add_field_widgets()

    def translate(self, string):
        """Translate string from :attr:`from_lang` to :attr:`to_lang`."""
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text

    def post_process(self):
        """Tag :attr:`search_term` in ``"explanation"`` and ``"example"`` fields."""
        for field in ["explanation", "example"]:
            self.content[field] = tag_word_in_sentence(
                self.content[field], self.search_term
            )


Builder.load_string(
    """
<Template>:
    orientation: "vertical"
    size_hint:1,None
    height: self.minimum_height
    padding: dp(10),dp(10),dp(10),dp(100)
    spacing: dp(10)
"""
)

# pylint: disable = W,C,R,I
if __name__ == "__main__":

    from kivymd.app import MDApp

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return template_cookbook.cook("Portuguese Vocabulary")

    _TestApp().run()
