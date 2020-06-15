from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class SpacyRecipe(CppCompiledComponentsPythonRecipe):
    version = "2.2.4"
    url = "https://github.com/explosion/spaCy/archive/v{version}.tar.gz"
    call_hostpython_via_targetpython = False

    # depends = []
    depends = [
        "preshed",
        "thinc",
        "blis",
        "tqdm",
        "setuptools",
        "murmurhash",
        "numpy",
        "wasabi",
        "plac",
        "catalogue",
        "cymem",
        "requests",
        "srsly",
    ]

    site_packages_name = "spacy"


recipe = SpacyRecipe()
