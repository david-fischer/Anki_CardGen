from pythonforandroid.recipe import PythonRecipe


class AcgRecipe(PythonRecipe):
    version = "master"
    url = "https://api.github.com/repos/Rabtman/AcgClub/tarball/{version}"

    # call_hostpython_via_targetpython = True
    """If True, tries to install the module using the hostpython binary
    copied to the target (normally arm) python build dir. However, this
    will fail if the module tries to import e.g. _io.so. Set this to False
    to call hostpython from its own build dir, installing the module in
    the right place via arguments to setup.py. However, this may not set
    the environment correctly and so False is not the default."""

    # install_in_hostpython = False
    """If True, additionally installs the module in the hostpython build
    dir. This will make it available to other recipes if
    call_hostpython_via_targetpython is False.
    """

    # install_in_targetpython = True
    """If True, installs the module in the targetpython installation dir.
    This is almost always what you want to do."""

    # depends = ['setuptools==49.6.0.post20201009', 'python-dateutil', 'docutils', 'genanki', 'async-timeout', 'blis', 'cymem', 'pystache', 'pony', 'acg', 'hstspreload', 'httpx', 'Pygments', 'appdirs', 'bidict', 'frozendict', 'titlecase', 'kivymd', 'typing-extensions', 'Kivy', 'regex', 'preshed', 'toolz', 'yarl', 'pandas', 'certifi==2020.12.5', 'Pillow', 'googletrans', 'multidict', 'httpcore', 'hyperframe', 'requests', 'cached-property', 'thinc', 'spacy', 'murmurhash', 'srsly', 'aiohttp', 'Unidecode', 'soupsieve', 'pytz', 'sniffio', 'tqdm', 'urllib3', 'beautifulsoup4', 'six', 'rfc3986', 'wasabi', 'hpack', 'Kivy-Garden', 'lxml', 'h2', 'numpy', 'plac', 'PyYAML', 'catalogue', 'chardet', 'attrs', 'idna']
    depends = [
        "poetry",
        "setuptools",
        "python-dateutil",
        "docutils",
        "genanki",
        "async-timeout",
        "blis",
        "cymem",
        "pystache",
        "pony",
        "acg",
        "hstspreload",
        "httpx",
        "Pygments",
        "appdirs",
        "bidict",
        "frozendict",
        "titlecase",
        "kivymd",
        "typing-extensions",
        "Kivy",
        "regex",
        "preshed",
        "toolz",
        "yarl",
        "pandas",
        "certifi",
        "Pillow",
        "googletrans",
        "multidict",
        "httpcore",
        "hyperframe",
        "requests",
        "cached-property",
        "thinc",
        "spacy",
        "murmurhash",
        "srsly",
        "aiohttp",
        "Unidecode",
        "soupsieve",
        "pytz",
        "sniffio",
        "tqdm",
        "urllib3",
        "beautifulsoup4",
        "six",
        "rfc3986",
        "wasabi",
        "hpack",
        "Kivy-Garden",
        "lxml",
        "h2",
        "numpy",
        "plac",
        "PyYAML",
        "catalogue",
        "chardet",
        "attrs",
        "idna",
    ]


recipe = AcgRecipe()
