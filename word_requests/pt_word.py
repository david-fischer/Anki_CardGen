import os
import pickle
import re

import attr
import pandas as pd
from kivy.network.urlrequest import UrlRequest
from googletrans import Translator
from unidecode import unidecode

from google_images_download import google_images_download
from word_requests.urls_and_parsers import DEFAULT_HEADERS, dicio_url, linguee_api_url, parse_dicio_resp, \
    parse_linguee_api_resp, \
    parse_reverso_resp, REVERSO_HEADERS, reverso_url

FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}

translator = Translator()

def translate(string):
    return translator.translate(string,dest=TO_LANG,src=FROM_LANG).text


def html_list(str_list):
    """
    Returns a string, that is displayed as a list in HTML.
    :param str_list:
    :return:
    """
    start = "<ul>\n"
    end = "</ul>\n"
    middle = ["<li type=\"square\">" + item + "</li>\n" for item in str_list]
    return start + "".join(middle) + end


@attr.s
class Word:
    # query properties
    search_term = attr.ib(default="casa")
    data_dir = attr.ib(default="data")
    # word properties
    word_type = attr.ib(default="")  # verb noun etc
    gender = attr.ib(default="")
    examples = attr.ib(default=[])
    explanations = attr.ib(default=[])
    synonyms = attr.ib(default=[])
    antonyms = attr.ib(default=[])
    translations = attr.ib(default=[])
    trans_syns = attr.ib(default=[])
    image_urls = attr.ib(default=[])
    audio_url = attr.ib(default="")
    add_info_dict = attr.ib(default={})
    conj_table_df = attr.ib(default=pd.DataFrame())

    def search_term_utf8(self):
        return unidecode(self.search_term).lower()

    def folder(self):
        return self.search_term_utf8().replace(" ", "_")

    def request_data(self):
        self.__init__(search_term=self.search_term.strip().lower())
        resp_reverso = self.reverso_request(reverso_url(self.search_term, FROM_LANG, TO_LANG))
        resp_linguee = UrlRequest(linguee_api_url(self.search_term, FROM_LANG, TO_LANG),
                                  on_success=lambda req, res: self.update_from_dict(
                                      parse_linguee_api_resp(res, from_lang=FROM_LANG)),
                                  )
        resp_dicio = self.dicio_request(dicio_url(self.search_term))
        return [resp_dicio, resp_linguee, resp_reverso]

    def redirect_url(self, req):
        return "/".join(req.url.split("/")[:3]) + req.resp_headers["Location"]

    def reverso_request(self, url):
        return UrlRequest(url,
                          req_headers=REVERSO_HEADERS,
                          on_success=lambda req, res: self.update_from_dict(parse_reverso_resp(res)),
                          on_redirect=lambda req, res: self.reverso_request(self.redirect_url(req)).wait(),
                          on_error=print)

    def dicio_request(self, url):
        return UrlRequest(url,
                          req_headers=DEFAULT_HEADERS,
                          on_success=lambda req, res: self.update_from_dict(parse_dicio_resp(res)),
                          on_redirect=lambda req, res: self.dicio_request(self.redirect_url(req)).wait(),
                          on_error=print)

    def update_from_dict(self, dict):
        for key, value in dict.items():
            old_val = getattr(self, key)
            if type(old_val) is list:
                value = old_val + value
            setattr(self, key, value)

    def add_translations(self):
        for key in ["examples", "synonyms", "antonyms"]:
            values = getattr(self, key)
            for i, val in enumerate(values):
                if type(val) is str:
                    values[i] = [val, translate(val)]
                elif type(val) is list and len(val) == 1:
                    values[i] = [val[0], translate(val[0])]
            setattr(self, key, values)

    def request_img_urls(self, conn=None, keywords=None):
        """
        sets self.img_urls from first 20 results of google_images
        """
        keywords = self.search_term if keywords is None else keywords
        keywords = unidecode(keywords).lower()
        response = google_images_download.googleimagesdownload()
        arguments = {
            "keywords":         keywords,
            "output_directory": f"data/{self.folder()}",
            "no_directory":     True,
            "limit":            10,
            "format":           "jpg",
            "language":         LANGUAGE[FROM_LANG],
            "no_download":      True,
            "print_urls":       True,
            "prefix":           "img_",
            "save_source":      "source",
        }
        paths = response.download(arguments)[0][keywords]
        self.image_urls = paths
        if conn is None:
            return paths
        else:
            conn.send(paths)

    def html_from_conj_df(self):
        return "\n".join([
            self.conj_table_df.to_html(columns=[col],
                                       classes="subj" if "Subjuntivo" in col else "ind",
                                       index=False
                                       ).replace("do Subjuntivo", "").replace("do Indicativo", "")
            for col in self.conj_table_df
        ])

    def mark_examples(self):
        """
        Highlights the search_word in the example sentences using css.
        """
        for word in self.search_term.split(" "):
            self.examples = [re.sub(r'((?i)%s)' % word, r'<font color=red><b>\1</font></b>', ex) for ex in
                             self.examples]

    @classmethod
    def from_pickle(cls, path):
        with open(path, "rb") as file:
            return pickle.load(file)

    def pickle(self):
        if not os.path.exists(f"data/{self.folder()}"):
            os.makedirs(f"data/{self.folder()}")
        with open(f"data/{self.folder()}/{self.folder()}.p", "wb") as file:
            pickle.dump(self, file)

    def search(self, new_search_term):
        self.search_term = new_search_term
        path = f"{self.data_dir}/{self.folder()}/{self.folder()}.p"
        if os.path.exists(path):
            try:
                self.__init__(**vars(self.from_pickle(path)))
                return True
            except TypeError:
                pass
        requests = self.request_data()
        self.request_img_urls()
        for r in requests:
            r.wait()
        self.add_translations()
        self.pickle()


if __name__ == "__main__":
    q = Word(search_term="mesa")
    print(q)
    q.get_data()
    print(q)
