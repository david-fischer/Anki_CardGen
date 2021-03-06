"""
The app uses :mod:`pony` to manage a sqlite-database. The database is structured as follows.

.. image:: ../docs/ponyorm_diagram.png
"""
from datetime import datetime

import toolz
from pony.orm import (
    Database,
    Json,
    Optional,
    PrimaryKey,
    Required,
    Set,
    buffer,
    db_session,
    select,
)

from . import APP_DIR
from .utils import CD, update_word_state_dict

db = Database()
db_path = APP_DIR / "db.sqlite"
db.bind(
    provider="sqlite",
    filename=str(db_path),
    create_db=not db_path.exists(),
)


class Template(db.Entity):
    """Contains data of a :class:`fields.Template` and all cards that have been generated with the template."""

    id = PrimaryKey(int, auto=True)
    """Id."""
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
    def get_cards(self, selector=None):
        """Get cards by selector."""
        if selector is not None:
            return select(c for c in self.cards if selector(c))
        return select(c for c in self.cards)

    @db_session
    def add_card(self, name):
        """Create a new :class:`Card` with relation to this template."""
        card = Card(name=name, state="waiting", template=self)
        return card

    @classmethod
    @db_session
    def names(cls):
        """Return list of all Templates in database."""
        return [template.name for template in cls.select()]


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
        super().__setattr__(key, value)
        if key == "base_data":
            self.dt_queried = datetime.now()
            self.state = "ready"
        if key == "fields":
            self.dt_generated = datetime.now()
            self.state = "done"
        if key == "state":
            update_word_state_dict(self.name, self.state)

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
    def write_media_files_to_folder(self, folder="."):
        """Write media-files in :attr:`media_files` to folder with name `folder`."""
        media_files = select(m for m in self.media_files)
        for m_file in media_files:
            name = f"{self.name}.{m_file.type}"
            with CD(folder):
                with open(name, "wb") as file:
                    file.write(m_file.content)


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


# pylint: disable = W,C,R,I
if __name__ == "__main__":
    from . import ANKI_DIR
    from .exporter import export_cards

    with db_session:
        template = Template.get(name="Portuguese Vocab")
        cards = select(c for c in template.cards if c.state == ("done" or "exported"))
        # export_cards(
        #     cards, "/home/david/Schreibtisch/", os.path.join(ANKI_DIR, "vocab_card")
        # )
