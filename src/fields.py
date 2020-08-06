import re
from pprint import pprint
from typing import Any, Callable, Dict, List

import attr
import requests
from bidict import bidict
from googletrans import Translator
from pony.orm import db_session

from custom_widgets.selection_widgets import *
from db import get_template, new_template
from parsers import (
    DicioParser,
    GoogleImagesParser,
    LingueeParser,
    Parser,
    ReversoParser,
)

translator = Translator()


def route_call_to_member(cls, member, method):
    setattr(
        cls,
        method,
        lambda x, *args, **kwargs: getattr(getattr(x, member), method,)(
            *args, **kwargs
        ),
    )


def route_calls_to_member(member, calls):
    def decorator_func(cls):
        for call in calls:
            route_call_to_member(cls, member, call)
        return cls

    return decorator_func


@attr.s
class Field:
    """
    Implementation of Field.
    """

    field_name = attr.ib(default="default_field")
    widget = attr.ib(type=object, default=None)
    widget_kv = attr.ib(type=str, default=None)
    option_dict = attr.ib()
    kv_dict = attr.ib()

    @option_dict.default
    def _default_option_dict(self):
        return {self.field_name: ""}

    @kv_dict.default
    def _default_kv_dict(self):
        return bidict({self.field_name: "text"})

    def __attrs_post_init__(self):
        self.kv_dict = bidict(self.kv_dict)
        self.pre_process()
        if self.widget_kv:
            self.construct_widget()

    def pre_process(self):
        """Placeholder-function."""

    def post_process(self, content):
        """Placeholder-function."""
        return content

    def get_data(self):
        """Get dictionary to construct child of :attr:`widget`."""
        return {value: self.option_dict[key] for key, value in self.kv_dict.items()}

    def construct_widget(self):
        """Constructs widget that is used for the selection of :attr:`content`."""
        self.widget = Builder.load_string(self.widget_kv)
        self.update_widget_data()

    def update(self):
        self.pre_process()
        self.update_widget_data()

    def update_widget_data(self):
        if self.widget:
            for key, value in self.kv_dict.items():
                setattr(self.widget, value, self.option_dict[key])

    def get_content(self):
        if self.widget:
            content = {
                key: getattr(self.widget, value) for key, value in self.kv_dict.items()
            }
        else:
            content = self.option_dict
        return self.post_process(content)


@attr.s(auto_attribs=True)
class DisplayTextField(Field):
    widget_kv: str = """
MDLabel:
    size_hint:1, None
    size: self.texture_size
"""


@attr.s
class TextInputField(Field):
    callback = attr.ib(default=None, type=Callable)
    widget_kv = attr.ib(default="MDTextField")

    def construct_widget(self):
        super(TextInputField, self).construct_widget()
        self.widget.hint_text = self.field_name
        self.widget.bind(on_text_validate=self.on_text_validate)

    def on_text_validate(self, widget):
        text = widget.text
        self.option_dict[self.kv_dict.inverse["text"]] = text
        if self.callback:
            self.callback(text)


@attr.s
class OptionsField(Field):
    """
    Implementation of Field.
    """

    option_dict = attr.ib()
    get_selection = attr.ib(default=None, type=Callable)

    @option_dict.default
    def _get_option_dict_default(self):
        return {self.field_name: []}

    def get_data(self):
        """Get dictionary to construct child of :attr:`widget`."""
        l = min(len(x) for x in self.option_dict.values())
        print(self.option_dict)
        return [
            {value: self.option_dict[key][i] for key, value in self.kv_dict.items()}
            for i in range(l)
        ]

    def update_widget_data(self):
        if self.widget:
            self.widget.data = self.get_data()

    def get_content(self):
        if self.widget_kv and hasattr(self.widget, "get_checked"):
            content = {
                field: ", ".join(
                    [getattr(widget, kv_attr) for widget in self.widget.get_checked()]
                )
                for field, kv_attr in self.kv_dict.items()
            }
        elif self.get_selection:
            content = self.get_selection()
        else:
            content = {
                field: (
                    options[0]
                    if isinstance(options, list) and len(options) >= 1
                    else options
                )
                for field, options in self.option_dict.items()
            }
        return self.post_process(content)


@attr.s(auto_attribs=True)
class CheckChipOptionsField(OptionsField):
    widget_kv: str = "MyCheckChipContainer"


@attr.s(auto_attribs=True)
class TransChipOptionsField(OptionsField):
    widget_kv: str = """
MyCheckChipContainer
    child_class_name: "MyTransChip"
    check_one: True"""


@attr.s(auto_attribs=True)
class DualLongTextField(OptionsField):
    widget_kv: str = "CardCarousel"


@attr.s(auto_attribs=True)
class ImgField(OptionsField):
    option_dict: Dict[str, Any] = {"image": [], "word": ""}
    kv_dict: dict or bidict = {"image": "source"}
    widget_kv: str = "ImageCarousel"

    def post_process(self, content):
        field_name = self.kv_dict.inverse["source"]
        print("downloading image...")
        url = content[field_name]
        resp = requests.get(url)
        content[field_name] = resp.content if resp.ok else None
        print("done.")
        return content


