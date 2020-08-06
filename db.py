from datetime import datetime
from pydoc import locate

import toolz
from pony.orm import *

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
    id = PrimaryKey(int, auto=True)
    cls_name = Required(str)
    name = Required(str, unique=True)
    description = Optional(str)
    cards = Set("Card")
    additional_info = Optional(Json)

    @db_session
    def get_card(self, name):
        cards = select(c for c in self.cards if c.name == name)
        return toolz.first(cards) if cards else None

    @db_session
    def add_card(self, name):
        card = Card(name=name, state="waiting", template=self)
        return card


class Card(db.Entity):
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
        super(Card, self).__setattr__(key, value)
        if key == "base_data":
            self.dt_queried = datetime.now()
        if key == "fields":
            self.dt_generated = datetime.now()


class Parser(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    cls_name = Required(str)
    init_json = Optional(Json)


class Field(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    cls_name = Required(str)
    init_json = Optional(Json)
    callback_str = Optional(str)


class MediaFile(db.Entity):
    id = PrimaryKey(int, auto=True)
    type = Required(str)
    content = Required(buffer)
    card_content = Required(Card)


db.generate_mapping(create_tables=True)


@db_session
def get_template(name):
    templates = select(t for t in Template if t.name == name)
    return toolz.first(templates) if templates else None


@db_session
def new_template(template_obj):
    return Template(
        name=template_obj.name,
        cls_name=f"fields.{type(template_obj).__name__}",
        description="A template.",
    )


@db_session
def init_from_db(db_obj, callback_obj=None):
    cls = locate(db_obj.cls_name)
    obj = cls(**db_obj.init_json)
    if getattr(db_obj, "callback_str", None):
        callback_obj = callback_obj or locals()
        obj.callback = getattr(callback_obj, db_obj.callback_str)
    return obj


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
        # rand_wiki_parser = Parser(
        #     name="Random Wiki Parser",
        #     templates=[rand_wiki_template],
        #     cls_name="parsers.RandTopicWikiParser",
        #     init_json={"phrase": None, "from_lang": None, "to_lang": None},
        # )
