"""
Implements :class:`AnkiObject` and :class:`ApkgExporter`.

Relies heavily on `genanki <https://github.com/kerrickstaley/genanki>`_.

Its purpose is to handle everything Anki-related:
    * construct card template from html-, css-, and js-files
    * generating and adding cards
    * saving apgk-file
"""


import pathlib
import re
from datetime import datetime

import attr
import bs4
import genanki
from kivymd.app import MDApp
from kivymd.toast import toast
from pony.orm import db_session

from ..utils import CD, cd_temp_dir, now_string, set_word_state
from . import EXPORTER_DIR


@attr.s
class HtmlLoader:
    """Load and process html."""

    path = attr.ib(default=None)
    """Path to load html-file from."""
    string = attr.ib(init=False)
    """Content of the file at :attr:`path`."""

    def __attrs_post_init__(self):
        with open(self.path) as file:
            self.string = file.read()

    def set_of_fields(self):
        """
        Get names of fields (as recognized by Anki) in the content of the html-file.

        Returns:
            Set[str]: Field names.
        """
        matches = re.findall("{{(type:|/|#)*([^}]*)}}", self.string)
        fields = {match[1] for match in matches}
        return fields

    def replace_includes_with_content(self):
        """
        Insert content of js-source-files at appropriate places and return body.

            * Removes ``src`` attributes from <script>-tags and inserts the content of the files.
            * ``<script>``-tags with "defer"-attribute are moved to the bottom of the body.
            * ``<script>``-tags in the header are moved to the top of the body.

        Returns:
            str: Body of processed html-file.
        """
        soup = bs4.BeautifulSoup(self.string, "lxml")
        for tag in soup.select("script[src]"):
            src = tag["src"]
            del tag.attrs["src"]
            with open(src) as file:
                tag.string = file.read()
        for tag in soup.select("script[defer]"):
            del tag.attrs["defer"]
            tag.extract()
            soup.body.append(tag)
        for tag in soup.select("head script"):
            tag.extract()
            soup.body.insert(0, tag)
        return str(soup.body)


def model_from_html(name, template_names, model_id, css_path):
    """
    Construct Model from html- and css-files.

    Args:
      name: Model name.
      template_names: List of html-paths.
      model_id: Unique id-string for the model.
      css_path: Path of css-file.

    Returns:
        constructed ``genanki.model``
    """
    templates_html = {
        template_name: {
            "front": HtmlLoader(f"{template_name}_front.html"),
            "back": HtmlLoader(f"{template_name}_back.html"),
        }
        for template_name in template_names
    }
    fields = set()
    for _, temp_dict in templates_html.items():
        for _, side in temp_dict.items():
            fields |= side.set_of_fields()
    fields = [{"name": field} for field in sorted(fields, reverse=True)]

    templates = [
        {
            "name": temp_name,
            "qfmt": templates_html[temp_name]["front"].replace_includes_with_content(),
            "afmt": templates_html[temp_name]["back"].replace_includes_with_content(),
        }
        for temp_name in templates_html
    ]

    with open(css_path) as file:
        css = file.read()

    return genanki.Model(
        model_id=model_id,
        name=name,
        fields=fields,
        templates=templates,
        css=css,
    )


@attr.s
class AnkiObject:  # pylint: disable=too-many-instance-attributes
    """
    Class containing all necessary objects from the `genanki <https://github.com/kerrickstaley/genanki>`_-module.

    Attributes:
        model: :class:`genanki.model`
        deck: :class:`genanki.deck`
        package: :class:`genanki.package`
        fields: List of field-names on anki-card.
    """

    model_name = attr.ib(default="pt-word")
    templates = attr.ib(default=["meaning-pt", "pt-meaning"])
    deck_name = attr.ib(default="Portuguese::Vocab")
    css_path = attr.ib(default="css/pt.css")
    root_dir = attr.ib(default=EXPORTER_DIR)
    id = attr.ib(default=12345)

    def __attrs_post_init__(self):
        with CD(self.root_dir):
            self.model = model_from_html(
                self.model_name,
                self.templates,
                css_path=self.css_path,
                model_id=self.id,
            )
            self.deck = genanki.Deck(self.id, name=self.deck_name)
            self.package = genanki.Package(self.deck)
            self.fields = [
                field
                for field_dict in self.model.fields
                for field in field_dict.values()
            ]

    def add_card(self, media_files=None, **kwargs):
        """
        Add card constructed from ``**kwargs`` to :attr:`deck` and ``media_files`` to :attr:`package.media_files`.

        Args:
          media_files (List[str]): Media files used on card.  (Default value = None)
          **kwargs: In the form: ``field_name="content"``.

        """
        if media_files is None:
            media_files = []
        fields = {
            field: (kwargs[field] if field in kwargs else "") for field in self.fields
        }
        fields = [fields[key] for key in sorted(fields, reverse=True)]
        new_note = genanki.Note(model=self.model, fields=fields, sort_field="word")
        for file in media_files:
            self.package.media_files.append(file)
        self.deck.add_note(new_note)

    def write_apkg(self, out_path):
        """
        Write current :attr:`package` as apkg-file to ``out_path``.

        Args:
          out_path: Path wherer .apkg-file is saved.
        """
        self.package.write_to_file(out_path)


def get_cards(state=None):
    """Get words from word_state_dict filtered, possibly filtered by state."""
    return {
        key
        for key, val in MDApp.get_running_app().word_state_dict.items()
        if not state or val in state
    }


@db_session
def export_cards(card_names):
    """Export cards to <template_name>_<time-stamp>.apkg file in apgk_export_dir."""
    if not card_names:
        toast("Empty selection.", duration=5)
        return
    config = MDApp.get_running_app().config
    template_dir = config["Paths"]["anki_template_dir"]
    anki_config = config["Anki"]
    anki_obj = AnkiObject(root_dir=template_dir, **anki_config)
    template_name = config["Template"]["name"]
    out_file = f'{template_name.replace(" ","_")}_{now_string()}.apkg'
    out_folder = config["Paths"]["apkg_export_dir"]
    out_path = pathlib.Path(out_folder) / out_file
    toast(f"Exporting cards to {out_folder}...", duration=5)
    card_list = [
        card
        for card in MDApp.get_running_app().get_current_template_db().get_cards()
        if card.name in card_names
    ]
    write_apkg(anki_obj, card_list, out_path)
    set_cards_exported(card_list)


def write_apkg(anki_obj, card_list, out_path):
    """Write apkg to ``out_path``."""
    with cd_temp_dir():
        for card in card_list:
            card.write_media_files_to_folder()
            anki_obj.add_card(**card.fields)
        anki_obj.write_apkg(out_path)


def set_cards_exported(card_list):
    """Set state to ``"exported"``."""
    now = datetime.now()
    for card in card_list:
        card.state = "exported"
        card.dt_exported = now
        set_word_state(word=card.name, state="exported")


# pylint: disable = W,C,R,I
# if __name__ == "__main__":
# ankiobject = AnkiObject(root_dir=ANKI_DIR)