class MediaField(Field):
    def pre_process(self):
        url = self.option_dict[self.field_name]
        print(f"downloading file from {url}...")
        response = requests.get(url)
        media_file = response.content if response.ok else None
        self.option_dict[self.field_name] = media_file
        print("done.")


Builder.load_string(
    """
<Template>:
    orientation: "vertical"
    size_hint:1,1
    padding: 10
    spacing: 10
"""
)


class Template(BoxLayout):
    fields: List[Field] = None
    parsers: Dict[str, Parser] = None
    data: Dict = None
    content: Dict = None
    search_term: str = None
    name: str = None
    sort_field: str = None

    def __init__(self, **kwargs):
        super(Template, self).__init__(**kwargs)

    def template_db(self):
        return get_template(self.name) or new_template(self)

    def current_card_db(self):
        t_db = self.template_db()
        return t_db.get_card(self.search_term) or t_db.add_card(self)

    def set_data_from_parsers(self):
        self.data = {}
        for parser in self.parsers.values():
            parser_res_dict = parser.result_dict(self.search_term)
            for key, value in parser_res_dict.items():
                if (
                    key in self.data
                    and isinstance(self.data[key], list)
                    and isinstance(parser_res_dict[key], list)
                ):
                    self.data[key] += value
                else:
                    self.data[key] = value
        pprint(self.data)

    def update_fields(self):
        for field in self.fields:
            for key in field.option_dict:
                if key in self.data:
                    field.option_dict[key] = self.data[key]
            field.update()

    def add_field_widgets(self):
        for field in self.fields:
            if field.widget:
                self.add_widget(field.widget)

    def get_content_from_fields(self):
        res_dict = {}
        for field in self.fields:
            print(field)
            res_dict.update(field.get_content())
        self.content = res_dict

    def post_process(self):
        """Placeholder-function."""

    def get_results(self):
        self.get_content_from_fields()
        self.post_process()
        pprint(self.content)
        with db_session:
            current_card = self.current_card_db()
            media_files = (
                self.content["media_files"] if "media_files" in self.content else []
            )
            for file_type, file in media_files.items():
                current_card.add_media_file(type=file_type, file=file)
            current_card.fields = {
                key: val for key, val in self.content if key != "media_files"
            }
        return self.content

    def search(self, search_term):
        self.search_term = search_term
        self.db_current_card = self.template_db().get_card(search_term)
        with db_session:
            if self.db_current_card and self.db_current_card.base_data:
                self.data = self.db_current_card.base_data
            else:
                self.db_current_card = self.db_current_card or get_template(
                    self.name
                ).add_card(search_term)
                self.set_data_from_parsers()
                self.db_current_card.base_data = self.data
        self.update_fields()

    # @classmethod
    # def from_db(cls, name):
    #     with db_session:
    #         template = cls()
    #         template.fields = []
    #         template.parsers = []
    #         template_db_entry = get_template(name)
    #         for db_parser in template_db_entry.parsers:
    #             template.parsers.append(init_from_db(db_parser))
    #         for db_field in template_db_entry.fields:
    #             template.fields.insert(0, init_from_db(db_field, template))
    #         return template


class PtTemplate(Template):
    name = "Portuguese Vocab"
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
            "google_images": GoogleImagesParser(**parser_attrs),
        }
        self.fields = [
            TextInputField(field_name="word", callback=self.search),
            ImgField(),
            CheckChipOptionsField(field_name="translation"),
            TransChipOptionsField(
                option_dict={"synonym": [], "synonym_trans": []},
                kv_dict={"synonym": "text_orig", "synonym_trans": "text_trans"},
            ),
            TransChipOptionsField(
                option_dict={"antonym": [], "antonym_trans": []},
                kv_dict={"antonym": "text_orig", "antonym_trans": "text_trans"},
            ),
            DualLongTextField(
                option_dict={"explanation": [], "explanation_trans": []},
                kv_dict={"explanation": "text_orig", "explanation_trans": "text_trans"},
            ),
            DualLongTextField(
                option_dict={"example": [], "example_trans": []},
                kv_dict={"example": "text_orig", "example_trans": "text_trans"},
            ),
        ]

    def set_data_from_parsers(self):
        super(PtTemplate, self).set_data_from_parsers()
        self.add_translations()

    def translate(self, string):
        """Translate string from :attr:`from_lang` to :attr:`to_lang`."""
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text

    def add_translations(self):
        for key_trans in self.data:
            match = re.findall(r"(.*)(_trans)", key_trans)
            if match:
                key_orig = match[0][0]
                for i, (text_orig, text_trans) in enumerate(
                    zip(self.data[key_orig], self.data[key_trans])
                ):
                    self.data[key_trans][i] = text_trans or self.translate(text_orig)


if __name__ == "__main__":
    from kivymd.app import MDApp

    # Template.from_db("Random Wiki Template")

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            # template = Template.from_db("Random Wiki Template")
            template = Builder.load_string(
                """#
PtTemplate:
    MDFlatButton:
        text: "Get Results"
        on_press: app.root.get_results()"""
            )
            print(template.fields)
            template.add_field_widgets()
            return template

    _TestApp().run()
