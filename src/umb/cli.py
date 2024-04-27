import argparse
import logging
import pathlib

from rich import print
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

import umb
import umb.build
import umb.new


def main():
    parser = argparse.ArgumentParser(description="Micromanubot")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {umb.__version__}",
        help="Show the version number and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase verbosity",
    )
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    add_new_command(subparsers)
    add_build_command(subparsers)
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
            umb.build.build_latex_pdf(cwd)
        case None:
            parser.print_help()
        case _:
            raise NotImplementedError(f"Command {args.command} not implemented")


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
