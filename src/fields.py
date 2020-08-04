from typing import Any, Callable, Dict, List

import attr
import requests
from bidict import bidict

from custom_widgets.scroll_widgets import *
from custom_widgets.selection_widgets import *
from db import get_template, new_template
from parsers import (
    DicioParser,
    GoogleImagesParser,
    LingueeParser,
    Parser,
    ReversoParser,
)


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


@attr.s(auto_attribs=True)
class Field:
    """
    Implementation of Field.
    """

    option_dict: Dict[str, Any] = {"field1": "value1"}
    kv_dict: dict or bidict = None
    widget: object = None
    widget_kv: str = None

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


@attr.s(auto_attribs=True)
class TextInputField(Field):
    widget_kv: str = "MDTextField"
    callback: Callable = None

    def construct_widget(self):
        super(TextInputField, self).construct_widget()
        self.widget.hint_text = toolz.first(self.option_dict.keys())
        self.widget.bind(on_text_validate=self.on_text_validate)

    def on_text_validate(self, widget):
        text = widget.text
        self.option_dict[self.kv_dict.inverse["text"]] = text
        if self.callback:
            self.callback(text)


@attr.s(auto_attribs=True)
class OptionsField(Field):
    """
    Implementation of Field.
    """

    option_dict: Dict[str, Any] = {"field1": ["op1", "op2"]}
    kv_dict: dict or bidict = None
    widget: object = None
    widget_kv: str = None
    selection_callback: Callable = None

    def get_data(self):
        """Get dictionary to construct child of :attr:`widget`."""
        l = min(len(x) for x in self.option_dict.values())
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
        elif self.selection_callback:
            content = self.selection_callback()
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
class ImgField(OptionsField):
    option_dict = {"image": []}
    kv_dict: dict or bidict = {"image": "source"}
    widget_kv: str = "ImageCarousel"

    def post_process(self, content):
        field_name = self.kv_dict.inverse["source"]
        try:
            print("downloading image...")
            url = content[field_name]
            resp = requests.get(url)
            with open("out.png", "wb") as file:
                file.write(resp.content)
            content[field_name] = '<img src="out.png">'
        except:
            print("download failed...")
            content[field_name] = ""
        return content


Builder.load_string(
    """
<Template>:
    orientation: "vertical"
    size_hint:1,1
    padding: 10
    spacing: 10
"""
)


@attr.s(auto_attribs=True)
class Template(BoxLayout):
    fields: List[Field] = None
    parsers: Dict[str, Parser] = None
    data: Dict = None
    content: Dict = None
    search_term: str = None
    name: str = None
    db_template: object = None
    sort_field: str = None
    db_current_card: object = None

    def __attrs_post_init__(self):
        self.db_template = get_template(self.name) or new_template(self.name)

    def set_data_from_parsers(self):
        self.data = {}
        for parser in self.parsers.values():
            parser_res_dict = parser.result_dict(self.search_term)
            self.data.update(parser_res_dict)
        print(self.data)

    def update_fields(self):
        for field in self.fields:
            for key in field.option_dict:
                if key in self.data:
                    field.option_dict[key] = self.data[key]
            field.update_widget_data()

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
        print(self.content)
        return self.content

    def search(self, search_term):
        self.search_term = search_term
        self.set_data_from_parsers()
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


@attr.s(auto_attribs=True)
class PtTemplate(Template):
    from_lang: str = "pt"
    to_lang: str = "de"

    def __attrs_post_init__(self):
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
        self.fields = [ImgField()]


if __name__ == "__main__":
    from kivymd.app import MDApp

    # Template.from_db("Random Wiki Template")

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            # template = Template.from_db("Random Wiki Template")
            template = Builder.load_string(
                """
RandWikiTemplate:
    MDFlatButton:
        text: "Get Results"
        on_press: app.root.get_results()"""
            )

            template.add_field_widgets()
            print(template.fields)
            return template

    _TestApp().run()
