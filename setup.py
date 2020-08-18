import io
import os
import setuptools

here = os.path.abspath(os.path.dirname(__file__))


# TODO i need a brand new project name, papermate is a tablet and isnt that good


# Package information
NAME = 'papermate'
VERSION = "1.0.0"

DESCRIPTION = 'Random Scientific articles, on display'
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = '\n' + f.read()

# Contributor information
AUTHOR = 'Nolan Dickson'
CONTACT_EMAIL = 'ndickson@protonmail.com'

# Installation information
REQUIRED = ['feedparser']
REQUIRES_PYTHON = '>=3.7'

# setup parameters
setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',

    author=AUTHOR,
    author_email=CONTACT_EMAIL,

    install_requires=REQUIRED,
    python_requires=REQUIRES_PYTHON,

    scripts=['bin/papermate'],
    packages=['papermate'],
)
