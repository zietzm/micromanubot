from __future__ import annotations

import logging
import pathlib
import shutil
import urllib.parse

import pyrate_limiter
import requests
import validators
from pydantic import AnyUrl, BaseModel, Field
from pylatexenc.latexwalker import LatexEnvironmentNode, LatexMacroNode

logger = logging.getLogger(__name__)


class FigureSpec(BaseModel):
    old_alias: str
    new_alias: str
    url: AnyUrl | None = None
    local_path: pathlib.Path | None = None

    def __hash__(self) -> int:
        return hash((self.old_alias, self.new_alias))


class FiguresCache(BaseModel):
    figures: list[FigureSpec]
    alias_to_figure: dict[str, FigureSpec] = Field(exclude=True, default=dict())

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.alias_to_figure = {
            str(figure.old_alias): figure for figure in self.figures
        }

    def __add__(self, other: FiguresCache) -> FiguresCache:
        all_figures = set(self.figures + other.figures)
        new_figures = sorted(all_figures, key=lambda x: x.old_alias)
        return FiguresCache(figures=new_figures)

    def write_json(self, path: pathlib.Path) -> None:
        content = self.model_dump_json(indent=2)
        with open(path, "w") as f:
            f.write(content + "\n")


class ManuscriptFigures:
    def __init__(
        self,
        cache_path: pathlib.Path,
        manual_path: pathlib.Path,
    ) -> None:
        self.cache_json_path = cache_path.joinpath("figures_cache.json")
        self.cache_path = cache_path.joinpath("images")
        self.cache_path.mkdir(exist_ok=True)
        self.manual_path = manual_path

        with open(self.cache_json_path, "r") as f:
            cache_content = f.read()
        cache = FiguresCache.model_validate_json(cache_content)
        manual_cache = self._find_content_images(self.manual_path)
        self.cache: FiguresCache = cache + manual_cache
        logger.info(f"Loaded {len(self.cache.figures)} cached figure(s)")

        self.reference_to_alias: dict[str, str] = dict()

    @staticmethod
    def _find_content_images(directory: pathlib.Path) -> FiguresCache:
        """
        Find all local images and return a dictionary of their paths and
        aliases. `directory` should point to `content/images`.
        """
        images = list()
        for image_path in directory.iterdir():
            alias = image_path.relative_to(directory)
            fig = FigureSpec(
                old_alias=str(alias),
                new_alias=str(alias),
                url=None,
                local_path=image_path,
            )
            images.append(fig)
        return FiguresCache.model_validate({"figures": images})

    def parse_node(self, node: LatexEnvironmentNode) -> None:
        """Parse a LaTeX node and extract the image path/url."""
        if node.environmentname != "figure":
            raise ValueError("Node is not a figure node")

        keys = extract_keys(node)
        self.reference_to_alias.update({key: self._make_alias(key) for key in keys})

    @staticmethod
    def _get_fig_name(key: str) -> str:
        if validators.url(key):
            path = urllib.parse.urlparse(key).path
            filename = pathlib.Path(path).name
        elif pathlib.Path(key).is_file():
            filename = pathlib.Path(key).name
        else:
            raise ValueError(f"Invalid key: {key}")
        return filename

    @staticmethod
    def _make_alias(key: str) -> str:
        """Make an alias for a referenced image file.

        The new filename is the last part of the URL or the local path. Aliases
        are used for the build directory, so they'll have `images/` prepended.
        """
        root = pathlib.Path("images")
        filename = ManuscriptFigures._get_fig_name(key)
        return str(root / filename)

    def reconcile_figures(self, build_dir: pathlib.Path) -> None:
        """
        Copy all figures from cache/content to build directory. This should
        populate `self.reference_to_alias`.
        """
        logger.info(f"Found {len(self.reference_to_alias)} figure(s) in manuscript")
        to_download: list[FigureSpec] = list()
        missing: list[str] = list()
        for ref, alias in self.reference_to_alias.items():
            if ref in self.cache.alias_to_figure:
                fig = self.cache.alias_to_figure[ref]
                if fig.local_path is None:
                    missing.append(ref)
                else:
                    shutil.copy(fig.local_path, build_dir / alias)
            elif validators.url(ref):
                fig_info = {
                    "old_alias": ref,
                    "new_alias": alias,
                    "local_path": self.cache_path.joinpath(self._get_fig_name(ref)),
                    "url": ref,
                }
                fig = FigureSpec.model_validate(fig_info)
                to_download.append(fig)
            else:
                missing.append(ref)

        if missing:
            raise ValueError(f"Missing figures: {missing}")

        if to_download:
            cache_url_figures(to_download)
            self.cache = self.cache + FiguresCache(figures=to_download)
            self.cache.write_json(self.cache_json_path)
            for fig in to_download:
                assert fig.local_path is not None, "Local path should be set"
                shutil.copy(fig.local_path, build_dir / fig.new_alias)

        return None


def extract_keys(fig_node: LatexEnvironmentNode) -> set[str]:
    """
    Extract the path/url from the figure node.

    For example:

    \\begin{figure}
        \\includegraphics[width=\\textwidth]{myfig.png}
    \\end{figure} -> {myfig.png}

    \\begin{figure}
        \\begin{subfigure}\\includegraphics{myfig.png}\\end{subfigure}
        \\begin{subfigure}\\includegraphics{myfig2.png}\\end{subfigure}
    \\end{figure} -> {myfig.png, myfig2.png}
    """
    results = set()
    for node in fig_node.nodelist:
        if (
            isinstance(node, LatexEnvironmentNode)
            and node.environmentname == "subfigure"
        ):
            keys = extract_keys(node)
            results.update(keys)
        if isinstance(node, LatexMacroNode) and node.macroname == "includegraphics":
            key = extract_includegraphics_key(node)
            results.add(key)

    return results


def extract_includegraphics_key(node: LatexMacroNode) -> str:
    """Extract the path/url from a LaTeX includegraphics node."""
    if node.nodeargd is None:
        raise ValueError("No arguments found in includegraphics node")

    argspec = node.nodeargd.argspec
    if r"{" not in argspec:
        raise ValueError(f"Invalid includegraphics node argspec: {argspec}")

    if len(argspec) != len(node.nodeargd.argnlist):
        raise ValueError("Mismatch between argspec and arguments")

    kw_idx = argspec.index(r"{")
    "}}"
    key_group = node.nodeargd.argnlist[kw_idx]

    if len(key_group.nodelist) != 1:
        raise ValueError(f"Invalid key group: {key_group}")

    key_node = key_group.nodelist[0]
    return key_node.chars


def cache_url_figures(figures: list[FigureSpec], n_per_second: int = 50) -> None:
    """Pull figures from a URL and save them to the cache."""
    logger.info(f"Fetching {len(figures)} figure(s)")
    rate = pyrate_limiter.Rate(n_per_second, pyrate_limiter.Duration.SECOND)
    limiter = pyrate_limiter.Limiter(rate, max_delay=1000)

    for fig in figures:
        try:
            limiter.try_acquire(str(fig.url))
        except pyrate_limiter.LimiterDelayException as e:
            raise ValueError("Rate limit exceeded") from e

        assert fig.local_path is not None, "Local path should be set"
        fetch_url_figure(str(fig.url), fig.local_path)


def fetch_url_figure(url: str, cache_path: pathlib.Path) -> None:
    """Fetch a figure from a URL and save it to the cache."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "github.com":
        url = url + "?raw=true"

    result = requests.get(url)
    if result.status_code != 200:
        raise ValueError(f"Failed to fetch figure: {url}")

    with open(cache_path, "wb") as f:
        f.write(result.content)
