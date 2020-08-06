"""
This module provides different parsers (children of :class:`Parser`) to obtain the necessary data to fill Anki-Cards.

Each parser returns a dict, that can directly be used by the :meth:`pt_word.Word.update_from_dict` method of the
:class:`pt_word.Word`
class.
"""
import re
from collections import defaultdict
from pprint import pprint
from typing import Any, Dict
from urllib.parse import quote

import attr
import pandas as pd
import requests
import toolz
from bs4 import BeautifulSoup
from google_images_download import google_images_download

LANGUAGES = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}


DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/56.0.2924.87 Safari/537.36",
    "referrer": "https://google.de",
}
"""
Default headers for the :class:`Parser` class.
"""

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


@attr.s(auto_attribs=True)
class Parser:
    """Base class for parsers.

    Main functionality is the result_dict function.
    """

    phrase: str = ""
    """The word or phrase to search the site for."""
    from_lang: str = ""
    """Target language."""
    to_lang: str = ""
    """Source Language."""
    base_url = ""
    """
    URL to make request to. Can contain every class attribute.
    E.g. https://some.url/{phrase}/dest={from_lang};src={to_lang}.html
    """
    headers: dict = DEFAULT_HEADERS
    """Headers for the request. Defaults to :const:`DEFAULT_HEADERS`."""

    def setup(self):
        """Stuff that needs to be executed before :meth:`format_url_with_attribs` is called."""
        self.phrase = quote(self.phrase.replace(" ", "+"))

    def format_url_with_attribs(self, url=None):
        # TODO: Rewrite Doc-string
        """Get format_url_with_attribs for http-request.

        Returns:
          :  :attr:`base_url` formatted with all class attributes.
        """
        url = url or self.base_url
        return url.format(**vars(self))

    def make_request(self, url=None):
        """Use :attr:`headers` to make an http-request via :meth:`~requests.get`.

        Args:
          url: If None, will be set to :meth:`format_url_with_attribs`. (Default value = None)

        Returns:
          : :class:`~requests.Response` object

        """
        url = self.format_url_with_attribs(url)
        return requests.get(url, headers=self.headers)

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse :class:`requests.response` and return dict with result."""

    def result_dict(self, phrase=None):
        """Use :meth:`make_request` and :meth:`parse_request` to return dict with result."""
        if phrase is not None:
            self.phrase = phrase
        self.setup()
        resp = self.make_request()
        # TODO: RAISE ERROR IF NECESSARY
        return self.parse_response(resp)


@attr.s(auto_attribs=True)
class LingueeParser(Parser):
    """Use Linguee to obtain: translation, word_type, gender and audio_url."""

    base_url = (
        "https://linguee-api.herokuapp.com/api?q={phrase}&src={from_lang}&dst={to_lang}"
    )
    lang_dict = {"pt": "Brazilian Portuguese"}
    audio_base_url = "https://www.linguee.de/mp3/%s.mp3"

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Extract: translation, word_type, gender, audio_url."""
        response = response.json()
        print(response)
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
            "translation": translations,
            "word_type": word_type,
            "gender": gender,
            "audio": audio_url,
        }


@attr.s(auto_attribs=True)
class DicioParser(Parser):
    """Uses Dicio to obtain: explanations, synonyms, antonyms, examples, add_info_dict, conj_table_html."""

    base_url = "https://www.dicio.com.br/pesquisa.php?q={phrase}/"

    def setup(self):
        """Set up attributes."""
        self.phrase = quote(self.phrase.replace(" ", "-"))

    def parse_response(self, response):
        """Extract: explanations, synonyms, antonyms, examples, add_info_dict, conj_table_html."""
        bs = BeautifulSoup(response.content, "lxml")
        suggestion = bs.select("a._sugg")
        if suggestion:
            response = self.make_request(
                url=f'https://www.dicio.com.br{suggestion[0]["href"]}'
            )
            bs = BeautifulSoup(response.content, "lxml")
        explanations = [e.text for e in bs.select(".significado > span:not(.cl)")]
        examples = [
            phrase.text.strip()
            for phrase in bs.select(".tit-frases + .frases div.frase")
        ]
        synonyms = [
            element.text for element in bs.select('p:contains("sin").sinonimos a')
        ]
        antonyms = [
            element.text for element in bs.select('p:contains("contr").sinonimos a')
        ]
        add_info_dict = strip_multiline_str(get_element_after_regex(bs, "Definição.*"))
        conj_table_html = ""
        try:
            conj_table_df = self._conj_df(bs)
            conj_table_html = self._html_from_conj_df(conj_table_df)
        except KeyError:
            print("no conjugation table obtained :(")
        return {
            "explanation": explanations,
            "explanation_trans": [None for _ in explanations],
            "synonym": synonyms,
            "synonym_trans": [None for _ in synonyms],
            "antonym": antonyms,
            "antonym_trans": [None for _ in antonyms],
            "example": examples,
            "example_trans": [None for _ in examples],
            "add_info_dict": add_info_dict,
            "conj_table_html": conj_table_html,
        }

    @staticmethod
    def _conj_df(bs_obj):
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

    @staticmethod
    def _html_from_conj_df(conj_table_df):
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


@attr.s(auto_attribs=True)
class ReversoParser(Parser):
    """Use Reverso to obtain: examples."""

    base_url = "https://context.reverso.net/{language_string}/{phrase}"
    lang_dict = {"pt": {"de": "traducao/portugues-alemao"}}
    language_string = None
    headers = REVERSO_HEADERS

    def setup(self):
        """Set up attributes."""
        self.phrase = quote(self.phrase)
        self.language_string = self.lang_dict[self.from_lang][self.to_lang]

    def parse_response(self, response: requests.Response) -> Dict[str, list]:
        """Parse response and return dict of the form ``{"examples":[ [ex_src_lang, ex_trg_lang],...]]}``."""
        bs = BeautifulSoup(response.content, features="lxml")
        examples = bs.select("div.example")
        return {
            "example": [x.select_one("div.src").text.strip() for x in examples],
            "example_trans": [x.select_one("div.trg").text.strip() for x in examples],
        }


