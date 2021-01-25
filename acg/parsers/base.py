"""
This module provides different parsers (children of :class:`Parser`) to obtain the necessary data to fill Anki-Cards.

Each parser returns a dict, that can directly be used by the :meth:`pt_word.Word.update_from_dict` method of the
:class:`pt_word.Word`
class.
"""
import asyncio
import re
from collections import defaultdict
from pprint import pprint
from typing import Any, Dict
from urllib.parse import quote

import attr
import pandas as pd
import requests
import unidecode
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from utils import async_get_results

from ..google_images_download import google_images_download
from ..utils import remove_whitespace

LANGUAGES = {"pt": "portuguese", "de": "german", "en": "english", "es": "spanish"}


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


class NoMatchError(Exception):
    """Error if no match can be found for the current search."""

    def __init__(self, site=""):
        super().__init__()
        self.site = site


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
            return super().make_request(url=url)
        category = category or self.phrase
        for _ in range(tries):
            self.page = get_random_wiki_topic(category)
            resp = super().make_request()
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


@attr.s(auto_attribs=True)
class AsyncParser:
    """Base-Class for asynchronous parsers."""

    base_url: str = None
    phrase: str = None
    request_kwargs: dict = None
    headers: dict = DEFAULT_HEADERS
    from_lang: str = None
    to_lang: str = None

    @staticmethod
    def format_str(some_str):
        """Replace spaces and special characters."""
        return quote(some_str.replace(" ", "+"))

    def url(self, url=None):
        """Return url for request."""
        url = url or self.base_url
        format_dict = {
            key: self.format_str(val)
            for key, val in vars(self).items()
            if isinstance(val, str)
        }
        formatted_url = url.format(**format_dict)
        return formatted_url

    def request_params(self):  # pylint: disable=no-self-use
        """Return request-params."""
        return {}

    async def request(self, url=None, request_params=None):
        """Make http-request using :package:`aiohttp`."""
        url = url or self.url
        url = url() if callable(url) else url
        params = request_params or self.request_params()
        async with ClientSession() as session:
            async with session.get(
                url, params=params, headers=self.headers
            ) as response:
                if response.status != 200:
                    raise NoMatchError
                if "html" in response.content_type:
                    return await response.text()
                if "json" in response.content_type:
                    return await response.json()

    def parse_response(  # pylint: disable=no-self-use,unused-argument
        self, response: dict or list or str
    ) -> Dict[str, list]:
        """Placeholder-function."""
        return {}

    async def __call__(self, phrase):
        """Return results asynchronously."""
        self.phrase = phrase
        response = await self.request()
        return self.parse_response(response)

    def result_dict(self, phrase):
        """Return results synchronously."""
        return asyncio.run(self(phrase))


@attr.s(auto_attribs=True)
class AsyncReverso(AsyncParser):
    """Use Reverso to obtain: examples."""

    headers: dict = REVERSO_HEADERS

    def url(self, url=None):
        """Set up attributes."""
        url = url or (
            f"https://context.reverso.net/translation/"
            f"{LANGUAGES[self.from_lang]}-{LANGUAGES[self.to_lang]}/"
            "{phrase}"
        )
        return super().url(url=url)

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Parse response and return dict of the form ``{"examples":[ [ex_src_lang, ex_trg_lang],...]]}``."""
        bs = BeautifulSoup(response, features="lxml")
        examples = bs.select("div.example")
        return {
            "example": [x.select_one("div.src").text.strip() for x in examples],
            "example_trans": [x.select_one("div.trg").text.strip() for x in examples],
        }


@attr.s(auto_attribs=True)
class AsyncLinguee(AsyncParser):
    """Get translation, word_type, gender, audio from Linguee."""

    base_url: str = "https://linguee-api.herokuapp.com/api"
    lang_dict = {"pt": "Brazilian Portuguese", "en": "American English"}
    audio_base_url = "https://www.linguee.de/mp3/%s.mp3"

    def request_params(self):
        """Return request params."""
        return {"q": self.phrase, "src": self.from_lang, "dst": self.to_lang}

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Extract: translation, word_type, gender, audio_url."""
        print(response)
        try:
            match = response["exact_matches"][0]
        except (TypeError, IndexError, KeyError) as error:
            print("Got no valid response.")
            raise NoMatchError from error
        audio_ids = [
            link["url_part"]
            for mat in response["exact_matches"]
            for link in mat["audio_links"]
            if link["lang"] == self.lang_dict[self.from_lang]
        ]
        audio_url = self.audio_base_url % audio_ids[0] if audio_ids else ""
        word_type = match["word_type"]["pos"] if match["word_type"] else ""
        gender = (
            match["word_type"]["gender"][0]
            if word_type == "noun" and "gender" in match["word_type"]
            else ""
        )
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
class AsyncDicio(AsyncParser):
    """Uses Dicio to obtain: explanations, synonyms, antonyms, examples, add_info_dict, conj_table_html."""

    base_url: str = "https://www.dicio.com.br/pesquisa.php"

    def request_params(self):
        """Return request params."""
        return {"q": self.phrase}

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Extract: explanations, synonyms, antonyms, examples, add_info_dict, conj_table_html."""
        bs = BeautifulSoup(response, "lxml")
        suggestion = bs.select("a._sugg")
        if suggestion:
            response = requests.get(
                url=f'https://www.dicio.com.br{suggestion[0]["href"]}'
            )
            bs = BeautifulSoup(response.content, "lxml")
        explanations = [e.text for e in bs.select(".significado > span:not(.cl)")]
        examples = [
            phrase.text.strip()
            for phrase in bs.select(".tit-frases + .frases div.frase")
        ]
        synonyms = [
            element.text
            for element in bs.select('p.sinonimos:-soup-contains-own("sin") a')
        ]
        antonyms = [
            element.text
            for element in bs.select('p.sinonimos:-soup-contains-own("contr") a')
        ]
        add_info_dict = remove_whitespace(
            bs.select("h2.tit-section + p.adicional")[0].text
        )
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
            "additional_info": add_info_dict,
            "conjugation_table": conj_table_html,
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
class AsyncGoogleImages(AsyncParser):
    """Uses google_images_download to get img_urls."""

    limit: int = 15
    gid: google_images_download.googleimagesdownload = None

    def __attrs_post_init__(self):
        self.gid = google_images_download.googleimagesdownload()

    async def __call__(self, phrase=None):
        """Return dictionary of the form ``{"image":[url0,url1,...]}}``."""
        if phrase is not None:
            self.phrase = unidecode.unidecode(phrase)
        arguments = {
            "keywords": self.phrase,
            "limit": self.limit,
            "format": "jpg",
            "language": LANGUAGES[self.from_lang].capitalize(),
            "no_download": True,
            "print_urls": False,
        }
        paths = self.gid.download(arguments)[0][self.phrase]
        return {"image": paths}


def linguee_did_you_mean(search_term):
    """Extract suggested corrections if the original search is not successful."""
    # TODO: generalize to different languages
    response = requests.get(
        f"https://www.linguee.de/deutsch-portugiesisch/search?source=portugiesisch&query={search_term}",
        headers=LINGUEE_HEADERS,
    )
    bs = BeautifulSoup(response.content, "lxml")
    return [element.text for element in bs.select("span.corrected")]


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
    PHRASE = "cão"
    ap = AsyncReverso(from_lang="pt", to_lang="de")
    al = AsyncLinguee(from_lang="pt", to_lang="de")
    ad = AsyncDicio()
    ag = AsyncGoogleImages(from_lang="pt")
    async_parsers = [ad, al, ap, ag]

    pprint(async_get_results(async_parsers, PHRASE))
