"""
Implementation of :class:`Field` and subclasses. They are used in the :attr:`templates.template.fields` attribute.

Each one is responsible handling a part of data-procesing in the card-generation process. This allows easy
customization of :class:`templates.Template`.
"""
from typing import Callable

import attr
import requests
from bidict import bidict
from googletrans import Translator
from kivy.lang import Builder
from pony.orm import db_session

from utils import compress_img_bytes

translator = Translator()


@attr.s
class TranslationMixin:
    """Mixin-Class that adds missing translations to the ``target_field`` of the ``template.data`` dict."""

    template = attr.ib(type=object)
    """Instance of :class:`templates.template`."""
    trans_callback = attr.ib(type=Callable)
    """Function that is applied to the data in source field to obtain a translation."""
    src_field = attr.ib(default="")
    """Name of the source_field of :attr:`template`.data."""
    target_field = attr.ib(default="")
    """Name of the target_field of :attr:`template`.data."""
    _kv_bidict = attr.ib()
    """Mapping between fields and kv_attributes of widgets."""

    @_kv_bidict.default
    def _get_kv_dict_default(self):
        return bidict({self.src_field: "text_orig", self.target_field: "text_trans"})

    @trans_callback.default
    def _default_trans_callback(self):
        return self.template.translate

    def pre_process(self):
        """
        Add translations, where they are missing.

        Handles the cases that source and target are strings or list of strings.
        """
        if hasattr(self, "pre_process"):
            super(TranslationMixin, self).pre_process()
        if self.template.data and self.src_field in self.template.data:
            src_data = self.template.data[self.src_field]
            if isinstance(src_data, str):
                self.template.data[self.target_field] = self.template.data.get(
                    self.target_field, None
                ) or self.trans_callback(src_data)
            if isinstance(src_data, list):
                target_data = self.template.data.get(self.target_field, None) or [
                    None for _ in src_data
                ]
                if len(target_data) < len(src_data):
                    target_data += [None] * (len(target_data) - len(src_data))
                self.template.data[self.target_field] = [
                    trans or self.trans_callback(source)
                    for source, trans in zip(src_data, target_data)
                ]


@attr.s
class Field:
    """
    Base-class for fields.

    Accesses the data in :attr:`template`.data, can perform actions on the obtained data and/or display it in a
    widget to allow user input to change it.
    """

    template = attr.ib()
    """Reference to :class:`templates.Template`."""
    field_name = attr.ib(default="default_field")
    """Key of :attr:`template`.data which this field is handling."""
    heading = attr.ib(default=None)
    """Heading to be shown over widget."""
    widget = attr.ib(type=object, default=None)
    """Gets constructed by :meth:`~kivy.lang.Builder.load_string` from :attr:`widget_kv` if set."""
    widget_kv = attr.ib(type=str, default=None)
    """If set, widget gets constructed."""
    _kv_bidict = attr.ib()
    """Mapping between attributes of kivy-widget and field_name."""

    @property
    def kv_bidict(self):
        """Getter function for :attr:`_audio_url`."""
        return self._kv_bidict

    @kv_bidict.setter
    def kv_bidict(self, value):
        """Set :attr:`_audio_url` and download file."""
        if not isinstance(value, bidict):
            value = bidict(value)
        self._kv_bidict = value

    @_kv_bidict.default
    def _default_kv_dict(self):
        return bidict({self.field_name: "text"})

    def __attrs_post_init__(self):
        self.pre_process()
        if self.widget_kv:
            self.construct_widget()

    def pre_process(self):
        """Placeholder-function."""

    def post_process(self, content):  # pylint: disable=no-self-use
        """Placeholder-function."""
        return content

    def get_data(self):
        """Get dictionary to construct :attr:`widget`."""
        return {
            value: self.template.data[key]
            if self.template.data and key in self.template.data
            else ""
            for key, value in self.kv_bidict.items()
        }

    def construct_widget(self):
        """Construct widget that is used for the selection of :attr:`content`."""
        self.widget = Builder.load_string(self.widget_kv)
        self.update_widget_data()

    def update(self):
        """Apply :meth:`pre_process` and :meth:`update_widget_data`."""
        self.pre_process()
        self.update_widget_data()

    def update_widget_data(self):
        """Check if widget is present and update the attributes of the kivy-widget from :attr:`template`.data."""
        if self.widget:
            for key, value in self.kv_bidict.items():
                if self.template.data and key in self.template.data:
                    setattr(self.widget, value, self.template.data[key])

    def get_content(self):
        """If :attr:`widget` is set, use :attr:`kv_bidict` to extract.

        Calls :meth:`post_process` on the data before returning it.
        """
        if self.widget:
            content = {
                key: getattr(self.widget, value)
                for key, value in self.kv_bidict.items()
            }
        else:
            content = {self.field_name: self.template.data[self.field_name]}
        return self.post_process(content)


