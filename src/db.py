"""
The app uses :mod:`pony` to manage a sqlite-database. The database is structured as follows.

.. image:: ../docs/ponyorm_diagram.png
"""
import os
import shutil
from datetime import datetime

import toolz
from pony.orm import (
    buffer,
    Database,
    db_session,
    dbapiprovider,
    Json,
    Optional,
    PrimaryKey,
    Required,
    select,
    Set,
)

from generate_anki_card import AnkiObject
from utils import CD, now_string

TEMPLATE_DICTS = [
    {
        "name": "Portuguese Vocab",
        "cls_name": "templates.PtTemplate",
        "description": "Generate beautiful cards to learn brazilian portuguese vocabulary.\n"
        "Sources: Dicio,Reverso,Linguee and Google Images.",
    }
]


# print(os.listdir(), os.path.exists("db.sqlite"))
# print(os.getcwd())
db = Database()
try:
    db.bind(
        provider="sqlite",
        filename="/data/data/org.ankicardgen.ankicardgenapp/files/app/db.sqlite",
        create_db=True,
    )
except dbapiprovider.OperationalError:
    db.bind(provider="sqlite", filename="db.sqlite")


class Template(db.Entity):
    """Contains data of a :class:`fields.Template` and all cards that have been generated with the template."""

    id = PrimaryKey(int, auto=True)
    """Id."""
    cls_name = Required(str)
    """The "module.class" to construct the template from."""
    name = Required(str, unique=True)
    """A unique name for the template."""
    description = Optional(str)
    """A short description of the template."""
    cards = Set("Card")
    """References to all the cards that have been generated using this template."""
    additional_info = Optional(Json)
    """Additional info."""

    @db_session
    def get_card(self, name):
        """Get a single :class:`Card` by name. (unique attribute)."""
        cards_by_name = select(c for c in self.cards if c.name == name)
        return toolz.first(cards_by_name) if cards_by_name else None

    @db_session
    def get_cards_by_selector(self, selector):
        """Get cards by selector."""
        return select(c for c in self.cards if selector(c))

    @db_session
    def add_card(self, name):
        """Create a new :class:`Card` with relation to this template."""
        card = Card(name=name, state="waiting", template=self)
        return card


class Card(db.Entity):
    """Object containing the data for a card."""

    id = PrimaryKey(int, auto=True)
    name = Required(str)
    state = Required(str)
    base_data = Optional(Json)
    fields = Optional(Json)
    media_files = Set("MediaFile")
    dt_queried = Optional(datetime)
    dt_generated = Optional(datetime)
    dt_exported = Optional(datetime)
    template = Required(Template)

    def __setattr__(self, key, value):
        """Change state according to values set."""
        super(Card, self).__setattr__(key, value)
        if key == "base_data":
            self.dt_queried = datetime.now()
            self.state = "ready"
        if key == "fields":
            self.dt_generated = datetime.now()
            self.state = "done"

    @db_session
    def get_media(self, field_key):
        """Get :class:`MediaFile` of this card by ``field_key`` which is unique."""
        media_files = select(m for m in self.media_files if m.field_key == field_key)
        return toolz.first(media_files) if media_files else None

    @db_session
    def add_media(self, **kwargs):
        """Add a new :class:`MediaFile` to this card."""
        media_file = MediaFile(**kwargs, card=self)
        return media_file

    @db_session
    def write_media_files_to_folder(self, folder):
        """Write media-files in :attr:`media_files` to folder with name `folder`."""
        media_files = select(m for m in self.media_files)
        for m_file in media_files:
            name = f"{self.name}.{m_file.type}"
            with CD(folder):
                with open(name, "wb") as file:
                    file.write(m_file.content)


## UNUSED FOR THE MOMENT:
# class Parser(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     name = Required(str)
#     cls_name = Required(str)
#     init_json = Optional(Json)
#
#
# class Field(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     name = Required(str)
#     cls_name = Required(str)
#     init_json = Optional(Json)
#     callback_str = Optional(str)


class MediaFile(db.Entity):
    """Class containing a media-file."""

    id = PrimaryKey(int, auto=True)
    """Unique id."""
    type = Required(str)
    """File type, e.g. "mp3", "jpg", "png", etc. ..."""
    field_key = Required(str)
    """Name of the field of the card which the content belongs to."""
    content = Required(buffer)
    """Bytes object with media-file."""
    card = Required(Card)
    """Relation to :class:`Card` object."""

    @db_session
    def update(self, **kwargs):
        """Update attributes by ``*kwargs``."""
        for key, val in kwargs.items():
            setattr(self, key, val)


db.generate_mapping(create_tables=True)


@db_session
def get_template(name):
    """Get :class:`Template` by unique ``name``-attribute."""
    templates = select(t for t in Template if t.name == name)
    return toolz.first(templates) if templates else None


@db_session
def new_template(template_obj):
    """Create a new entry in the database from an :class:`fields.Template`-object."""
    return Template(
        name=template_obj.name,
        cls_name=f"fields.{type(template_obj).__name__}",
        description="A template.",
    )


@db_session
def get_card_by_id(card_id):
    """Get card from database by id."""
    card_list = select(c for c in Card if c.id == card_id)
    return toolz.first(card_list) if card_list else None


def export_cards(card_list, out_folder):
    """Export cards to <template_name>_<time-stamp>.apkg file in out_folder."""
    anki_obj = AnkiObject(root_dir="anki")
    if not card_list:
        print("Empty list.")
        return False
    folder_name = f"temp_{now_string()}"
    os.makedirs(folder_name, exist_ok=True)
    for card in card_list:
        card.write_media_files_to_folder(folder_name)
        content_dict = card.fields
        anki_obj.add_card(**content_dict)
    with CD(folder_name):
        file_name = f'{toolz.first(card_list).template.name.replace(" ", "_")}_{now_string()}.apkg'
        anki_obj.write_apkg(file_name)
    os.rename(os.path.join(folder_name, file_name), os.path.join(out_folder, file_name))
    now = datetime.now()
    for card in card_list:
        card.state = "exported"
        card.dt_exported = now
    shutil.rmtree(folder_name)
    return True


@db_session
def get_template_names():
    """Get list of all templates in database."""
    return list(select(t.name for t in Template))


@db_session
def add_missing_templates():
    """Add templates from :data:`TEMPLATE_DICTS` to database if not already present."""
    template_names = get_template_names()
    for template_dict in TEMPLATE_DICTS:
        if template_dict["name"] not in template_names:
            Template(**template_dict)


# pylint: disable = W,C,R,I
if __name__ == "__main__":
    #

    # with db_session:
    #     # rand_wiki_template = Template(
    #     #     name="Random Wiki Template",
    #     #     cls_name="fields.Template",
    #     #     description="Generate cards from random articles of a topic on Wikipedia.",
    #     # )
    #     rand_wiki_template = Template(
    #         name="Portuguese Vocab",
    #         cls_name="fields.PtTemplate",
    #         description="Generate beautiful cards to learn brazilian portuguese vocabulary.\nSources: Dicio,Reverso,"
    #         "Linguee and Google Images.",
    #     )
    with db_session:
        template = get_template("Portuguese Vocab")
        cards = select(c for c in template.cards if c.state == ("done" or "exported"))
        export_cards(cards, "/home/david/Schreibtisch/")
