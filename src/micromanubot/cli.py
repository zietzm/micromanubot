import argparse
import logging
import pathlib

from rich import print
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

import micromanubot
import micromanubot.build
import micromanubot.install
import micromanubot.new


def main():
    parser = argparse.ArgumentParser(description="Micromanubot")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {micromanubot.__version__}",
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
            handle_new(args)
        case "build":
            cwd = pathlib.Path.cwd()
            handle_build(args, cwd)
        case "install":
            handle_install(args)
        case "uninstall":
            handle_uninstall(args)
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
    new_parser.add_argument(
        "--no-custom",
        help="Do not customize anything for the current user/date/locale",
        action="store_true",
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


def handle_new(args: argparse.Namespace) -> None:
    if args.PATH.exists():
        raise ValueError(f"Path `{args.PATH}` already exists")
    args.PATH.mkdir()
    micromanubot.new.initialize(args.PATH, args.no_custom)
    micromanubot.new.git_init(args.PATH)
    print(f"    [bold green]Created[/] manuscript at `{args.PATH}`")


def handle_build(args: argparse.Namespace, cwd: pathlib.Path) -> None:
    if not micromanubot.build.is_umb_project(cwd):
        raise ValueError("Not an umb project")
    print("   [bold green]Building[/] manuscript")
    micromanubot.build.setup_build_directory(cwd)
    micromanubot.build.build_latex(cwd)
    if args.type in {"all", "pdf"}:
        micromanubot.install.check_pdflatex_bibtex_installed()
        micromanubot.build.build_latex_pdf(cwd)
    print("   [bold green]Finished[/] building the manuscript")


def handle_install(args: argparse.Namespace) -> None:
    is_installed = micromanubot.install.is_tinytex_installed()
    if is_installed and not args.force:
        print("TinyTeX already installed (use --force to reinstall)")
        return
    if is_installed and args.force:
        print("   [bold green]Removing[/] existing TinyTeX installation")
        micromanubot.install.uninstall_tinytex(args.root)

    print(" [bold green]Installing[/] LaTeX compiler and packages")
    micromanubot.install.install_tinytex(args.root)
    print("   [bold green]Finished[/] installing TinyTeX and packages")


def handle_uninstall(args: argparse.Namespace) -> None:
    if not micromanubot.install.is_tinytex_installed():
        print("TinyTeX is not installed")
        return
    micromanubot.install.uninstall_tinytex(args.root)
    print(" [bold green]Uninstalled[/] LaTeX compiler and packages")
