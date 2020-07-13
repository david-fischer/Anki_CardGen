# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

# sys.path.insert(0, '/home/david/coding/python/Anki_CardGen')
sys.path.append(os.path.abspath("sphinxext"))
sys.path.append(os.path.abspath("../../"))
sys.path.append(os.path.abspath(".."))

print(sys.path)

# -- Project information -----------------------------------------------------

project = "ACG"
copyright = "2020, David Fischer"
author = "David Fischer"

# The full version, including alpha/beta/rc tags
release = "0.3.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "kivy_lexer",
    "sphinx.ext.napoleon",
]
autoapi_type = "python"
autoapi_dirs = [".."]
autoapi_ignore = [
    f"*/{folder}/*"
    for folder in [
        ".buildozer",
        "apkgs",
        "app_state",
        "bin",
        "data",
        "docs",
        "google_image_download",
        "src",
        "test",
    ]
]
autoapi_generate_api_docs = True

autodoc_mock_imports = ["kivymd"]
autodoc_inherit_docstrings = False
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    #    'exclude-members':  "checked",  # "ObjectProperty,DictProperty",
    "show-inheritance": True,
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# InterSphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "kivy": ("https://kivy.org/doc/stable/", None),
    "kivymd": ("https://kivymd.readthedocs.io/en/0.104.1/", None),
}
