from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class SpacyRecipe(CppCompiledComponentsPythonRecipe):
    version = "2.3.0"
    url = "https://files.pythonhosted.org/packages/63/04/9309749d00a44447c9e93510a3ccb21a37a36a23dbe8b35d09d4d2110094/spacy-2.3.0.tar.gz"

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

    # depends = ['tqdm==4.46.0', 'plac==1.1.3', 'murmurhash==1.0.2', 'srsly==1.0.2', 'blis==0.4.1', 'certifi==2020.6.20', 'setuptools==47.1.1.post20200529', 'catalogue==1.0.0', 'idna==2.9', 'numpy', 'cymem==2.0.3', 'thinc==7.4.1', 'preshed==3.0.2', 'wasabi==0.6.0', 'importlib-metadata==1.6.0', 'zipp==3.1.0', 'requests==2.23.0', 'chardet==3.0.4']
    depends = [
        "tqdm",
        "plac",
        "murmurhash",
        "srsly",
        "blis",
        "certifi",
        "setuptools",
        "catalogue",
        "idna",
        "numpy",
        "cymem",
        "thinc",
        "preshed",
        "wasabi",
        "importlib-metadata",
        "zipp",
        "requests",
        "chardet",
    ]


recipe = SpacyRecipe()
