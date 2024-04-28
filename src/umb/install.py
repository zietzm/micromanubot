"""Install a LaTeX compiler and necessary packages

Defaults to TinyTeX. Installation requires the "tex" extra.
"""
import importlib
import importlib.util
import pathlib
import shutil


def check_extra_installed() -> None:
    spec = importlib.util.find_spec("pytinytex")
    is_installed = spec is not None
    if not is_installed:
        raise ImportError("The 'tex' extra is required. ('pip install umb[tex]')")


def is_tinytex_installed(root: pathlib.Path) -> bool:
    bin_dir = root.joinpath("tinytex", "bin")
    for bin in ["pdflatex", "bibtex"]:
        if not bin_dir.joinpath(bin).exists():
            return False
    return True


def check_pdflatex_bibtex_installed() -> None:
    """Check if pdflatex and bibtex are installed."""
    umb_dir = pathlib.Path.home().joinpath(".umb", "tinytex", "bin")
    for command in ["pdflatex", "bibtex"]:
        on_path = shutil.which(command)
        if on_path:
            continue
        elif umb_dir.joinpath(command).exists():
            continue
        else:
            raise FileNotFoundError(f"{command} not found")


def install_tinytex(root: pathlib.Path) -> None:
    pytinytex = importlib.import_module("pytinytex")
    tex_dir = root.joinpath("tinytex")
    pytinytex.install_tinytex(tex_dir)
    print(f"TinyTeX installed at {root}")
