import re
from collections import defaultdict

from bs4 import BeautifulSoup


def get_element_after_regex(bs_obj, regex):
    match = bs_obj.body.find(text=re.compile(regex))
    if match is None:
        return BeautifulSoup(features="lxml")
    return match.parent.find_next()


def get_conjugation_as_dict(bs_obj):
    conjugation_table_dict = defaultdict(lambda: defaultdict(dict))
    for modo in ["Indicativo", "Subjuntivo"]:
        for tempo_col in get_element_after_regex(bs_obj, modo).select("li"):
            strings = list(tempo_col.stripped_strings)
            tempo = strings[0]
            verb_col = [[word.strip() for word in row.split(" ") if word.strip() != ""] for row in strings[1:]]
            for row in verb_col:
                conjugation_table_dict[modo][tempo][row[0]] = row[1]
    return conjugation_table_dict


def table_row(person, verb_forms):
    n = "\n"
    return f"""
       <div class="divTableRow">
         <div class="divTableCell divPerson">{person}</div>
         {n.join([f'<div class="divTableCell">{v}</div>' for v in verb_forms])}
       </div>
"""


# Unfortunately Imperative has no "eu", so method fails
def html_table_from_single_modo(modo_dict):
    n = "\n"
    pronom = ["eu", "ele", "nós", "eles"]
    html_table = f"""<div class="divTable">
            <div class="divTableBody">
              <div class="divTableRow divHeader sans">
                <div class="divTableCell"></div>
{n.join([f'<div class="divTableCell">{header}</div>' for header in modo_dict.keys()])}
              </div>
        {n.join([table_row(p, [
        modo_dict[tempo][p] for tempo in modo_dict
    ]) for p in pronom])}
              <div class="divTableRow">
                <div class="divTableCell divPerson">eu</div>
                <div class="divTableCell">começo</div>
                <div class="divTableCell">comecei</div>
              </div>
            </div>
          </div>
        """
    return str(BeautifulSoup(html_table, "html.parser"))


def conj_htmltable_from_html(bs_obj):
    html_string = re.sub(r"(do Subjuntivo|do Indicativo|<a[^>]*>)", "", bs_obj.prettify())
    bs = BeautifulSoup(html_string, "lxml")
    conj_dict = get_conjugation_as_dict(bs)
    return "\n".join(
        [
            f"<div> {modo}</div>\n"
            + html_table_from_single_modo(conj_dict[modo])
            for modo in conj_dict
        ])


if __name__ =="__main__":
    import requests
    def get_soup_object(url):
        return BeautifulSoup(requests.get(url).content, features="lxml")

    bs = get_soup_object("https://www.dicio.com.br/comecar/")
    print(conj_htmltable_from_html(bs))
