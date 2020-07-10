import re
from collections import defaultdict
from pprint import pprint
from urllib.parse import quote

import attr
import pandas as pd
import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/56.0.2924.87 Safari/537.36",
    "referrer": "https://google.de",
}

REVERSO_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    # "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://google.com",
}

LINGUEE_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap "
    "Chromium/80.0.3987.162 "
    "Chrome/80.0.3987.162 Safari/537.36",
    "Referer": "https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query=",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
    "application/signed-exchange;v=b3;q=0.9",
    # "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


@attr.s
class Parser:
    phrase = attr.ib()
    from_lang = attr.ib()
    to_lang = attr.ib()
    base_url = attr.ib(default="")
    headers = attr.ib(default=DEFAULT_HEADERS)

    def setup(self):
        self.phrase = quote(self.phrase.replace(" ", "+"))

    def url(self):
        return self.base_url.format(**vars(self))

    def make_request(self, url=None):
        if url is None:
            url = self.url()
        return requests.get(url, headers=self.headers)

    def parse_response(self, response):
        """placeholder to implement in subclasses"""

    def result_dict(self, phrase=None):
        if phrase is not None:
            self.phrase = phrase
        self.setup()
        resp = self.make_request()
        # TODO: RAISE ERROR IF NECESSARY
        return self.parse_response(resp)


@attr.s
class LingueeParser(Parser):
    base_url = attr.ib(
        default="https://linguee-api.herokuapp.com/api?q={phrase}&src={from_lang}&dst={to_lang}"
    )
    lang_dict = {"pt": "Brazilian Portuguese"}
    audio_base_url = "https://www.linguee.de/mp3/%s.mp3"

    def parse_response(self, response):
        response = response.json()
        try:
            match = response["exact_matches"][0]
        except (TypeError, IndexError, KeyError):
            print("Got no valid response.")
            raise NoMatchError
        audio_ids = [
            link["url_part"]
            for mat in response["exact_matches"]
            for link in mat["audio_links"]
            if link["lang"] == self.lang_dict[self.from_lang]
        ]
        # audio_ids = {link["lang"]: link["url_part"] for link in match["audio_links"]}
        audio_url = self.audio_base_url % audio_ids[0] if audio_ids else ""
        word_type = match["word_type"]["pos"] if match["word_type"] else ""
        gender = match["word_type"]["gender"][0] if word_type == "noun" else ""
        translations = [
            entry["text"]
            for match in response["exact_matches"]
            for entry in match["translations"]
        ]
        return {
            "translations": translations,
            "word_type": word_type,
            "gender": gender,
            "audio_url": audio_url,
        }


@attr.s
class DicioParser(Parser):
    base_url = attr.ib("https://www.dicio.com.br/pesquisa.php?q={phrase}/")

    def setup(self):
        self.phrase = quote(self.phrase.replace(" ", "-"))

    def parse_response(self, response):
        bs = BeautifulSoup(response.content, "lxml")
        suggestion = bs.select("a._sugg")
        if suggestion:
            response = self.make_request(
                url=f'https://www.dicio.com.br{suggestion[0]["href"]}'
            )
            bs = BeautifulSoup(response.content, "lxml")
        explanations = [e.text for e in bs.select(".significado > span:not(.cl)")]
        examples = [
            [phrase.text.strip()]
            for phrase in bs.select(".tit-frases + .frases div.frase")
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
        conj_table_html = ""
        try:
            conj_table_df = self.conj_df(bs)
            conj_table_html = self.html_from_conj_df(conj_table_df)
        except:
            print("no conjugation table obtained :(")
        return {
            "explanations": explanations,
            "synonyms": synonyms,
            "antonyms": antonyms,
            "examples": examples,
            "add_info_dict": add_info_dict,
            "conj_table_html": conj_table_html,
        }

    def conj_df(self, bs_obj):
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

    def html_from_conj_df(self, conj_table_df):
        return "\n".join(
            [
                conj_table_df.to_html(
                    columns=[col],
                    classes="subj" if "Subjuntivo" in col else "ind",
                    index=False,
                )
                .replace("do Subjuntivo", "")
                .replace("do Indicativo", "")
                for col in conj_table_df
            ]
        )


@attr.s
class ReversoParser(Parser):
    base_url = attr.ib(default="https://context.reverso.net/{language_string}/{phrase}")
    lang_dict = {"pt": {"de": "traducao/portugues-alemao"}}
    language_string = None
    headers = REVERSO_HEADERS

    def setup(self):
        self.phrase = quote(self.phrase)
        self.language_string = self.lang_dict[self.from_lang][self.to_lang]

    def parse_response(self, response):
        bs = BeautifulSoup(response.content, features="lxml")
        # test = bs.select_one("div.example")
        # print(test.select_one("div.src").text.strip())
        return {
            "examples": [
                [
                    x.select_one("div.src").text.strip(),
                    x.select_one("div.trg").text.strip(),
                ]
                for x in bs.select("div.example")
            ]
        }


# BS4 Helper Functions


def get_element_after_regex(bs_obj, regex):
    match = bs_obj.body.find(text=re.compile(regex))
    if match is None:
        return BeautifulSoup(features="lxml")
    return match.parent.find_next()


def to_stripped_multiline_str(bs_obj):
    return "\n".join([line.strip() for line in bs_obj.text.strip().splitlines()])


# Error


class NoMatchError(Exception):
    def __init__(self, site=""):
        super(NoMatchError, self).__init__()
        self.site = site


def get_soup_object(url, headers=None):
    if headers is None:
        headers = DEFAULT_HEADERS
    return BeautifulSoup(requests.get(url, headers=headers).content, features="lxml")


def linguee_did_you_mean(search_term):
    bs = get_soup_object(
        f"https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query={search_term}",
        headers=LINGUEE_HEADERS,
    )
    return [element.text for element in bs.select("span.corrected")]


if __name__ == "__main__":
    TEST_WORD = ""
    # print(linguee_did_you_mean("comecar"))
    phrase = "começar"
    RP = ReversoParser(phrase=phrase, from_lang="pt", to_lang="de")
    DP = DicioParser(phrase=phrase, from_lang="pt", to_lang="de")
    LP = LingueeParser(phrase=phrase, from_lang="pt", to_lang="de")
    pprint(LP.result_dict())
