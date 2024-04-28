from __future__ import annotations

import importlib.resources
import os
import pathlib
import re
import shlex
import shutil
import subprocess
from typing import Type, TypeVar

import bibtexparser
import pylatexenc.latexwalker
import rich.progress
from pylatexenc.latexwalker import LatexEnvironmentNode, LatexMacroNode

import micromanubot.cite
import micromanubot.config
import micromanubot.figures
import micromanubot.install


def is_umb_project(root_dir: pathlib.Path) -> bool:
    """Check if a directory is a valid micromanubot project."""
    return (
        root_dir.joinpath("umb.toml").exists()
        and root_dir.joinpath("content").exists()
        and root_dir.joinpath(".umb").exists()
    )


def setup_build_directory(root_dir: pathlib.Path) -> None:
    """Setup the `build` directory and `assets`/`images` subdirectories."""
    build_dir = root_dir.joinpath("build")
    build_dir.mkdir(exist_ok=True)
    for child in build_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    build_dir.joinpath("images").mkdir()
    assets_path = root_dir.joinpath("assets")
    for asset in assets_path.iterdir():
        shutil.copy(asset, build_dir)


def build_latex(root_dir: pathlib.Path) -> None:
    """Build the LaTeX manuscript.

    1. Figure out what main files exist in the `content` directory.
    2. Load, parse, and process the main files, then write to `build`.
    3. Load the template `main.tex` file, parse, process and write to `build`.
    4. Gather citations and write to `.umb` and `build`.
    5. Gather figures and write to `build/images`.
    """
    build_dir = root_dir.joinpath("build")
    shutil.copy(root_dir.joinpath("content/imports.tex"), build_dir)
    main_files = find_manuscript_files(root_dir)

    bib = micromanubot.cite.Bibliography(
        cache_path=root_dir.joinpath(".umb/citations_cache.bib"),
        manual_path=root_dir.joinpath("content/manual_references.bib"),
    )
    fig = micromanubot.figures.ManuscriptFigures(
        cache_path=root_dir.joinpath(".umb"),
        manual_path=root_dir.joinpath("content").joinpath("images"),
    )

    built_main_files = list()
    for file in main_files:
        output_path = build_dir.joinpath(file.name)
        ManuscriptSection.read_tex(file).process(bib, fig).write(output_path)
        if file.name[0].isdigit():
            built_main_files.append(output_path)

    bib_path = build_dir.joinpath("references.bib")
    bib_library = bib.reconcile_citations()
    bibtexparser.write_file(str(bib_path), bib_library)
    fig.reconcile_figures(build_dir)

    metadata = micromanubot.config.Metadata.read_toml(root_dir.joinpath("umb.toml"))
    build_files = importlib.resources.files("micromanubot.template_data.build")
    template_path = build_files.joinpath("main.tex")
    with importlib.resources.as_file(template_path) as file:
        (
            MainTemplate.read_tex(file)
            .process(metadata, built_main_files)
            .write(root_dir.joinpath("build", "main.tex"))
        )

    return None


def build_latex_pdf(root_dir: pathlib.Path) -> None:
    """Compile the built LaTeX manuscript to a PDF."""
    build_dir = root_dir.joinpath("build")
    pdflatex = micromanubot.install.find_pdflatex().as_posix()
    bibtex = micromanubot.install.find_bibtex().as_posix()
    commands = [
        f"{pdflatex} -interaction=nonstopmode main",
        f"{bibtex} main",
        f"{pdflatex} -interaction=nonstopmode main",
        f"{pdflatex} -interaction=nonstopmode main",
    ]
    # Set the SOURCE_DATE_EPOCH environment variable to 0 to ensure reproducible
    # builds. For more info, see https://tex.stackexchange.com/q/229605 and
    # https://reproducible-builds.org/specs/source-date-epoch
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "0"
    for command in rich.progress.track(commands, description="Compiling LaTeX"):
        command_args = shlex.split(command)
        result = subprocess.run(
            command_args, cwd=build_dir, capture_output=True, env=env
        )
        if result.returncode != 0:
            raise ValueError(
                f"Error compiling LaTeX: {command}.",
                result.returncode,
                result.stdout,
                result.stderr,
            )


def find_manuscript_files(root_dir: pathlib.Path) -> list[pathlib.Path]:
    """Find the main files in the content directory.

    These include the main manuscript files (e.g. `1-introduction.tex`) and
    the abstract and supplement files, if they exist.
    """
    main_files = sorted(root_dir.joinpath("content").glob("[0-9]*.tex"))
    if not main_files:
        raise ValueError("No main files found in the content directory.")

    abstract_path = root_dir.joinpath("content").joinpath("abstract.tex")
    if abstract_path.exists():
        main_files.insert(0, abstract_path)

    supplement_path = root_dir.joinpath("content").joinpath("supplement.tex")
    if supplement_path.exists():
        main_files.append(supplement_path)

    return main_files


T = TypeVar("T", bound="ManuscriptFile")


class ManuscriptFile:
    def __init__(self, raw_content: str) -> None:
        self.raw_content = raw_content
        self.fmt_content: str | None = None

    @classmethod
    def read_tex(cls: Type[T], path: pathlib.Path) -> T:
        with open(path, "r") as f:
            raw_content = f.read()

        return cls(raw_content)

    def write(self, path: pathlib.Path) -> None:
        """Write the processed content to a file."""
        if self.fmt_content is None:
            raise ValueError("The content has not been processed yet.")

        with open(path, "w") as f:
            f.write(self.fmt_content)


