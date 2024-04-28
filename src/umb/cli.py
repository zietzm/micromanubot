import argparse
import logging
import pathlib

from rich import print
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

import umb
import umb.build
import umb.install
import umb.new


def main():
    parser = argparse.ArgumentParser(description="Micromanubot")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {umb.__version__}",
        help="Show the version number and exit",
    )
    add_verbosity_arg(parser)
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    add_new_command(subparsers)
    add_build_command(subparsers)
    add_install_command(subparsers)
    add_uninstall_command(subparsers)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            handlers=[RichHandler(show_time=False, highlighter=NullHighlighter())],
        )
    else:
        logging.basicConfig(
            level=logging.WARNING,
            handlers=[RichHandler(show_time=False, highlighter=NullHighlighter())],
        )

    match args.command:
        case "new":
            if args.PATH.exists():
                raise ValueError(f"Path `{args.PATH}` already exists")
            args.PATH.mkdir()
            umb.new.initialize(args.PATH)
            umb.new.git_init(args.PATH)
            print(f"    [bold green]Created[/] manuscript at `{args.PATH}`")
        case "build":
            cwd = pathlib.Path.cwd()
            if not umb.build.is_umb_project(cwd):
                raise ValueError("Not an umb project")
            print("   [bold green]Building[/] manuscript")
            umb.build.setup_build_directory(cwd)
            umb.build.build_latex(cwd)
            if args.type in {"all", "pdf"}:
                umb.install.check_pdflatex_bibtex_installed()
                umb.build.build_latex_pdf(cwd)
        case "install":
            umb.install.check_extra_installed()
            is_installed = umb.install.is_tinytex_installed(args.root)
            if is_installed and not args.force:
                print("TinyTeX already installed (use --force to reinstall)")
                return
            if is_installed and args.force:
                print("   [bold green]Removing[/] existing TinyTeX installation")
                umb.install.uninstall_tinytex(args.root)

            print(" [bold green]Installing[/] LaTeX compiler and packages")
            umb.install.install_tinytex(args.root)
        case "uninstall":
            if not umb.install.is_tinytex_installed(args.root):
                print("TinyTeX is not installed")
                return
            umb.install.uninstall_tinytex(args.root)
            print(" [bold green]Uninstalled[/] LaTeX compiler and packages")
        case None:
            parser.print_help()
        case _:
            raise NotImplementedError(f"Command {args.command} not implemented")


def add_verbosity_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase verbosity",
    )


def add_new_command(subparsers: argparse._SubParsersAction) -> None:
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new project",
        description="Create a new project at <path>",
        add_help=True,
    )
    new_parser.add_argument(
        "PATH", help="Path to create the project", type=pathlib.Path
    )
    add_verbosity_arg(new_parser)


def add_build_command(subparsers: argparse._SubParsersAction) -> None:
    build_parser = subparsers.add_parser(
        "build",
        help="Build the project",
        description="Build the project",
        add_help=True,
    )
    build_parser.add_argument(
        "--type",
        help="Type of build",
        choices=["all", "tex", "pdf"],
        default="all",
    )
    add_verbosity_arg(build_parser)


def add_install_command(subparsers: argparse._SubParsersAction) -> None:
    install_parser = subparsers.add_parser(
        "install",
        help="Install LaTeX compiler and packages",
        description="Install LaTeX compiler and packages",
        add_help=True,
    )
    install_parser.add_argument(
        "--root",
        help="Root directory to install TinyTex. Default is ~/.umb",
        type=pathlib.Path,
        default=pathlib.Path.home().joinpath(".umb"),
    )
    install_parser.add_argument(
        "--force",
        help="Force installation",
        action="store_true",
    )
    add_verbosity_arg(install_parser)


def add_uninstall_command(subparsers: argparse._SubParsersAction) -> None:
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall LaTeX compiler and packages",
        description="Uninstall LaTeX compiler and packages",
        add_help=True,
    )
    uninstall_parser.add_argument(
        "--root",
        help="Root directory to uninstall TinyTex. Default is ~/.umb",
        type=pathlib.Path,
        default=pathlib.Path.home().joinpath(".umb"),
    )
    add_verbosity_arg(uninstall_parser)