@attr.s(auto_attribs=True)
class DisplayTextField(Field):
    """Only displays text."""

    widget_kv: str = """
MDLabel:
    size_hint:1, None
    size: self.texture_size
"""


@attr.s
class TextInputField(Field):
    """
    Displays text and lets user edit it.

    If callback is set, it will be called ``on_text_validate``, i.e. when the user presses enter while field is in
    focus.

    Useful to bind to :meth:`templates.Template.search` or `templates.Template.update_from_single_parser`.
    """

    callback = attr.ib(default=None, type=Callable)
    """Gets called ``on_text_validate`` of the kivy-widget."""
    widget_kv = attr.ib(default="MDTextField")
    """kv-string describing the widget."""

    def construct_widget(self):
        """Furthermore add :attr:`field_name` as hint-text and bind ``on_text_validate``."""
        super(TextInputField, self).construct_widget()
        self.widget.hint_text = self.field_name
        self.widget.bind(on_text_validate=self.on_text_validate)

    def on_text_validate(self, widget):
        """Wrapper-function for the possible call of :attr:`callback`."""
        text = widget.text
        if self.callback:
            self.callback(text)


@attr.s
class OptionsField(Field):
    """Base-class for a field with multiple options to choose from."""

    get_selection = attr.ib(default=None, type=Callable)
    display_limit = attr.ib(default=None)

    def get_data(self):
        """Get dictionaries to construct children of :attr:`widget`."""
        if self.template.data:
            min_len = min(
                len(self.template.data[key]) if key in self.template.data else 0
                for key in self.kv_bidict.keys()
            )
        else:
            min_len = 0
        if self.display_limit:
            min_len = min(self.display_limit, min_len)
        return [
            {value: self.template.data[key][i] for key, value in self.kv_bidict.items()}
            for i in range(min_len)
        ]

    def update_widget_data(self):
        """Update widget (if present) with data from :meth:`get_data`."""
        if self.widget:
            self.widget.data = self.get_data()

    def get_content(self):
        """
        If :attr:`widget` is set, gets content from widget using :attr:`kv_bidict`.

        If :attr:`selection_callback` is set, get content from call.

        Else simply get the first option as default.
        """
        if self.widget_kv and hasattr(self.widget, "get_checked"):
            content = {
                field: ", ".join(
                    [
                        getattr(widget, kv_attr)
                        for widget in self.widget.get_checked()
                        if widget
                    ]
                )
                for field, kv_attr in self.kv_bidict.items()
            }
        elif self.get_selection:
            content = self.get_selection()
        else:
            options = self.template.data[self.field_name]
            content = {
                self.field_name: (
                    options[0]
                    if isinstance(options, list) and len(options) >= 1
                    else options
                )
            }
        return self.post_process(content)


@attr.s(auto_attribs=True)
class CheckChipOptionsField(OptionsField):
    r"""Pick multiple options using :class:`custom_widgets.selection_widgets.CheckChip`\ s."""

    widget_kv: str = "MyCheckChipContainer"


