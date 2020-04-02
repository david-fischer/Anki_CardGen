import itertools
import warnings

import requests

warnings.filterwarnings('ignore')

languages = itertools.cycle(("de", "en", "es", "pt", "it", "fr", "el"))


def ask_once(qry_str, lang, try_no, linguee_api_url):
    print("querying ... (Language: %s)" % lang)
    data = requests.get(linguee_api_url % (qry_str, lang))
    print(data.status_code)
    # print(data.json())
    if data.status_code == 200:
        # print(data.json())
        if data.json()["exact_matches"] is None:
            lang = next(languages)
            return ask_once(qry_str, lang, try_no + 1, linguee_api_url)
        return data.json()
    if data.status_code == 500:
        lang = next(languages)
        if try_no == 20:
            return {"exact_matches": None}
        else:
            return ask_once(qry_str, lang, try_no + 1, linguee_api_url)


def extract_info(response):
    if response["exact_matches"] is None:
        return None
    examples = []
    match = response["exact_matches"][0]
    audio_id = match["audio_links"][0]["url_part"]
    word_type = match["word_type"]["pos"]
    gender = match['word_type']['gender'][0] if word_type == 'noun' else ''
    real_ex = [x["src"] for x in response["real_examples"]]  # .sort(key = lambda s: len(s))
    for key in match["translations"]:
        try:
            examples.append(key["examples"][0]["source"])
        except IndexError:
            pass
    examples = list(set(examples))
    i = len(examples)
    for x in real_ex:
        if len(x) < 150:
            examples.append(x)
            i += 1
        if i == 3:
            break
    translations = [x["translations"] for x in response["exact_matches"]]
    translations = [[x["text"] for x in y] for y in translations]
    translation_string = "\n".join([", ".join(x) for x in translations])
    return translation_string, audio_id, word_type, gender, examples


def ask(qry_str, linguee_api_url):
    return ask_once(qry_str, "de", 0, linguee_api_url)