class ManuscriptSection(ManuscriptFile):
    """A class to represent a manuscript main text file.

    These are files that just contain section content (i.e. text/tables/figures),
    and should not be self-contained LaTeX documents. They will be included in
    the main LaTeX document via the `input` command after processing.
    """

    def process(
        self,
        bib: micromanubot.cite.Bibliography,
        fig: micromanubot.figures.ManuscriptFigures,
    ) -> ManuscriptSection:
        walker = pylatexenc.latexwalker.LatexWalker(self.raw_content)
        nodelist, _, _ = walker.get_latex_nodes()

        for node in nodelist:
            if isinstance(node, LatexMacroNode) and node.macroname == "cite":
                bib.parse_node(node)
            elif (
                isinstance(node, LatexEnvironmentNode)
                and node.environmentname == "figure"
            ):
                fig.parse_node(node)

        self.fmt_content = self.raw_content
        keys_to_replace = [key for key in bib.unique_keys if "@" in key]
        for key in keys_to_replace:
            self.fmt_content = self.fmt_content.replace(key, key.lstrip("@"))

        for ref, alias in fig.reference_to_alias.items():
            self.fmt_content = self.fmt_content.replace(ref, alias)

        return self


class MainTemplate(ManuscriptFile):
    """A class to represent the main LaTeX file (a template).

    All other manuscript files will be processed and inserted into this template
    using the `input` command. The processed template will be written to
    `build/main.tex`.

    Current templating is very crude, using `@name` to replace `name`. Could
    imagine using something like Jinja2 in the future. For example,
    https://github.com/pappasam/latexbuild.
    """

    def __init__(self, raw_content: str) -> None:
        self.raw_content = raw_content
        self.fmt_content: str | None = None
        self.templates: list[str] = self._parse_templates(raw_content)

    @staticmethod
    def _parse_templates(content: str) -> list[str]:
        templates = []
        lines = content.split("\n")
        for line in lines:
            match = re.match(r"^@[a-z]+$", line.strip())
            if match:
                templates.append(match.group())

        return templates

    @staticmethod
    def format_metadata(metadata: micromanubot.config.Metadata) -> str:
        output = f"\\title{{{metadata.manuscript.title}}}\n\n"
        output += f"\\date{{{metadata.manuscript.date}}}\n\n"
        output += (
            r"\renewcommand\Authfont{\bfseries}"
            + "\n"
            + r"\setlength{\affilsep}{0em}"
            + "\n"
            + r"\newbox{\orcid}\sbox{\orcid}{\includegraphics[scale=0.06]"
            + r"{orcid.pdf}}"
            + "\n\n"
        )

        affil_to_idx = MainTemplate.gather_affiliations(metadata.authors)
        for author in metadata.authors:
            author_string = MainTemplate.format_author(author, affil_to_idx)
            output += author_string + "\n"

        output += "\n"

        for affil, i in affil_to_idx.items():
            output += f"\\affil[{i}]{{{affil}}}\n"

        return output

    @staticmethod
    def gather_affiliations(
        authors: list[micromanubot.config.Author],
    ) -> dict[str, int]:
        idx = 1
        affil_to_idx = dict()
        for author in authors:
            if author.affiliations is None:
                continue

            for affil in author.affiliations:
                if affil not in affil_to_idx:
                    affil_to_idx[affil] = idx
                    idx += 1

        return affil_to_idx

    @staticmethod
    def format_author(
        author: micromanubot.config.Author, affil_to_idx: dict[str, int]
    ) -> str:
        author_string = "\\author"
        if author.affiliations is not None:
            affil_idx = [str(affil_to_idx[a]) for a in author.affiliations]
            affil_idx = ",".join(affil_idx)
            author_string += f"[{affil_idx}]"
        author_string += r"{"
        if author.orcid is not None:
            author_string += f"{{\\href{{https://orcid.org/{author.orcid}}}"
            author_string += r"{\usebox{\orcid}\hspace{1mm}}"
        name = author.name.replace(" ", "~")
        author_string += name
        if author.corresponding:
            if author.email is None:
                author_string += r"\thanks{\texttt{Corresponding author}}"
            else:
                author_string += (
                    r"\thanks{\texttt{Correspondence may be addressed to "
                    + author.email
                    + r"}}"
                )
        author_string += r"}"
        if author.orcid is not None:
            author_string += r"}"
        return author_string

    def process(
        self,
        metadata: micromanubot.config.Metadata,
        main_files: list[pathlib.Path],
    ) -> MainTemplate:
        if self.templates != ["@metadata", "@abstract", "@main", "@supplement"]:
            raise ValueError(
                f"Unexpected templates in the main.tex file: {self.templates}."
            )

        content = self.raw_content
        if "@metadata" in self.templates:
            content = content.replace("@metadata", self.format_metadata(metadata), 1)
        if "@abstract" in self.templates:
            content = content.replace("@abstract", r"\input{abstract.tex}", 1)
        if "@main" in self.templates:
            main_content = ""
            for file in main_files:
                main_content += r"\input{" + file.name + "}\n"
            content = content.replace("@main", main_content, 1)
        if "@supplement" in self.templates:
            supplement_file = pathlib.Path("content/supplement.tex")
            if supplement_file.exists():
                supp_text = (
                    r"\section*{Supplementary Materials}"
                    + "\n"
                    + r"\input{supplement.tex}"
                )
                content = content.replace("@supplement", supp_text, 1)
            else:
                content = content.replace("@supplement", "", 1)

        self.fmt_content = content
        return self
