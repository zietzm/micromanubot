import importlib.resources
import pathlib
import shutil
import subprocess

import micromanubot.config
import micromanubot.figures


def initialize(directory: pathlib.Path, no_custom: bool = True) -> None:
    """Initialize a new project in a given, existing directory.

    Args:
        directory: Existing directory in which to initialize the project.
        no_custom: Whether to use a default configuration or not.

    Returns:
        None

    Raises:
        FileNotFoundError: The directory does not exist.
        NotADirectoryError: The path is not a directory.
        ValueError: The directory is not empty.
        OSError: The directory is not writable.
    """
    _check_directory(directory)
    if no_custom:
        metadata = micromanubot.config.Metadata.make_no_custom()
    else:
        metadata = micromanubot.config.Metadata.make_default()

    try:
        metadata.write_toml(directory / "umb.toml")
    except OSError as e:
        raise OSError(f"{directory} is not writable") from e

    cache_dir = directory.joinpath(".umb")
    cache_dir.mkdir()
    cache_dir.joinpath("images").mkdir()
    cache_dir.joinpath("citations_cache.bib").touch()
    fig_cache = cache_dir.joinpath("figures_cache.json")
    micromanubot.figures.FiguresCache(figures=[]).write_json(fig_cache)

    with open(directory.joinpath(".gitignore"), "w") as f:
        f.write(".umb\nbuild\n")

    _make_template_manuscript(directory)


def _check_directory(directory: pathlib.Path) -> None:
    """Check if a directory is suitable for a new project."""
    if not directory.exists():
        raise FileNotFoundError(f"{directory} does not exist")

    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    if list(directory.iterdir()):
        raise ValueError(f"{directory} is not empty")


def _make_template_manuscript(directory: pathlib.Path) -> None:
    """Create a template manuscript in the given directory."""
    content_templates = importlib.resources.files("micromanubot.template_data.content")
    content_dir = directory.joinpath("content")
    content_dir.mkdir()
    content_dir.joinpath("images").mkdir()
    files = [
        "abstract.tex",
        "1.introduction.tex",
        "2.results.tex",
        "3.discussion.tex",
        "4.methods.tex",
        "supplement.tex",
        "imports.tex",
        "manual_references.bib",
    ]
    for file in files:
        source_file = content_templates.joinpath(file)
        with importlib.resources.as_file(source_file) as source_path:
            shutil.copy(source_path, content_dir.joinpath(file))

    asset_templates = importlib.resources.files("micromanubot.template_data.assets")
    asset_dir = directory.joinpath("assets")
    asset_dir.mkdir()
    files = [
        "arxiv.sty",
        "orcid.pdf",
    ]
    for file in files:
        source_file = asset_templates.joinpath(file)
        with importlib.resources.as_file(source_file) as source_path:
            shutil.copy(source_path, asset_dir.joinpath(file))


def git_init(directory: pathlib.Path) -> None:
    """Initialize a git repository in the given directory."""
    subprocess.run(["git", "init"], cwd=directory, check=True, capture_output=True)
