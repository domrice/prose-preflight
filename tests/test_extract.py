"""Line fidelity is the contract: every assertion here is a line number."""

from prose_preflight.extract import read

DOC = """\
# Methods

We sampled the corpus [@smith2020] and ran `preflight --full` on it.

```python
# this heading is code, not a heading
print("dataset")
```

$$
E = mc^2
$$

More prose, inline math $x_1$ here.

![A plot](plot.png){#fig:plot}

## Results
"""


def build(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text(DOC)
    return read(path)


def test_headings_keep_source_lines(tmp_path):
    assert build(tmp_path).headings == [(1, 1, "Methods"), (18, 2, "Results")]


def test_code_and_math_are_masked_not_deleted(tmp_path):
    doc = build(tmp_path)
    assert len(doc.masked) == len(doc.lines) == 18
    assert [n for n, _ in doc.prose()] == [1, 3, 14, 16, 18]
    # inline code blanked, surrounding prose and every column left where it was
    assert len(doc.masked[2]) == len(doc.lines[2])
    assert doc.masked[2].startswith("We sampled the corpus [@smith2020] and ran ")
    assert doc.masked[2].endswith(" on it.")
    assert "preflight" not in doc.masked[2]


def test_paragraphs_and_sections(tmp_path):
    doc = build(tmp_path)
    assert doc.paragraphs == [(3, 3), (14, 14), (16, 16)]
    assert doc.section_at(14) == "Methods"
    assert doc.section_at(18) == "Results"


def test_plain_text_recognizes_nothing(tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text(DOC)
    doc = read(path)
    assert doc.headings == []
    assert doc.masked == doc.lines


TEX = r"""\documentclass{article}
\title{Ignored preamble}
\begin{document}
\section{Methods}

We sampled the corpus \citep[p.~3]{smith2020,jones2019} and \emph{ran} it.

\begin{verbatim}
\section{not a heading}
\end{verbatim}

\begin{equation}
E = mc^2
\end{equation}

More prose, inline math $x_1$ here.  % a trailing comment

\begin{figure}
\caption{A plot}\label{fig:plot}
\end{figure}

\subsection{Results}
\end{document}
"""


def build_tex(tmp_path):
    path = tmp_path / "doc.tex"
    path.write_text(TEX)
    return read(path)


def test_latex_line_fidelity(tmp_path):
    doc = build_tex(tmp_path)
    assert len(doc.masked) == len(doc.lines)
    assert all(len(m) == len(s) for m, s in zip(doc.masked, doc.lines))
    assert doc.headings == [(4, 1, "Methods"), (22, 2, "Results")]


def test_latex_masks_preamble_verbatim_math_and_comments(tmp_path):
    doc = build_tex(tmp_path)
    assert [n for n, _ in doc.prose()] == [6, 16, 19]
    assert " ".join(doc.masked[5].split()) == "We sampled the corpus and ran it."
    assert " ".join(doc.masked[15].split()) == "More prose, inline math here."
    assert doc.section_at(16) == "Methods"
