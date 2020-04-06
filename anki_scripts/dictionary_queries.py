import itertools
import re

import requests
from bs4 import BeautifulSoup

LINGUEE_API_BASE_URL = "https://linguee-api.herokuapp.com/api?q=%s&src=%s&dst=%s"
AUDIO_BASE_URL = "http://www.linguee.de/mp3/%s.mp3"

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'referrer': 'https://google.de',
}

linguee_headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/80.0.3987.162 Chrome/80.0.3987.162 Safari/537.36",
    "Referer": "https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query=",
    "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


def get_soup_object(url):
    return BeautifulSoup(requests.get(url, headers=headers).content, features="lxml")


languages = itertools.cycle(("de", "en", "es", "pt", "it", "fr", "el"))


def ask_once(qry_str, lang):
    print("start_query")
    data = requests.get(qry_str % lang)
    print(f"""Query to Linguee (to_lang:{lang}) returned status code {data.status_code}.""")
    return data.json() if data.status_code == 200 else None


def extract_info(response):
    try:
        match = response["exact_matches"][0]
    except KeyError or IndexError:
        print("Got no valid response.")
        return None
    audio_ids = {link["lang"]: link["url_part"] for link in match["audio_links"]}
    audio_url = AUDIO_BASE_URL % audio_ids["Brazilian Portuguese"]
    try:
        word_type = match["word_type"]["pos"]
    except KeyError:
        word_type = ""
    gender = match['word_type']['gender'][0] if word_type == 'noun' else ''
    translations = [entry["text"] for match in response["exact_matches"] for entry in match["translations"]]
    return translations, audio_url, word_type, gender


def ask(phrase, lang):
    phrase = phrase.replace(" ", "+")
    qry_str = LINGUEE_API_BASE_URL % (phrase, lang, "%s")
    return ask_once(qry_str, "de")


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
    bs = get_soup_object(f"https://www.dicio.com.br/pesquisa.php?q={phrase}/")
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
