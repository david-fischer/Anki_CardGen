import itertools
import re

import requests
from bs4 import BeautifulSoup

LINGUEE_API_BASE_URL = "https://linguee-api.herokuapp.com/api?q=%s&src=%s&dst=%s"
AUDIO_BASE_URL = "http://www.linguee.de/mp3/%s.mp3"


def get_soup_object(url):
    return BeautifulSoup(requests.get(url).content, features="lxml")


languages = itertools.cycle(("de", "en", "es", "pt", "it", "fr", "el"))


def ask_once(qry_str, lang, try_no):
    # print("querying ... (Language: %s)" % lang)
    data = requests.get(qry_str % lang)
    # print(qry_str % lang)
    print(f"""Query to Linguee (to_lang:{lang}) returned status code {data.status_code}.""")
    if data.status_code == 200:
        if data.json()["exact_matches"] is None:
            lang = next(languages)
            return ask_once(qry_str, lang, try_no + 1)
        return data.json()
    if data.status_code == 500:
        lang = next(languages)
        if try_no == 20:
            return {"exact_matches": None}
        else:
            return ask_once(qry_str, lang, try_no + 1)


def extract_info(response):
    if response["exact_matches"] is None:
        return None
    examples = []
    match = response["exact_matches"][0]
    audio_ids = {link["lang"]: link["url_part"] for link in match["audio_links"]}
    audio_id = audio_ids["Brazilian Portuguese"]
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
    return translation_string, AUDIO_BASE_URL % audio_id, word_type, gender, examples


def ask(phrase, lang):
    phrase = phrase.replace(" ", "+")
    qry_str = LINGUEE_API_BASE_URL % (phrase, lang, "%s")
    return ask_once(qry_str, "de", 0)


def request_data_from_linguee(phrase, lang):
    return extract_info(ask(phrase, lang))


def get_element_after_regex(bs_obj, regex):
    match = bs_obj.body.find(text=re.compile(regex))
    if match is None:
        return BeautifulSoup(features="lxml")
    return match.parent.find_next()


def dict_from_bs_text(bs_obj):
    return_dict = {}
    if bs_obj is BeautifulSoup(features="lxml"):
        return return_dict
    for line in bs_obj.text.strip().splitlines():
        key, value = line.split(": ")
        return_dict[key.strip()] = value.strip()
    return return_dict


def span_not_cl(tag):
    return tag.get("class") is None and tag.name == "span"


def request_data_from_dicio(phrase):
    phrase = phrase.replace(" ", "-")
    bs = get_soup_object(f"https://www.dicio.com.br/{phrase}/")
    explanations = [e.text for e in get_element_after_regex(bs, "Significado.*").find_all(span_not_cl)]
    examples = [phrase.text.strip() for phrase in bs.find_all("div", {"class": "frase"})]
    synonyms = [syn.text for syn in get_element_after_regex(bs, ".*sinônimo.*").find_all("a")]
    antonyms = [syn.text for syn in get_element_after_regex(bs, ".*contrário.*").find_all("a")]
    add_info_dict = dict_from_bs_text(get_element_after_regex(bs, "Definição.*"))
    return explanations, synonyms, antonyms, examples, add_info_dict


def request_synonyms_from_wordref(word):
    """
    If possible, uses http://www.wordreference.com/sinonimos/ to find synonyms and returns as list.
    Returns None, when the response was empty.
    :param word:
    :return list_of_synonyms:
    """
    soup = get_soup_object("http://www.wordreference.com/sinonimos/%s" % word)
    try:
        return soup.find_all(class_="trans clickable")[0].find_all("li")[0].text.split(",")
    except IndexError:
        print("could not find synonyms :(")
        return []


if __name__ == "__main__":
    pass
    # tests here
