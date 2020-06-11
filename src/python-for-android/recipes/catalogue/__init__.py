from pythonforandroid.recipe import CythonRecipe


class CatalogueRecipe(CythonRecipe):
    version = '2.0.0'
    url = 'https://files.pythonhosted.org/packages/c8/6e/067c2963303f4f069878f443c11d6b4f515370e50009f7d5a81b33d879d6/catalogue-{version}.tar.gz'

    call_hostpython_via_targetpython = False
    '''If True, tries to install the module using the hostpython binary
    copied to the target (normally arm) python build dir. However, this
    will fail if the module tries to import e.g. _io.so. Set this to False
    to call hostpython from its own build dir, installing the module in
    the right place via arguments to setup.py. However, this may not set
    the environment correctly and so False is not the default.'''

    #install_in_hostpython = False
    '''If True, additionally installs the module in the hostpython build
    dir. This will make it available to other recipes if
    call_hostpython_via_targetpython is False.
    '''

    #install_in_targetpython = True
    '''If True, installs the module in the targetpython installation dir.
    This is almost always what you want to do.'''

    # depends = ['importlib-metadata>=0.20; python_version < "3.8"']
    depends = ['importlib-metadata',"zipp","setuptools"]


recipe = CatalogueRecipe()
