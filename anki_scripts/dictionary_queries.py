import itertools
import re
from collections import defaultdict

import pandas as pd
import requests
from bs4 import BeautifulSoup

LINGUEE_API_BASE_URL = "https://linguee-api.herokuapp.com/api?q=%s&src=%s&dst=%s"
AUDIO_BASE_URL = "http://www.linguee.de/mp3/%s.mp3"

DEFAULT_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36',
    'referrer': 'https://google.de',
}

linguee_headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/80.0.3987.162 "
                  "Chrome/80.0.3987.162 Safari/537.36",
    "Referer": "https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query=",
    "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

reverso_header = {
    "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://google.com",
}


def get_soup_object(url, headers=DEFAULT_HEADERS):
    return BeautifulSoup(requests.get(url, headers=headers).content, features="lxml")


languages = itertools.cycle(("de", "en", "es", "pt", "it", "fr", "el"))


def ask_once(qry_str, lang):
    print("start_query")
    data = requests.get(qry_str % lang)
    print(f"""Query to Linguee (to_lang:{lang}) returned status code {data.status_code}.""")
    return data.json() if data.status_code == 200 else None


class NoMatchError(Exception):
    pass


def extract_info(response):
    try:
        match = response["exact_matches"][0]
    except TypeError:
        print("Got no valid response.")
        raise NoMatchError
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


def to_stripped_multiline_str(bs_obj):
    return "\n".join([line.strip() for line in bs_obj.text.strip().splitlines()])


def span_not_cl(tag):
    return tag.get("class") is None and tag.name == "span"


def dicio_conj_df(bs_obj):
    html_string = re.sub(r"(<a[^>]*>)", "", bs_obj.prettify())
    bs = BeautifulSoup(html_string, "lxml")
    conjugation_table_dict = defaultdict(dict)
    # the following [:2] only takes indicativo and subjuntivo
    temp_cols = [temp_col for modo_table in bs.select("div.modo")[:2] for temp_col in
                 modo_table.find_next().select("li")]
    for tempo_col in temp_cols:
        strings = list(tempo_col.stripped_strings)
        tempo = strings[0]
        verb_col = [[word.strip() for word in row.split(" ") if word.strip() != ""] for row in strings[1:]]
        for row in verb_col:
            conjugation_table_dict[tempo][row[0]] = row[1]
    return pd.DataFrame.from_dict(conjugation_table_dict).loc[["eu", "ele", "nós", "eles"]]


def request_data_from_dicio(phrase):
    phrase = phrase.replace(" ", "-")
    bs = get_soup_object(f"https://www.dicio.com.br/pesquisa.php?q={phrase}/")
    explanations = [e.text for e in get_element_after_regex(bs, "Significado.*").find_all(span_not_cl)]
    examples = [phrase.text.strip() for phrase in bs.find_all("div", {"class": "frase"})]
    synonyms = [syn.text for syn in get_element_after_regex(bs, ".*sinônimo.*").find_all("a")]
    antonyms = [syn.text for syn in get_element_after_regex(bs, ".*contrário.*").find_all("a")]
    add_info_dict = to_stripped_multiline_str(get_element_after_regex(bs, "Definição.*"))
    conj_table_df = pd.DataFrame()
    try:
        conj_table_df = dicio_conj_df(bs)
    except:
        print("no conjugation table obtained :(")
    return explanations, synonyms, antonyms, examples, add_info_dict, conj_table_df


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


def request_examples_from_reverso(search_term):
    bs = get_soup_object(f'https://context.reverso.net/traducao/portugues-ingles/{search_term}',
                         headers=reverso_header)
    return [
        [
            x.find("div", {"class": "src ltr"}).text.strip(),
            x.find("div", {"class": "trg ltr"}).text.strip(),
        ]
        for x in bs.find_all("div", {"class": "example"})
    ]


def linguee_did_you_mean(search_term):
    bs = get_soup_object(
        f'https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query={search_term}',
        headers=linguee_headers)
    return [element.text for element in bs.select("span.corrected")]


if __name__ == "__main__":
    print(linguee_did_you_mean("comecar"))
