# setup.py

import os
from setuptools import setup, find_packages

def read_file(fname):
    "Read a local file"
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='jplugin',
    version='1.0.0',
    description='jplugin',
	long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    keywords='mkdocs python markdown',
    url='https://github.com/stuebersystems/mkdocs-img2fig-plugin',
    author='electroy',
    author_email='electroy@stueber.de',
	license='MIT',
	python_requires='>=3.5',
    install_requires=[
		'mkdocs'
	],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'jplugin = src:jplugin',
        ]
    }
)