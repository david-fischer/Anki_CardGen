from pythonforandroid.recipe import PythonRecipe


class SrslyRecipe(PythonRecipe):
    version = '2.0.1'
    url = 'https://files.pythonhosted.org/packages/f4/0b/22c6caff32757e6c350dcaecf3a55f4df57e15c9a8eaa8c6db6f29b99b54' \
          '/srsly-{version}.tar.gz'
    depends = ["setuptools"]

recipe = SrslyRecipe()