class GoogleImagesParser(Parser):
    """Uses google_images_download to get img_urls."""

    def result_dict(self, phrase=None):
        """Return dictionary of the form ``{"image":[url0,url1,...]}}``."""
        if phrase is not None:
            self.phrase = phrase
        self.setup()
        gid = google_images_download.googleimagesdownload()
        arguments = {
            "keywords": self.phrase,
            # "no_directory": True,
            "limit": 10,
            "format": "jpg",
            # "language": LANGUAGES[self.from_lang],
            "no_download": True,
            "print_urls": False,
            # "prefix": "img_",
        }
        paths = gid.download(arguments)[0][self.phrase]
        return {"image": paths}


# @attr.s(auto_attribs=True)
# class WikiParser(Parser):
#     base_url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
#     media_url = (
#         "https://en.wikipedia.org/api/rest_v1/page/media-list/{title}?redirect=true"
#     )
#     title = ""
#
#     def parse_response(self, response: requests.Response) -> Dict[str, Any]:
#         json_resp = response.json()
#         title = json_resp["title"]
#         summary = json_resp["extract"]
#         self.title = json_resp["titles"]["canonical"]
#         media_json_resp = self.make_request(self.media_url).json()
#         image = [
#             "https:" + item["srcset"][0]["src"]
#             for item in media_json_resp["items"]
#             if item["type"] == "image"
#         ]
#         return {"title": title, "summary": summary, "img_urls": image}


@attr.s(auto_attribs=True)
class RandTopicWikiParser(Parser):
    """Get title, summary and a list of image-urls for given random topic."""

    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/{page}"
    media_url = (
        "https://en.wikipedia.org/api/rest_v1/page/media-list/{title}?redirect=true"
    )
    page = ""
    title = ""

    def make_request(  # pylint: disable=arguments-differ
        self, url=None, tries=10, category=None
    ):
        """
        Call base method if url is set. Else obtain response from random wiki page.

        Because we only use content-pages and not category-pages ``try`` specifies how often we draw a random page.
        """
        if url:
            return super(RandTopicWikiParser, self).make_request(url=url)
        category = category or self.phrase
        for _ in range(tries):
            self.page = get_random_wiki_topic(category)
            resp = super(RandTopicWikiParser, self).make_request()
            if resp.status_code == 200:
                return resp
            print(resp.status_code, resp.content)
            # TODO: Error handling.
        raise NoMatchError(site="Wiki")

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Extract title, summary, image_urls and return in dict."""
        json_resp = response.json()
        title = json_resp["title"]
        summary = json_resp["extract"]
        self.title = json_resp["titles"]["canonical"]
        media_json_resp = self.make_request(url=self.media_url).json()
        if media_json_resp["items"]:
            image = [
                "https:" + item["srcset"][0]["src"]
                for item in media_json_resp["items"]
                if item["type"] == "image"
            ]
        else:
            image = []
        return {"title": title, "summary": summary, "image": image}


# BS4 Helper Functions


def get_element_after_regex(bs_obj, regex):
    """Get bs_object after element which text-attribute matches a given regex."""
    match = bs_obj.body.find(text=re.compile(regex))
    if match is None:
        return BeautifulSoup(features="lxml")
    return match.parent.find_next()


def strip_multiline_str(bs_obj):
    """Strip each line of a string of leading and trailing whitespace."""
    return "\n".join([line.strip() for line in bs_obj.text.strip().splitlines()])


# Error


class NoMatchError(Exception):
    """Error if no match can be found for the current search."""

    def __init__(self, site=""):
        super(NoMatchError, self).__init__()
        self.site = site


def linguee_did_you_mean(search_term):
    """
    Exctracts suggested corrections if the original search is not successful.

    Args:
      search_term: original search_term

    Returns:
        List of possible corrections for the original search_term.
    """
    response = requests.get(
        f"https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query={search_term}",
        headers=LINGUEE_HEADERS,
    )
    bs = BeautifulSoup(response.content, "lxml")
    return [element.text for element in bs.select("span.corrected")]


def star(func):
    """Wrapper-function. Call a function with unpacked arguments."""
    return lambda args: func(*args)


def json2list(filter_fn, map_fn, dictionary):
    """Filter and map dictionary in succession to obtain list."""
    filtered = toolz.itemfilter(star(filter_fn), dictionary)
    return toolz.itemmap(star(map_fn), filtered, factory=list)


def get_random_wiki_topic(category):
    """Return page-string for a random page in a category."""
    print(category)
    resp = requests.get(
        f"https://en.wikipedia.org/wiki/Special:RandomInCategory/{category}",
        allow_redirects=False,
    )
    page_string = resp.headers["Location"].split("/wiki/")[-1]
    page_string = re.sub("Category:", "", page_string)
    return page_string


if __name__ == "__main__":
    TEST_WORD = ""
    # print(linguee_did_you_mean("comecar"))
    PHRASE = "começar"
    RP = ReversoParser(phrase=PHRASE, from_lang="pt", to_lang="de")
    DP = DicioParser(phrase=PHRASE, from_lang="pt", to_lang="de")
    LP = LingueeParser(phrase=PHRASE, from_lang="pt", to_lang="de")
    WP = RandTopicWikiParser(phrase="animal_rights", from_lang="xx", to_lang="xx")
    pprint(WP.result_dict())
    # pprint(LP.result_dict())
