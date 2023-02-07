<h1 align="center">
<img src="logo.svg" width="600">
</h1><br>

Paperstack is a powerful, lightweight, universal bibliography management tool written in Python.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

Paperstack can be installed from PyPI with the following command.

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

to add a new paper. Note the syntax for entries ("key1: value1; key2: value2"). Then run

```sh
paperstack list
```

to list all added records in the library. To open the interactive interface, run `paperstack` by itself.

## Contributing

All contributions are welcome. Reporting issues on the GitHub repository is greatly appreciated, but pull requests are preferred. In particular, help is needed to:

- Improve documentation;
- Test on different platforms;
- Add support for new databases;
- Add support for new record types (books, websites, etc.);
- Add export types (HTML, MLA, APA, etc.);
- Any other goals or roadmap items listed in the [Project Notes](./notes.org).

Note that contributions should follow PEP 8 as closely as possible (though not strictly enforced), docstrings should follow the [Numpy format](https://numpydoc.readthedocs.io/en/latest/format.html), and that, in general, simple, flat, and scalable code is strongly encouraged.

## License

This program is licensed under the GNU General Public License.
