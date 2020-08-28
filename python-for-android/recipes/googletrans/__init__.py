from pythonforandroid.recipe import PythonRecipe


class GoogletransRecipe(PythonRecipe):
    version = "3.0.0"
    url = "https://files.pythonhosted.org/packages/71/3a/3b19effdd4c03958b90f40fe01c93de6d5280e03843cc5adf6956bfc9512/googletrans-{version}.tar.gz"

    call_hostpython_via_targetpython = False
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

    # depends = ['httpx==0.13.3', 'certifi==2020.4.5.2', 'chardet==3.0.4', 'hstspreload==2020.6.30', 'httpcore==0.9.1', 'h11==0.9.0', 'h2==3.2.0', 'hpack==3.0.0', 'hyperframe==5.2.0', 'sniffio==1.1.0', 'idna==2.9', 'rfc3986==1.4.0', 'sniffio==1.1.0']
    depends = [
        "setuptools",
        "httpx",
        "certifi",
        "chardet",
        "hstspreload",
        "httpcore",
        "h11",
        "h2",
        "hpack",
        "hyperframe",
        "sniffio",
        "idna",
        "rfc3986",
        "sniffio",
    ]


recipe = GoogletransRecipe()
