from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        README = f.read()
    return README


setup(
    name='paperstack',
    version='1.2.1',
    description='A powerful, lightweight, universal bibliography management tool',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/williamroque/Paperstack',
    author='William Roque',
    author_email='william.aroque@gmail.com',
    license='GPL',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Database',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Utilities'
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'bibtexparser',
        'urwid',
        'pyperclip',
        'pymupdf',
        'beautifulsoup4',
        'citeproc-py'
    ],
    scripts = ['bin/paperstack'],
)
