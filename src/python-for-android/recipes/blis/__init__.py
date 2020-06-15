from pythonforandroid.recipe import (
    CppCompiledComponentsPythonRecipe,
    current_directory,
    shprint,
)
import sh


class BlisRecipe(CppCompiledComponentsPythonRecipe):
    version = "0.4.1"
    url = "https://github.com/explosion/cython-blis/archive/master.zip"

    # setup_extra_args = []
    # call_hostpython_via_targetpython = False
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

    # depends = ['numpy>=1.15.0']
    depends = ["numpy", "setuptools"]

    # def get_recipe_env(self,*args,**kwargs):
    # env = super(BlisRecipe, self).get_recipe_env(*args,**kwargs)
    # env["BLIS_ARCH"] = "generic"
    # return env

    # def build_arch(self,arch):
    #    with current_directory(self.get_build_dir(arch.arch)):
    #        shprint(sh.ls)
    #        make_json = sh.Command("./bin/generate-make-jsonl")
    #        make_json("linux","cortexa9")
    #    super(BlisRecipe, self).prebuild_arch(arch)


recipe = BlisRecipe()
