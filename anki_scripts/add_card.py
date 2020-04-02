import os

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


img_model = genanki.Model(
    1607392319,
    'Image',
    fields=[
        {'name': 'Word'},
        {'name': 'Sound'},
        {'name': 'Picture'},
        {'name': 'Synonyms'},
        {'name': 'Hint'},
        {'name': 'Example'},
        {'name': 'Explanation'}

    ],
    templates=[
        {
            'name': 'ES-IMG',
            'qfmt': '<font size="7" face="arial"> <center><b>{{Word}}</b> {{Sound}}</font><br />{{hint:Hint}}<br />',
            'afmt': """{{FrontSide}}
                <hr id="answer">
                <font size="4">
                <font color="blue"> <b>Sinónimo(s): </b> {{Synonyms}} </font><br />
                <br />
                {{Explanation}}
                <br />


                {{Picture}}<br />
                <b> Ejemplo(s):</b><br /> <em>{{Example}}</em>""",

        },
        {
            'name': 'IMG-ES',
            'qfmt': """<center>{{Picture}}<br />
                <font color="blue" size="4"> <b>Sinónimo(s): </b> {{Synonyms}} </font><br />
                {{Explanation}}<br />
                {{hint:Hint}}
                <br />""",
            # '<center>{{Picture}}<br />{{Synonyms}}<br />{{Example}}',
            'afmt': """{{FrontSide}}
                <hr id="answer">
                <font size="7" face="arial"> <center><b>{{Word}}</b> {{Sound}}</font><br />
                <font size="4">
                <b> Ejemplo(s):</b><br /> <em>{{Example}}</em></font>
                """,
            # '{{FrontSide}}<hr id="answer"><font size="6" face="arial"> <center><b>{{Word}}</b> {{Sound}}</font>',
        },
    ])

cloze_model = genanki.Model(
    1607392320,
    'Lückentext', fields=[{"name": "Text",
                           # "name": "Extra"
                           }], templates=[{"name": "Lückentext"}])

syn_model = genanki.Model(
    1607392318,
    'Synonyms',
    fields=[
        {'name': 'Word'},
        {'name': 'Sound'},
        {'name': 'Synonyms'}
    ],
    templates=[
        {
            'name': 'ES-Syn',
            'qfmt': '{{Word}} {{Sound}}',
            'afmt': '{{FrontSide}}<hr id="answer"> {{Synonyms}}',
        },

    ])


def add_image_card(word, file, synonyms, hint, examples):
    first_deck = genanki.Deck(1, "test_deck")
    my_package = genanki.Package(first_deck)
    with CD(path):
        if os.path.isfile("%s.mp3" % file):
            my_package.media_files.append("%s.mp3" % file)
            print("added %s.mp3" % file)
        else:
            print("Could not find Sound-File :(")
        if os.path.isfile("%s.jpg" % file):
            my_package.media_files.append("%s.jpg" % file)
            print("added %s.jpg" % file)

        else:
            print("Could not find Imgage-File  :(")
        my_note = genanki.Note(model=img_model, fields=[word,
                                                        "[sound:%s.mp3]" % file,
                                                        '<img src="%s.jpg">' % file,
                                                        synonyms,
                                                        hint,
                                                        examples, ""])

        first_deck.add_note(my_note)
        my_package.write_to_file("output.apkg")


def add_cloze_card(cloze_phrase):
    first_deck = genanki.Deck(1, "test_deck")
    my_package = genanki.Package(first_deck)
    my_note = genanki.Note(model=cloze_model, fields=[cloze_phrase])
    first_deck.add_note(my_note)
    my_package.write_to_file("output.apkg")

# first_deck.add_note(my_note)


# add_image_card("word","casarse","synonym","examples")

# my_package.write_to_file("output.apkg")
