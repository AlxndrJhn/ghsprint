from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='ghsprint',
    packages=['ghsprint'],
    version='0.5',
    license='GNU GPLv3',
    description='Contains utilities for agile sprints that use the GitHub platform.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Alexander Jahn',
    author_email='jahn.alexander@gmail.com',
    url='https://github.com/AlxndrJhn/ghsprint',
    download_url='https://github.com/AlxndrJhn/ghsprint/archive/0.5.tar.gz',
    keywords=['GitHub', 'utilities', 'reporting', 'sprint'],
    install_requires=[
        'requests',
        'urllib3',
        'rake-nltk',
        'tqdm',
        'click',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Utilities',

        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

    ],
)
