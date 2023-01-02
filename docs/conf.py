# -*- coding: utf-8 -*-

import sys
import os
import re

sys.path.insert(0, os.path.abspath('../src'))

autodoc_mock_imports = ['numpy','psutil','matplotlib','cycler','reportlab']
autoclass_content = "init"

project = u'nvmetools'
slug = re.sub(r'\W+', '-', project.lower())
version = "0.4.1"
release = version
author = u'Joe Jones'
copyright = "2023 Joseph Jones"
language = 'en'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
source_suffix = '.rst'
exclude_patterns = []
locale_dirs = ['locale/']
gettext_compact = False
toc_object_entries = False

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'navigation_depth': 5,
}
html_context = {}

if not 'READTHEDOCS' in os.environ:
    html_static_path = ['_static/']
    html_js_files = ['debug.js']

html_show_sourcelink = True
htmlhelp_basename = slug


latex_documents = [
  ('index', '{0}.tex'.format(slug), project, author, 'manual'),
]

man_pages = [
    ('index', slug, project, [author], 1)
]

texinfo_documents = [
  ('index', slug, project, author, slug, project, 'Miscellaneous'),
]
