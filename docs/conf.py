#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021, SERTIT-ICube - France, https://sertit.unistra.fr/
# This file is part of sertit-utils project
#     https://github.com/sertit/sertit-utils
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sertit

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = "3"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "myst_nb",
]
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
]

# Notebook integration parameters
jupyter_execute_notebooks = "cache"
execution_timeout = 3600

# This is going to generate a banner on top of each notebook
nbsphinx_prolog = ""

# sphinx-copybutton configurations
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Scan all found documents for autosummary directives, and to generate stub
# pages for each
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = {
#     '.rst': 'restructuredtext',
#     '.md': 'markdown',
# }

# The master toctree document.
master_doc = "index"

# General information about the project.
project = sertit.__title__
copyright = sertit.__copyright__[10:]
author = sertit.__author__

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = sertit.__version__
# The full version, including alpha/beta/rc tags.
release = version

today_fmt = "%Y-%m-%d"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "repository_url": sertit.__url__,
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": False,
    "repository_branch": "master",
    "path_to_docs": "docs",
    "use_download_button": False,
    "extra_navbar": "",
}

html_logo = "_static/sertit_utils.png"
html_title = ""

html_favicon = "_static/favicon.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.

html_show_sourcelink = False

html_last_updated_fmt = today_fmt

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "sertitdoc"

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "sertit_utils.tex",
        "Sertit-Utils Documentation",
        "ICube-SERTIT",
        "manual",
    )
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "sertit-utils", "Sertit-Utils Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "sertit-utils",
        "Sertit-Utils Documentation",
        author,
        "sertit-utils",
        "One line description of project.",
        "Miscellaneous",
    )
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "https://docs.python.org/3/": None,
    "https://docs.python-requests.org/en/master/": None,
}

add_function_parentheses = False
add_module_names = False


def _html_page_context(app, pagename, templatename, context, doctree):
    # Disable edit button for docstring generated pages
    if "generated" in pagename:
        context["theme_use_edit_page_button"] = False


def setup(app):
    """dummy docstring for pydocstyle"""
    app.connect("html-page-context", _html_page_context)
