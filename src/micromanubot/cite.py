from __future__ import annotations

import logging
import os
import sys

import bibtexparser
import pyrate_limiter
import requests
from bibtexparser.model import Block
from pylatexenc.latexwalker import LatexMacroNode

import micromanubot

logger = logging.getLogger(__name__)


class Bibliography:
    def __init__(
        self, cache_path: str | os.PathLike, manual_path: str | os.PathLike
    ) -> None:
        self.cache_path = cache_path
        self.manual_path = manual_path
        self.cache = bibtexparser.parse_file(str(cache_path))
        self.manual = bibtexparser.parse_file(str(manual_path))
        n_citations = len(self.cache.entries) + len(self.manual.entries)
        logger.info(f"Loaded {n_citations} cached citation(s)")
        self.unique_keys: set[str] = set()

    def parse_node(self, node: LatexMacroNode) -> None:
        """Parse a LaTeX node and extract citation keys."""
        if node.macroname != "cite":
            raise ValueError("Node is not a citation node")

        citation_keys = extract_keys(node)
        self.unique_keys.update(citation_keys)

    def reconcile_citations(self) -> bibtexparser.Library:
        """Reconcile the citations in the manuscript with the cache and manual
        BibTeX file. Returns the final BibTeX library with all references for
        the manuscript.
        """
        cache_dict = self.cache.entries_dict
        cache_keys = set(cache_dict.keys())
        manual_dict = self.manual.entries_dict
        manual_keys = set(manual_dict.keys())

        logger.info(f"Found {len(self.unique_keys)} citation(s) in manuscript")
        output = bibtexparser.Library()
        references_to_pull = list()
        missing_keys = list()
        for key in sorted(self.unique_keys):
            if "@" in key:
                stripped = key.lstrip("@").strip()
                if stripped in cache_keys:
                    output.add(cache_dict[stripped])
                elif stripped in manual_keys:
                    output.add(manual_dict[stripped])
                else:
                    references_to_pull.append(stripped)
            elif key in manual_keys:
                # Manual entries take precedence
                output.add(manual_dict[key])
            elif key in cache_keys:
                output.add(cache_dict[key])
            else:
                missing_keys.append(key)

        if missing_keys:
            raise ValueError(f"Missing keys: {missing_keys}")

        if references_to_pull:
            new_entries = pull_doi_references(references_to_pull)
            output.add(new_entries)
            self.cache.add(new_entries)
            bibtexparser.write_file(str(self.cache_path), self.cache)

        return output


def extract_keys(node: LatexMacroNode) -> set[str]:
    """Extract the citation keys from a citation node.

    For example:

    \\cite{abc123} -> {'abc123'}
    \\cite{abc123, def456} -> {'abc123', 'def456'}

    This is a complicated process because the LaTeX parser allows for all
    sorts of additional arguments in the \\cite command. We also can't
    modify the node in place, since it's only a view of the original LaTeX
    string. We need to extract the keys, de-duplicate, then modify the
    whole string later (because we don't want to change the string
    underneath the LaTeX parser).
    """
    if node.nodeargd is None:
        raise ValueError("Citation node has no arguments")

    argspec = node.nodeargd.argspec
    if r"{" not in argspec:
        raise ValueError(f"Invalid citation node argspec: {argspec}")

    if len(argspec) != len(node.nodeargd.argnlist):
        raise ValueError(f"Invalid citation node: {argspec}")

    kw_idx = argspec.index(r"{")
    key_group = node.nodeargd.argnlist[kw_idx]

    if len(key_group.nodelist) != 1:
        raise ValueError(f"Invalid citation key node: {key_group}")

    key_node = key_group.nodelist[0]
    citation_keys = key_node.chars.split(",")
    citation_keys = [key.strip() for key in citation_keys]
    return set(citation_keys)


def pull_doi_references(keys: list[str], n_per_second: int = 50) -> list[Block]:
    """Fetch BibTeX references for a list of DOI keys.

    Ensure that no more than `n_per_second` requests are made."""
    logger.info(f"Fetching {len(keys)} reference(s)")
    rate = pyrate_limiter.Rate(n_per_second, pyrate_limiter.Duration.SECOND)
    limiter = pyrate_limiter.Limiter(rate, max_delay=1000)

    results = list()
    for key in keys:
        try:
            limiter.try_acquire(key)
        except pyrate_limiter.LimiterDelayException as e:
            raise ValueError("Rate limit exceeded") from e

        try:
            result = fetch_doi_reference(key)
        except Exception as e:
            raise ValueError(f"Failed to fetch reference for {key}") from e

        entry = bibtexparser.parse_string(result).entries[0]
        entry.key = key
        results.append(entry)

    return results


def fetch_doi_reference(key: str) -> str:
    """Fetch a BibTeX reference for a DOI using the doi.org API."""
    headers = {
        "Accept": "application/x-bibtex",
        "User-Agent": f"umb/{micromanubot.__version__}; Python/{sys.version}",
    }
    response = requests.get(f"https://doi.org/{key}", headers=headers)
    response.raise_for_status()
    return response.text
