import pylatexenc.latexwalker
import pytest

import micromanubot.cite


@pytest.mark.parametrize(
    "input, expected",
    [
        (r"\cite{abc123}", {"abc123"}),
        (r"\cite{abc123,def456}", {"abc123", "def456"}),
        (r"\cite{abc123, def456}", {"abc123", "def456"}),
        (r"\cite{doi:10.1103/PhysRev.47.777}", {"doi:10.1103/PhysRev.47.777"}),
        (r"\cite{@doi:10.1103/PhysRev.47.777}", {"@doi:10.1103/PhysRev.47.777"}),
        (
            r"\cite{@doi:10.1103/PhysRev.47.777, @doi:10.1002/andp.19053220607}",
            {"@doi:10.1103/PhysRev.47.777", "@doi:10.1002/andp.19053220607"},
        ),
    ],
)
def test_extract_keys(input, expected):
    parsed = pylatexenc.latexwalker.LatexWalker(input).get_latex_nodes()[0][0]
    assert micromanubot.cite.extract_keys(parsed) == expected


def test_fetch_doi_reference():
    doi = "10.1103/PhysRev.47.777"
    expected_output = "@article{Einstein_1935, title={Can Quantum-Mechanical Description of Physical Reality Be Considered Complete?}, volume={47}, ISSN={0031-899X}, url={http://dx.doi.org/10.1103/PhysRev.47.777}, DOI={10.1103/physrev.47.777}, number={10}, journal={Physical Review}, publisher={American Physical Society (APS)}, author={Einstein, A. and Podolsky, B. and Rosen, N.}, year={1935}, month=may, pages={777–780} }"
    reference = micromanubot.cite.fetch_doi_reference(doi)
    assert reference.strip() == expected_output
