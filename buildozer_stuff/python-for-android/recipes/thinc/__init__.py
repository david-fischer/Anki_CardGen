from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class ThincRecipe(CppCompiledComponentsPythonRecipe):
    version = "7.4.1"
    url = (
        "https://files.pythonhosted.org/packages/17/5d/4343b3a79565af88ba2d53818d97995c3c239288f2565b826865f376d271"
        "/thinc-{version}.tar.gz"
    )
    depends = ["setuptools"]
    call_hostpython_via_targetpython = False
    patches = ["remove_numpy_assert_allclose_import.patch"]


recipe = ThincRecipe()
