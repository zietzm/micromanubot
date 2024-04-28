"""Install a LaTeX compiler and necessary packages

Defaults to TinyTeX. Installation requires the "tex" extra.
"""

import pathlib
import shutil
import subprocess

import micromanubot.pytinytex

DEFAULT_PACKAGES = ["fancyhdr", "multirow", "preprint"]


def is_tinytex_installed() -> bool:
    return pathlib.Path.home().joinpath(".umb", "tinytex").exists()


def _find_binary(name: str) -> pathlib.Path:
    root = pathlib.Path.home().joinpath(".umb")
    umb_dir = root.joinpath("tinytex", "bin")
    matches = list(umb_dir.glob(f"*/{name}"))
    if len(matches) > 0:
        return matches[0]

    on_path = shutil.which(name)
    if on_path:
        return pathlib.Path(on_path)

    raise FileNotFoundError(f"{name} not found")


def find_pdflatex() -> pathlib.Path:
    return _find_binary("pdflatex")


def find_bibtex() -> pathlib.Path:
    return _find_binary("bibtex")


def find_tlmgr() -> pathlib.Path:
    return _find_binary("tlmgr")


def check_pdflatex_bibtex_installed() -> None:
    """Check if pdflatex and bibtex are installed."""
    find_pdflatex()
    find_bibtex()


def install_tinytex(root: pathlib.Path) -> None:
    tex_dir = root.joinpath("tinytex")
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_dir = tex_dir.as_posix()
    micromanubot.pytinytex.download_tinytex(
        target_folder=tex_dir, download_folder=tex_dir
    )
    check_pdflatex_bibtex_installed()
    install_packages(DEFAULT_PACKAGES)


def uninstall_tinytex(root: pathlib.Path) -> None:
    shutil.rmtree(root.joinpath("tinytex"))


def install_packages(packages: list[str]) -> None:
    tlmgr = find_tlmgr()
    command = [tlmgr.as_posix(), "install"] + packages
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to install packages: {result.stdout.decode()} "
            f"{result.stderr.decode()}"
        )
