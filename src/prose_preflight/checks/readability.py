"""Per-section readability scores from textstat, against YAML thresholds."""

from bisect import bisect_right

import textstat

from prose_preflight.extract import Document
from prose_preflight.finding import Finding

METRICS = {  # rule suffix: (textstat function, comparison, threshold key)
    "flesch": (textstat.flesch_reading_ease, "min", "min_flesch"),
    "fog": (textstat.gunning_fog, "max", "max_fog"),
}


def check(doc: Document, rule: dict) -> list[Finding]:
    severity = rule.get("severity", "warning")
    min_words = rule.get("min_words", 50)
    findings = []
    for line, title, text, words in _sections(doc):
        if words < min_words:  # short sections score as noise
            continue
        for name, (score_of, direction, key) in METRICS.items():
            limit = rule.get(key)
            score = round(score_of(text), 1)
            if limit is None or (
                score >= limit if direction == "min" else score <= limit
            ):
                continue
            findings.append(
                Finding(
                    check=f"readability.{name}",
                    category="readability",
                    severity=severity,
                    line=line,
                    col=1,
                    excerpt=title or str(doc.path.name),
                    message=(
                        f"{name} score {score} is "
                        f"{'below' if direction == 'min' else 'above'} the {limit} "
                        f"threshold ({words} words); shorten sentences or simplify wording."
                    ),
                    section=title,
                )
            )
    return findings


def _sections(doc: Document):
    """Yield (line, title, text, word count) per section; the whole file if unheaded."""
    bounds = [(line, title) for line, _, title in doc.headings] or [(1, None)]
    starts = [line for line, _ in bounds]
    chunks = [[] for _ in bounds]
    for first, last in doc.paragraphs:
        owner = bisect_right(starts, first) - 1
        if owner >= 0:  # paragraphs above the first heading belong to no section
            chunks[owner] += [doc.masked[n - 1].strip() for n in range(first, last + 1)]
    for (start, title), parts in zip(bounds, chunks):
        text = " ".join(parts)
        yield start, title, text, len(text.split())
