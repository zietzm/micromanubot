import pytest
from pylatexenc.latexwalker import LatexWalker

import micromanubot.figures


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            r"\begin{figure}\includegraphics[width=\textwidth]{myfig.png}\end{figure}",
            {"myfig.png"},
        ),
        (
            r"\begin{figure}\centering\includegraphics[width=\textwidth]{myfig.png}\end{figure}",
            {"myfig.png"},
        ),
        (
            r"\begin{figure}\begin{subfigure}\includegraphics{myfig.png}\end{subfigure}\begin{subfigure}\includegraphics{myfig2.png}\end{subfigure}\end{figure}",
            {"myfig.png", "myfig2.png"},
        ),
    ],
)
def test_extract_keys(test_input, expected):
    walker = LatexWalker(test_input)
    nodelist, _, _ = walker.get_latex_nodes()
    fig_node = nodelist[0]
    assert micromanubot.figures.extract_keys(fig_node) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            r"\includegraphics[width=\textwidth]{myfig.png}",
            "myfig.png",
        ),
        (
            r"\includegraphics{myfig.png}",
            "myfig.png",
        ),
    ],
)
def test_extract_includegraphics_key(test_input, expected):
    walker = LatexWalker(test_input)
    nodelist, _, _ = walker.get_latex_nodes()
    fig_node = nodelist[0]
    assert micromanubot.figures.extract_includegraphics_key(fig_node) == expected
