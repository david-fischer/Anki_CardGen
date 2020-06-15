import re
from collections import defaultdict
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup

LINGUEE_API_BASE_URL = "https://linguee-api.herokuapp.com/api?q=%s&src=%s&dst=%s"
AUDIO_BASE_URL = "https://www.linguee.de/mp3/%s.mp3"

DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/56.0.2924.87 Safari/537.36",
    "referrer":   "https://google.de",
}

LINGUEE_HEADERS = {
    "user-agent":      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap "
                       "Chromium/80.0.3987.162 "
                       "Chrome/80.0.3987.162 Safari/537.36",
    "Referer":         "https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query=",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                       "application/signed-exchange;v=b3;q=0.9",
    # "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

REVERSO_HEADERS = {
    "user-agent":      "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    # "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://google.com",
}


# BS4 Helper Functions


def get_element_after_regex(bs_obj, regex):
    match = bs_obj.body.find(text=re.compile(regex))
    if match is None:
        return BeautifulSoup(features="lxml")
    return match.parent.find_next()


def to_stripped_multiline_str(bs_obj):
    return "\n".join([line.strip() for line in bs_obj.text.strip().splitlines()])


def span_not_cl(tag):
    return tag.get("class") is None and tag.name == "span"


# Error


class NoMatchError(Exception):
    def __init__(self, site=""):
        super(NoMatchError, self).__init__()
        self.site = site


def get_soup_object(url, headers=None):
    if headers is None:
        headers = DEFAULT_HEADERS
    return BeautifulSoup(requests.get(url, headers=headers).content, features="lxml")


# URLS


def linguee_api_url(phrase, from_lang, to_lang):
    phrase = phrase.replace(" ", "+")
    phrase = quote(phrase)
    return LINGUEE_API_BASE_URL % (phrase, from_lang, to_lang)


def dicio_url(phrase):
    phrase = phrase.replace(" ", "-")
    phrase = quote(phrase)
    return f"https://www.dicio.com.br/pesquisa.php?q={phrase}/"


def reverso_url(phrase, from_lang, to_lang):
    reverso_dict = {"pt": {"de": "traducao/portugues-alemao"}}
    phrase = quote(phrase)
    return f"https://context.reverso.net/{reverso_dict[from_lang][to_lang]}/{phrase}"


def parse_linguee_api_resp(response, from_lang):
    lang_dict = {"pt": "Brazilian Portuguese"}
    try:
        match = response["exact_matches"][0]
    except (TypeError, IndexError, KeyError):
        print("Got no valid response.")
        raise NoMatchError
    audio_ids = [
        link["url_part"]
        for mat in response["exact_matches"]
        for link in mat["audio_links"]
        if link["lang"] == lang_dict[from_lang]
    ]
    # audio_ids = {link["lang"]: link["url_part"] for link in match["audio_links"]}
    audio_url = AUDIO_BASE_URL % audio_ids[0] if audio_ids else ""
    word_type = match["word_type"]["pos"] if match["word_type"] else ""
    gender = match["word_type"]["gender"][0] if word_type == "noun" else ""
    translations = [
        entry["text"]
        for match in response["exact_matches"]
        for entry in match["translations"]
    ]
    return {
        "translations": translations,
        "word_type":    word_type,
        "gender":       gender,
        "audio_url":    audio_url,
    }


def dicio_conj_df(bs_obj):
    html_string = re.sub(r"(<a[^>]*>)", "", bs_obj.prettify())
    bs = BeautifulSoup(html_string, "lxml")
    conjugation_table_dict = defaultdict(dict)
    # the following [:2] only takes indicativo and subjuntivo
    temp_cols = [
        temp_col
        for modo_table in bs.select("div.modo")[:2]
        for temp_col in modo_table.find_next().select("li")
    ]
    for tempo_col in temp_cols:
        strings = list(tempo_col.stripped_strings)
        tempo = strings[0]
        verb_col = [
            [word.strip() for word in row.split(" ") if word.strip() != ""]
            for row in strings[1:]
        ]
        for row in verb_col:
            conjugation_table_dict[tempo][row[0]] = row[1]
    return pd.DataFrame.from_dict(conjugation_table_dict).loc[
        ["eu", "ele", "nós", "eles"]
    ]


# TODO: Check if unidecode was unnecessary
def parse_dicio_resp(response):
    bs = BeautifulSoup(response, "lxml")
    suggestion = bs.select("a._sugg")
    if suggestion:
        bs = get_soup_object(f'https://www.dicio.com.br{suggestion[0]["href"]}')
    explanations = [e.text for e in bs.select(".significado > span:not(.cl)")]
    examples = [
        [phrase.text.strip()] for phrase in bs.select(".tit-frases ~ .frases div.frase")
    ]
    synonyms = [
        [element.text] for element in bs.select('p:contains("sin").sinonimos a')
    ]
    antonyms = [
        [element.text] for element in bs.select('p:contains("contr").sinonimos a')
    ]
    add_info_dict = to_stripped_multiline_str(
        get_element_after_regex(bs, "Definição.*")
    )
    conj_table_df = pd.DataFrame()
    try:
        conj_table_df = dicio_conj_df(bs)
    except:
        print("no conjugation table obtained :(")
    return {
        "explanations":  explanations,
        "synonyms":      synonyms,
        "antonyms":      antonyms,
        "examples":      examples,
        "add_info_dict": add_info_dict,
        "conj_table_df": conj_table_df,
    }


def parse_reverso_resp(response):
    bs = BeautifulSoup(response, features="lxml")
    return {
        "examples": [
            [
                x.select_one("div.src").text.strip(),
                x.select_one("div.trg").text.strip(),
            ]
            for x in bs.select("div.example")
        ]
    }


def linguee_did_you_mean(search_term):
    bs = get_soup_object(
        f"https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query={search_term}",
        headers=LINGUEE_HEADERS,
    )
    return [element.text for element in bs.select("span.corrected")]


if __name__ == "__main__":
    print(linguee_did_you_mean("comecar"))
