from distutils.core import setup
setup(
    name='ghsprint',
    packages=['ghsprint'],
    version='0.1',
    license='GNU GPLv3',
    description='Contains utilities for agile sprints that use the GitHub platform.',
    author='Alexander Jahn',
    author_email='jahn.alexander@gmail.com',
    url='https://github.com/AlxndrJhn/ghsprint',
    download_url='https://github.com/AlxndrJhn/ghsprint/archive/0.1.tar.gz',
    keywords=['GitHub', 'utilities', 'reporting', 'sprint'],
    install_requires=[
        'requests',
        'urllib3',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: GNU General Public License v3 (GPL-3)',

        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

    ],
)
