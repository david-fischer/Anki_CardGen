import os
import re

import attr
import bs4
import genanki

path = "/home/david/gen_ank/"


class CD:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


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
            del tag.attrs
            with open(src, "r") as file:
                tag.string = file.read()
        return str(soup)


def model_from_html(name, template_names, id, css_path):
    templates_html = {
        template_name:
            {
                "front": HtmlLoader(f"{template_name}_front.html"),
                "back":  HtmlLoader(f"{template_name}_back.html")
            } for template_name in template_names
    }
    fields = set()
    for _, temp_dict in templates_html.items():
        for _, side in temp_dict.items():
            fields |= side.set_of_fields()
    fields = [{"name": field} for field in sorted(fields, reverse=True)]

    templates = [{
        "name": temp_name,
        "qfmt": templates_html[temp_name]["front"].replace_includes_with_content(),
        "afmt": templates_html[temp_name]["back"].replace_includes_with_content(),
    } for temp_name in templates_html]

    with open(css_path, "r") as file:
        css = file.read()

    return genanki.Model(
        model_id=id,
        name=name,
        fields=fields,
        templates=templates,
        css=css,
    )


@attr.s
class AnkiObject:
    model_name = attr.ib(default="pt-word")
    templates = attr.ib(default=["meaning-pt", "pt-meaning"])
    deck_name = attr.ib(default="Portuguese::Vocab")
    css_path = attr.ib(default="pt.css")
    id = attr.ib(default=12345)

    def __attrs_post_init__(self):
        self.model = model_from_html(self.model_name,
                                     self.templates,
                                     css_path=self.css_path,
                                     id=self.id)
        self.deck = genanki.Deck(self.id, name=self.deck_name)
        self.package = genanki.Package(self.deck)
        self.fields = [
            field for field_dict in self.model.fields
            for _, field in field_dict.items()
        ]

    def add_note(self, media_file_dict=None, **kwargs):
        if media_file_dict is None:
            media_file_dict = {}
        fields = {
            field: (kwargs[field] if field in kwargs else "")
            for field in self.fields
        }
        new_note = genanki.Note(
            model=self.model,
            fields=fields,
        )
        for field, file in media_file_dict:
            self.package.media_files.append(file)
        self.deck.add_note(new_note)

    def write_apkg(self, out_path):
        self.package.write_to_file(out_path)


if __name__ == "__main__":
    ankiobject = AnkiObject()
    ankiobject.add_note(Word="test")
    ankiobject.write_apkg("output.apkg")
