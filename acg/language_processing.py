"""Language processing."""

import re
import string

from kivymd.app import MDApp


def get_nlp(language):
    """Get NLP using spacy."""
    import spacy  # pylint: disable=import-outside-toplevel

    if language not in spacy.info()["Models"]:
        spacy.cli.download(language)
    return spacy.load(language)


try:
    NLP = get_nlp("pt")
except:  # pylint: disable=bare-except
    NLP = None
    print("COULD NOT FIND SPACY MODEL.")


def remove_punctuation(some_string):
    """Return string without punctuation and whitespace."""
    return some_string.strip(string.punctuation + string.whitespace + "”")


def join_lemmas(doc):
    """Return joined lemmas with appropriate whitespace."""
    return "".join(token.lemma_ + token.whitespace_ for token in doc)


def lemma_dict(phrases):
    """Return dictionary with original_phrase: lemmatized_phrase."""
    global NLP  # pylint: disable=global-statement
    if not NLP:
        return {phrase: phrase for phrase in phrases}
    language = getattr(MDApp.get_running_app(), "target_language", None)
    if language and NLP.lang != language:
        NLP = get_nlp(language)
    return {phrase: join_lemmas(NLP(phrase)) for phrase in phrases}


def clean_up(words, remove_punct=True, lower_case=True, lemmatize=True):
    """
    Preprocess a list of words (or phrases).

    Args:
      words: List of words
      remove_punct: If True, removes trailing and leading punctuation. (Default value = True)
      lower_case: If True, converts everything to lower case. (Default value = True)
      lemmatize: If True, tries to convert each word to its dictionary-form. (Default value = True)

    Returns:
        : List of processed words (or phrases).
    """
    if remove_punct:
        words = [word.strip(",.;:-–—!?¿¡\"'") for word in words]
    if lower_case:
        words = [word.lower() for word in words]
    if lemmatize:
        words = list(lemma_dict(words).values())
    return words


def tag_word_in_sentence(sentence, tag_word):
    """
    Use regex to wrap every derived form of a given ``tag_word`` in ``sentence`` in an html-tag.

    Args:
      sentence: String containing of multiple words.
      tag_word: Word that should be wrapped.

    Returns:
      : Sentence with replacements.
    """
    words = sentence.split()
    words = clean_up(words, lemmatize=False)
    # get unique, non-empty strings:
    words = [word for word in set(words) if word]
    lemmas = clean_up(words, lemmatize=True)
    tag_lemma = clean_up([tag_word])[0]
    words_found = [
        word
        for word, lemma in zip(words, lemmas)
        if lemma == tag_lemma or word == tag_word
    ]
    for word in words_found:
        sentence = re.sub(
            f"([^>])({word})([^<])",
            r'\1<span class="word">\2</span>\3',
            sentence,
            flags=re.IGNORECASE,
        )
    return sentence
