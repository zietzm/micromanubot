import argparse
import pathlib
from tempfile import TemporaryDirectory

import fitz

import micromanubot.cli
import micromanubot.config


def test_new(tmp_path: pathlib.Path) -> None:
    """Test that all the necessary directories and files are created."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir).joinpath("my-manuscript")
        new_args = argparse.Namespace(PATH=tmp_path, no_custom=True)
        micromanubot.cli.handle_new(new_args)
        directories = [
            ".umb",
            ".umb/images",
            "assets",
            "content",
            "content/images",
        ]
        for directory in directories:
            assert (tmp_path / directory).exists()
            assert (tmp_path / directory).is_dir()

        files = [
            "umb.toml",
            ".gitignore",
            ".umb/citations_cache.bib",
            ".umb/figures_cache.json",
            "content/abstract.tex",
            "content/1.introduction.tex",
            "content/2.results.tex",
            "content/3.discussion.tex",
            "content/4.methods.tex",
            "content/supplement.tex",
            "content/imports.tex",
            "content/manual_references.bib",
        ]
        for file in files:
            assert (tmp_path / file).exists()
            assert (tmp_path / file).is_file()


def test_build(tmp_path: pathlib.Path) -> None:
    """Test that the build command works."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir).joinpath("my-manuscript")
        new_args = argparse.Namespace(PATH=tmp_path, no_custom=True)
        micromanubot.cli.handle_new(new_args)

        build_args = argparse.Namespace(type="all")
        micromanubot.cli.handle_build(build_args, tmp_path)

        build_files = [
            "build/main.tex",
            "build/main.pdf",
        ]
        for file in build_files:
            assert (tmp_path / file).exists()
            assert (tmp_path / file).is_file()

        validate_pdf(tmp_path / "build/main.pdf")


def validate_pdf(pdf_path: pathlib.Path) -> None:
    """Validate a PDF file.

    This currently just checks for the image being correct. The main issue with
    early builds was failing to include images correctly. Could add many more
    checks here in the future.
    """
    doc = fitz.open(pdf_path)
    assert doc.page_count == 2
    pages = list(doc.pages())
    page = pages[0]
    image_hash = page.get_image_info(hashes=True)[0]["digest"]
    expected = b"\xce(\x9b\x8a\xe3\xfe\xbe_p5\xdf\x8b\x1f2u\xb4"
    assert image_hash == expected
