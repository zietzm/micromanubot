# Micromanubot

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![image](https://img.shields.io/pypi/v/micromanubot)](https://pypi.python.org/pypi/micromanubot)
[![image](https://img.shields.io/pypi/l/micromanubot)](https://pypi.python.org/pypi/micromanubot)
[![image](https://img.shields.io/pypi/pyversions/micromanubot)](https://pypi.python.org/pypi/micromanubot)
[![Actions status](https://img.shields.io/github/actions/workflow/status/zietzm/micromanubot/python-app.yml?branch=main&label=actions)](https://github.com/zietzm/micromanubot/actions)

A build tool for academic manuscripts.

Lowering the friction to academic writing.
Opinionated but customizable.
[Cargo](https://doc.rust-lang.org/book/ch01-03-hello-cargo.html) for preprints.
A fraction of [Manubot](https://manubot.org/) in a self-contained, command-line tool.
All the flexibility of LaTeX, available immediately.

## Why Micromanubot?

* LaTeX based - flexible, extensible, fully-customizable
* Automatic citation management - cite using DOI directly
* Automatic image file management - provide images at URLs without manual downloads
* No LaTeX boilerplate fiddling - automatic authorship, metadata, and formatting.

## Usage

### Create a new manuscript

```bash
umb new my-manuscript
```

### Build the manuscript in the current directory

```bash
umb build
```

### Install TinyTex

```bash
umb install
```

Installs TinyTex into the `~/.umb/tinytex` directory.

### Help

For a full list of commands and arguments, add `--help` to any command.

```bash
umb --help
umb new --help
```

## Installation

```bash
pip install micromanubot
```

`pdflatex` and `bibtex` must be installed to produce PDF output.
Micromanubot includes an installer for TinyTex, a minimal version of LaTeX.
To install TinyTex, run

```bash
umb install
```

If you already have TeX installed and prefer to use the existing installation, simply do not run the above command.


## FAQ

#### Why not [manubot](https://manubot.org/)?

Manubot is the inspiration for this project.
Its selling point is Markdown manuscripts and web interfaces, though it can produce many different kinds of output, including DOCX and PDF.
Micromanubot is more focused---dealing only with LaTeX manuscripts and PDF output.
We believe that Micromanubot's simplified interface to LaTeX (no boilerplate!) provides most of the advantages of writing in Markdown while maintaining LaTeX's superior flexibility (especially for tables).

Manubot provides an alternative to preprint servers and traditional publishing, allowing users to serve nicely-formatted manuscripts online at no cost.
Micromanubot provides the simplest path to creating a manuscript or preprint locally.

Setting up a new manuscript should be as simple as possible.
It should be possible to go from producing the last figure of the analysis to typing in the manuscript within five seconds, and to produce a nicely-formatted PDF five seconds after that.
Micromanubot does not seek to replace Manubot (in fact, we use some of it internally!).
Instead, it seeks to provide a more lightweight alternative in the form of a command-line tool.

To create a new Manubot manuscript, the standard path is to clone the [rootstock]() repository and begin altering the manuscript content.
This leads to a repository that maintains all of the commits to the rootstock, making it harder to decipher who actually wrote the manuscript using GitHub.
On the other hand, Micromanubot creates a clean repository every time, using the simple command `umb new`.


#### Why not [Overleaf](https://overleaf.com)?

Overleaf is a collaborative online LaTeX editor, basically Google Docs for LaTeX.
We love Overleaf, and we use it regularly for manuscripts.
However, Overleaf can be a less ergonomic *starting point* for a new manuscript, especially if the initial writing is done by only one person.

One key feature we feel is missing from LaTeX/Overleaf is the ability to automatically pull content (e.g. images, citations) from the internet.
In Manubot, you can cite papers using `[@doi:10.1103/PhysRev.47.777]` and images using `![](https://example.com/figure.png)`.
In Micromanubot, you can do essentially the same thing, just in LaTeX.
A formatted LaTeX document is produced when you run `umb build`, and this pulls all citations and figures automatically.

Overall, we feel Overleaf is better for a mid-to-late-stage manuscript, but we prefer Micromanubot for initial writing.
The output of `umb build` is a perfect input to an Overleaf document, which is perfect for review and making final changes.

#### Why not just plain LaTeX?

Micromanubot is plain LaTeX, just with a (to our eyes) nicer interface.
Building a manuscript locally with plain LaTeX is like compiling a C++ project by typing `g++ -Wall ... file_a.cpp file_b.cpp main.cpp -o ...`.
Building a Micromanubot manuscript is like compiling a Rust project using `cargo build`.
It's ultimately doing a similar thing, but using the opinionated tool and structure makes the user interface so much nicer.
Ultimately, though, it's just a first step build tool.
You can always output a full LaTeX manuscript and compile it however you please.


## Possible future features

1. Citing using PubMedId (PMID)
2. Citing using [Manubot](https://github.com/manubot/manubot) itself
3. Improved templating (e.g. [Jinja2](https://palletsprojects.com/p/jinja/), [latexbuild](https://github.com/pappasam/latexbuild))
4. In-place modification of LaTeX, not just whole-document string replacements.
5. `clean` command to clear cache, etc.
6. Allow `install` command to install other packages.
