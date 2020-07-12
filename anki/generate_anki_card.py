import re

import attr
import bs4
import genanki

from utils import CD, smart_loader


@attr.s
class HtmlLoader:
    path = attr.ib(default=None)

    def __attrs_post_init__(self):
        with open(self.path, "r") as file:
            self.string = file.read()

    def set_of_fields(self):
        return set(re.findall("{{([^}]*)}}", self.string))

    def replace_includes_with_content(self):
        soup = bs4.BeautifulSoup(self.string, "lxml")
        js_tags = soup.select("script")
        for tag in js_tags:
            src = tag["src"]
            # print(tag.attrs)
            defer = "defer" in tag.attrs
            del tag.attrs
            with open(src, "r") as file:
                tag.string = file.read()
            if defer:
                tag.extract()
                soup.body.append(tag)
        # css_tags = soup.select("link[rel=stylesheet][href*=css]")
        # for css in css_tags:
        #     css.extract()
        return str(soup.body)


def model_from_html(name, template_names, id, css_path):
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

    with open(css_path, "r") as file:
        css = file.read()

    return genanki.Model(
        model_id=id, name=name, fields=fields, templates=templates, css=css,
    )


@attr.s
class AnkiObject:
    model_name = attr.ib(default="pt-word")
    templates = attr.ib(default=["meaning-pt", "pt-meaning"])
    deck_name = attr.ib(default="Portuguese::Vocab")
    css_path = attr.ib(default="css/pt.css")
    root_dir = attr.ib(default=".")
    id = attr.ib(default=12345)

    def __attrs_post_init__(self):
        with CD(self.root_dir):
            self.model = model_from_html(
                self.model_name, self.templates, css_path=self.css_path, id=self.id
            )
            self.deck = genanki.Deck(self.id, name=self.deck_name)
            self.package = genanki.Package(self.deck)
            self.fields = [
                field
                for field_dict in self.model.fields
                for field in field_dict.values()
            ]

    def add_card(self, media_files=None, **kwargs):
        if media_files is None:
            media_files = []
        fields = {
            field: (kwargs[field] if field in kwargs else "") for field in self.fields
        }
        fields = [fields[key] for key in sorted(fields, reverse=True)]
        new_note = genanki.Note(model=self.model, fields=fields, sort_field="Word")
        for file in media_files:
            self.package.media_files.append(file)
        self.deck.add_note(new_note)

    def write_apkg(self, out_path):
        self.package.write_to_file(out_path)


if __name__ == "__main__":
    with CD(".."):
        ankiobject = AnkiObject(root_dir="anki")
        ankiobject.add_card(
            **smart_loader("data/casa/casa_card.json")
            # Word="casa",
            # Audio="[sound:casa.mp3]",
            # Image='<img src="casa.jpg">',
            # media_files=["../data/casa/casa.mp3", "../data/casa/casa.jpg"],
        )
        ankiobject.write_apkg("output.apkg")
    # HtmlLoader("meaning-pt_back.html").replace_includes_with_content()
