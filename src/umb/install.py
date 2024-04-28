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
    if not bin_dir.exists():
        return False

    for bin in ["pdflatex", "bibtex"]:
        matches = list(bin_dir.glob(f"*/{bin}"))
        if len(matches) == 0:
            return False
    return True


def _find_latex(name: str) -> pathlib.Path:
    on_path = shutil.which(name)
    if on_path:
        return pathlib.Path(on_path)

    umb_dir = pathlib.Path.home().joinpath(".umb", "tinytex", "bin")
    tinytex_executable = umb_dir.joinpath(name)
    if tinytex_executable.exists():
        return tinytex_executable

    raise FileNotFoundError(f"{name} not found")


def find_pdflatex() -> pathlib.Path:
    return _find_latex("pdflatex")


def find_bibtex() -> pathlib.Path:
    return _find_latex("bibtex")


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
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_dir = tex_dir.as_posix()
    pytinytex.download_tinytex(target_folder=tex_dir, download_folder=tex_dir)


def uninstall_tinytex(root: pathlib.Path) -> None:
    shutil.rmtree(root.joinpath("tinytex"))
