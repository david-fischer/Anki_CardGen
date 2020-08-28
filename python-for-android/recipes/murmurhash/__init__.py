from pythonforandroid.recipe import CythonRecipe


class MurmurhashRecipe(CythonRecipe):
    version = "1.0.2"
    url = "https://files.pythonhosted.org/packages/22/e9/411be1845f1ac07ae3bc40a4b19ba401819baed4fa63b4f5ef28b2300eb4/murmurhash-{version}.tar.gz"

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

    # depends = []
    depends = ["setuptools"]


recipe = MurmurhashRecipe()
