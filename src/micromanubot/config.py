from __future__ import annotations

import datetime
import getpass
import locale
import os

import tomlkit
from pydantic import BaseModel, Field

import micromanubot


class ManubotConfig(BaseModel):
    version: str = Field(default=micromanubot.__version__)


class Manuscript(BaseModel):
    title: str = Field(default="Manuscript Title")
    date: datetime.date = Field(default_factory=datetime.date.today)
    keywords: list[str]
    language: str = Field(default_factory=lambda: locale.getlocale()[0] or "en_US")

    @classmethod
    def make_no_custom(cls) -> Manuscript:
        """Create a default manuscript object without customizing."""
        return cls(
            title="Manuscript Title",
            keywords=["umb", "micromanubot"],
            date=datetime.date(2024, 1, 1),
            language="en_US",
        )


class Author(BaseModel):
    name: str = Field(default_factory=getpass.getuser)
    initials: str = Field(default_factory=lambda: getpass.getuser()[0:2].upper())
    orcid: str | None = None
    email: str | None = None
    affiliations: list[str] | None = None
    funders: list[str] | None = None
    corresponding: bool | None = None

    @classmethod
    def make_no_custom(cls) -> Author:
        """Create a default author object without customizing."""
        return cls(
            name="Author Name",
            initials="AN",
            orcid="0000-0000-0000-0000",
            email="author@uni-somewhere.edu",
            affiliations=[
                "Department of Something, University of Somewhere, City, Country"
            ],
            funders=["Funder Name"],
            corresponding=True,
        )


class Metadata(BaseModel):
    umb: ManubotConfig
    manuscript: Manuscript
    authors: list[Author]

    @classmethod
    def make_no_custom(cls) -> Metadata:
        """Create a default manuscript metadata object without customizing."""
        return cls(
            umb=ManubotConfig(),
            manuscript=Manuscript.make_no_custom(),
            authors=[Author.make_no_custom()],
        )

    @classmethod
    def make_default(cls) -> Metadata:
        """Create a default manuscript metadata object."""
        template_affil = (
            "Department of Something, University of Somewhere, City, Country"
        )
        return cls(
            umb=ManubotConfig(),
            manuscript=Manuscript(
                title="Manuscript Title",
                keywords=["umb", "micromanubot"],
            ),
            authors=[Author(affiliations=[template_affil], corresponding=True)],
        )

    @classmethod
    def read_toml(cls, path: str | os.PathLike) -> Metadata:
        """Read manuscript metadata from a TOML file."""
        with open(path, "r") as file:
            doc = tomlkit.loads(file.read())

        return cls.model_validate(doc)

    def _build_toml(self) -> tomlkit.TOMLDocument:
        """Marshal the metadata into a TOML document.

        This verbose implementation is used to give flexibility for future
        additions like comments, etc.
        """
        doc = tomlkit.document()

        umb = tomlkit.table()
        umb.add("version", self.umb.version)
        doc.add("umb", umb)

        manuscript = tomlkit.table()
        manuscript.add("title", self.manuscript.title)
        manuscript.add("date", self.manuscript.date)
        manuscript.add("keywords", self.manuscript.keywords)
        manuscript.add("language", self.manuscript.language)
        doc.add("manuscript", manuscript)

        authors = tomlkit.aot()
        for author in self.authors:
            a = tomlkit.item(author.model_dump(exclude_none=True))
            authors.append(a)

        doc.add("authors", authors)
        return doc

    def write_toml(self, path: str | os.PathLike) -> None:
        """Write the metadata to a TOML file."""
        toml_doc = self._build_toml()
        with open(path, "w") as file:
            tomlkit.dump(toml_doc, file)
