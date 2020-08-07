"""Database containing Templates, Cards and the corresponding media-files."""
from datetime import datetime

import toolz
from pony.orm import (
    buffer,
    Database,
    db_session,
    Json,
    Optional,
    PrimaryKey,
    Required,
    select,
    Set,
    set_sql_debug,
)

db = Database()
db.bind(provider="sqlite", filename="db.sqlite", create_db=True)


# @attr.s(
#     these={
#         "name": attr.ib(),
#         "id": attr.ib(init=False),
#         "cards": attr.ib(init=False),
#         "cls_name": attr.ib(default="fields.Template"),
#         "description": attr.ib(default=""),
#         "additional_info": attr.ib(default=None),
#     }
# )
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
        """The ``name`` attribute is unique, so we can get a single :class:`Card` by name."""
        cards = select(c for c in self.cards if c.name == name)
        return toolz.first(cards) if cards else None

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


if __name__ == "__main__":
    set_sql_debug(True)

    with db_session:
        # rand_wiki_template = Template(
        #     name="Random Wiki Template",
        #     cls_name="fields.Template",
        #     description="Generate cards from random articles of a topic on Wikipedia.",
        # )
        rand_wiki_template = Template(
            name="Portuguese Vocab",
            cls_name="fields.PtTemplate",
            description="Generate beautiful cards to learn brazilian portuguese vocabulary.\nSources: Dicio,Reverso,"
            "Linguee and Google Images.",
        )
