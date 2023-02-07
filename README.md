<h1 align="center">
<img src="https://raw.githubusercontent.com/williamroque/Paperstack/main/logo.svg" width="600">
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

The program can be used both through the CLI and an interactive text-based interface. Try running

```sh
paperstack add article 'author: Albert Einstein; title: Die Grundlage der allgemeinen Relativitätstheorie; journal: AdP; year: 1916'
```

to add a new paper. Note the syntax for entries (`key1: value1; key2: value2`). Then run

```sh
paperstack list
```

to list all added records in the library. To open the interactive interface, run `paperstack` by itself.

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

## Contributing

All contributions are welcome. Reporting issues on the GitHub repository is greatly appreciated, but pull requests are preferred. In particular, help is needed to:

- Improve documentation;
- Test on different platforms;
- Add support for new databases;
- Add support for new record types (books, websites, etc.);
- Add export types (HTML, MLA, APA, etc.);
- Any other goals or roadmap items listed in the [Project Notes](./notes.org).

Note that contributions should follow PEP 8 as closely as possible (though not strictly enforced), docstrings should follow the [Numpy format](https://numpydoc.readthedocs.io/en/latest/format.html), and that, in general, simple, flat, and scalable code is strongly encouraged.

A special thanks to [Dr. Mosenkov](https://physics.byu.edu/department/directory/mosenkov) for conceiving and co-creating this project.

## License

This program is licensed under the GNU General Public License.
