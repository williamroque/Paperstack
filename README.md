<h1 align="center">
<img src="https://raw.githubusercontent.com/williamroque/Paperstack/main/assets/logo.svg" width="600">
</h1><br>

[![PyPI version](https://badge.fury.io/py/paperstack.svg)](https://badge.fury.io/py/paperstack) [![GitHub version](https://badge.fury.io/gh/williamroque%2FPaperstack.svg)](https://badge.fury.io/gh/williamroque%2FPaperstack)

Paperstack is a powerful, lightweight, universal bibliography management tool written in Python.

- [GitHub repository](https://github.com/williamroque/Paperstack)

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

Paperstack can be installed from PyPI with the following command:

```sh
python3 -m pip install paperstack
```

To build directly from source, run:

```sh
git clone https://github.com/williamroque/Paperstack.git
cd Paperstack
python3 setup.py install
```

Afterwards, run the following command to test the installation and explore CLI options.

```sh
paperstack --help
```

## Usage

### Interface

Run `paperstack` by itself to open the interactive text-based interface. There, the left panel lists the records in your library (use arrow keys to navigate) and the right panel shows record details. Below, the footer displays key map hints and other messages.

<p align="center">
<img src="https://raw.githubusercontent.com/williamroque/Paperstack/main/assets/screenshot_1.png" width="800">
</p>

There is also a command-line interface, which can be useful for batch actions and integration with other programs. For example, run the command

```sh
paperstack add article 'author: Albert Einstein; title: Die Grundlage der allgemeinen Relativitätstheorie; journal: AdP; year: 1916'
```

to add a new paper. Note the syntax for entries (`key1: value1; key2: value2`). Then run

```sh
paperstack list
```

to list all added records in the library. A slightly less trivial use case might be to scrape multiple articles at once. The following script reads a list of bibcodes from a text file and uses Paperstack to add them to your library.

```sh
for line in $(cat bibcodes.txt); do
    paperstack scrape ads "bibcode: $line" --add
done
```

Configuration for Paperstack goes in `$HOME/.paperstack.cfg`. The config file follows a standard similar to Windows `.ini` files. Sections are labeled with `[section name]` and settings are written as `key = value`. Check the documentation for the different settings you can customize. Below is an example configuration.

```ini
[paths]
data = ~/Documents/Paperstack/

[article]
id-format = author@2-title@15-year@4

[ads]
key = <YOUR-API-KEY>
timeout = 10

[arxiv]
timeout = 10

[keys]
vim-bindings = yes

[editor]
command = nvim
```

Note that to scrape ADS, a valid API key has to be specified in the config file.

Find a presentation containing a few use cases and general information [here](https://raw.githubusercontent.com/williamroque/Paperstack/main/assets/Paperstack.pdf).

### Exporting

Paperstack supports exporting to both BibTeX and a variety of citation standards. In order to maintain a small installation size, however, only the Harvard citation style is enabled by default. To add more, visit [CSL Styles | GitHub](https://github.com/citation-style-language/styles) and download the `.csl` file corresponding to your preferred style. Then, save that file to the `csl` directory within the data directory specified in your configuration.

A few common styles you can download include:

* <a href="https://raw.githubusercontent.com/citation-style-language/styles/master/apa-6th-edition.csl" download>APA 6 | GitHub</a>
* <a href="https://raw.githubusercontent.com/citation-style-language/styles/master/modern-language-association.csl" download>MLA | GitHub</a>
* <a href="https://raw.githubusercontent.com/citation-style-language/styles/master/chicago-author-date.csl" download>Chicago | GitHub</a>

## Contributing

All contributions are welcome. Reporting issues on the GitHub repository is greatly appreciated, but pull requests are preferred. In particular, help is needed to:

- Improve documentation;
- Test on different platforms;
- Add support for new databases;
- Add support for new record types (books, websites, etc.);
- Any other goals or roadmap items listed in the [Project Notes](./notes.org).

Note that contributions should follow PEP 8 as closely as possible (though not strictly enforced), docstrings should follow the [Numpy format](https://numpydoc.readthedocs.io/en/latest/format.html), and that, in general, simple, flat, and scalable code is strongly encouraged.

A special thanks to [Dr. Mosenkov](https://physics.byu.edu/department/directory/mosenkov) for conceiving and co-creating this project.

## License

This program is licensed under the GNU General Public License.
