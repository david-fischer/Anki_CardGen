from pythonforandroid.recipe import CythonRecipe


class CymemRecipe(CythonRecipe):
    version = '2.0.3'
    url = 'https://files.pythonhosted.org/packages/ce/8d/d095bbb109a004351c85c83bc853782fc27692693b305dd7b170c36a1262/cymem-{version}.tar.gz'

    #call_hostpython_via_targetpython = False
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

    # depends = []
    depends = []


recipe = CymemRecipe()