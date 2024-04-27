import datetime
import hashlib
import pathlib
import shlex
import subprocess
from tempfile import TemporaryDirectory

import umb.config


def test_init(tmp_path: pathlib.Path) -> None:
    """Test that all the necessary directories and files are created."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        new_args = shlex.split(f"umb new {tmp_path}")
        subprocess.run(new_args, check=True)
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
        tmp_path = pathlib.Path(tmp_dir)
        new_args = shlex.split(f"umb new {tmp_path}")
        subprocess.run(new_args, check=True)

        scrub_metadata(tmp_path)

        build_args = shlex.split("umb build")
        subprocess.run(build_args, cwd=tmp_path, check=True)

        build_files = [
            "build/main.tex",
            "build/main.pdf",
        ]
        for file in build_files:
            assert (tmp_path / file).exists()
            assert (tmp_path / file).is_file()

        # This hash will need to be modified manually if the templates change.
        # Simply inspect the file, run md5sum main.pdf, and update the hash.
        expected_hash = "351f209f01528a181f28f34d2d367b15"
        with open(tmp_path / "build/main.pdf", "rb") as f:
            pdf_content = f.read()

        assert hashlib.md5(pdf_content).hexdigest() == expected_hash


def scrub_metadata(root_dir: pathlib.Path) -> None:
    """Set all non-standard metadata to arbitrary, fixed values.

    This allows reproducible testing without worrying about the username/date.
    """
    metadata = umb.config.Metadata.read_toml(root_dir / "umb.toml")
    metadata.umb.version = "0.0.0"
    metadata.manuscript.date = datetime.date(2024, 1, 1)
    metadata.manuscript.title = "Test Title"
    metadata.authors[0].name = "Test Author"
    metadata.authors[0].initials = "TA"
