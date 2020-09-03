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
sys.path.append(os.path.abspath("../src/"))

print(sys.path)

# -- Project information -----------------------------------------------------

project = "Anki Card Gen"
copyright = "2020, David Fischer"
author = "David Fischer"

master_doc = "index"
# The full version, including alpha/beta/rc tags
release = "1.0.10"

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
autoapi_dirs = ["../acg"]
autoapi_ignore = [
    f"*{folder}/*"
    for folder in [
        "anki",
        "apkgs",
        "app_state",
        "words",
        "google_images_download",
        "python-for-android",
    ]
] + ["*/__init__.py"]
autoapi_member_order = "groupwise"
autoapi_generate_api_docs = False
# autoapi_add_toctree_entry = False

# autodoc_mock_imports = ["kivymd"]
# autodoc_inherit_docstrings = True
# autodoc_default_options = {
#     "members": True,
#     "member-order": "bysource",
#     "undoc-members": True,
#     #    'exclude-members':  "checked",  # "ObjectProperty,DictProperty",
#     "show-inheritance": True,
# }

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

pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = "alabaster"
html_theme = "sphinx_rtd_theme"

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
    "requests": ("https://requests.readthedocs.io/en/master/", None),
    "pony": ("https://docs.ponyorm.org", None),
}
