from ankisync.anki import Anki
with Anki(anki2_path="/home/david/.local/share/Anki2",account_name="Benutzer 1") as a:
    a.add_model(
        name='foo',
        fields=['field_a', 'field_b', 'field_c'],
        templates={
            'Forward': ("QUESTION1", "ANSWER1"),
            'Reverse': ("QUESTION2", "ANSWER2")
        }
    )