@attr.s(auto_attribs=True)
class TransChipOptionsField(TranslationMixin, OptionsField):
    r"""
    Pick a single options using :class:`custom_widgets.selection_widgets.MyTransChip`\ s.

    Inheritance from :class:`TranslationMixin` guarantees that translations are available.
    """

    widget_kv: str = """
MyCheckChipContainer
    child_class_name: "MyTransChip"
    check_one: True"""


@attr.s(auto_attribs=True)
class DualLongTextField(TranslationMixin, OptionsField):
    """
    Pick a single options using :class:`custom_widgets.selection_widgets.CardCarousel`.

    Useful for longer text, i.e. examples or explanations.

    Inheritance from :class:`TranslationMixin` guarantees that translations are available.
    """

    widget_kv: str = "CardCarousel"


@attr.s
class MediaField(Field):
    """
    Handles download of a single media-file and content of corresponding field.

    The field should only contain the a single url.
    """

    file_type = attr.ib(default="mp3")
    """File-type of media-file."""

    @staticmethod
    def get_media_file(url):
        """Download file using :meth:`requests.get`."""
        print(f"downloading file from {url}...")
        response = requests.get(url)
        print("done." if response.ok else "download failed :(")
        return response.content if response.ok else None

    def get_file_strings(self):
        """Get string that embeds the file in the anki-card."""
        # TODO: Add different media types.
        ext = self.file_type
        name = self.template.search_term
        if ext in ["jpg", "png"]:
            field_val = f'<img src="{name}.{ext}">'
        elif ext in ["wav", "mp3", "ogg"]:
            field_val = f"[sound:{name}.{ext}]"
        else:
            field_val = f"{name}.{ext} (don't know how to embed)."
        return f"{name}.{ext}", field_val

    def save_media_file(self, media_file):
        """Save media_file to the data-base."""
        with db_session:
            current_card = self.template.current_card_db()
            media_file_db = current_card.get_media(self.field_name)
            if media_file_db:
                media_file_db.update(
                    content=media_file, field_key=self.field_name, type=self.file_type
                )
            else:
                current_card.add_media(
                    content=media_file, field_key=self.field_name, type=self.file_type
                )

    def pre_process(self):
        """Obtain url, download and save file."""
        url = (
            self.template.data[self.field_name]
            if self.template.data and self.field_name in self.template.data
            else None
        )
        if url and isinstance(url, str):
            media_file = self.get_media_file(url)
            if media_file:
                self.save_media_file(media_file=media_file)

    def post_process(self, content):
        """Return strings for the fields of the anki-card."""
        with db_session:
            current_card = self.template.current_card_db()
            media_file_db = current_card.get_media(self.field_name)
        file_name, field_val = self.get_file_strings()
        content[self.field_name] = field_val
        content["media_files"] = [file_name]
        return content if media_file_db else {self.field_name: ""}


@attr.s
class ImgField(OptionsField, MediaField):
    """Let user choose between multiple images."""

    file_type = attr.ib(default="jpg")
    widget_kv = attr.ib(default="ImageCarousel:\n\theight:dp(250)")
    display_limit = attr.ib(default=10)
    _kv_bidict = attr.ib()

    def construct_widget(self):
        """Bind :meth:`on_error` to child's ``on_error`` event."""
        super(ImgField, self).construct_widget()
        self.widget.bind(on_error=self.on_error)

    @_kv_bidict.default
    def _get_kv_dict_default(self):
        return bidict({self.field_name: "source"})

    def post_process(self, content):
        """Download user choice and save to data-base."""
        url = content[self.field_name]
        if url:
            img_file = self.get_media_file(url)
            if img_file:
                img_file = compress_img_bytes(img_file)
                self.save_media_file(media_file=img_file)
        return super(ImgField, self).post_process(content)

    def on_error(self, _widget, child, *_):
        """Remove urls that could not be loaded from :attr:`template`.data."""
        self.template.data[self.field_name].remove(child.source)
        self.update()
