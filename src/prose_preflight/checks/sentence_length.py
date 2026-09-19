"""Sentence-length outliers. Regex segmentation, word count against a YAML maximum."""

from prose_preflight.checks._text import WORD, paragraphs, sentences
from prose_preflight.extract import Document
from prose_preflight.finding import Finding


def check(doc: Document, rule: dict) -> list[Finding]:
    maximum = rule.get("max_words", 40)
    severity = rule.get("severity", "warning")
    findings = []
    for text, positions in paragraphs(doc):
        for offset, sentence in sentences(text):
            words = len(WORD.findall(sentence))
            if words <= maximum:
                continue
            short = sentence[:40].strip() + ("\u2026" if len(sentence) > 40 else "")
            line, col = positions[offset]
            findings.append(
                Finding(
                    check="sentence_length.long",
                    category="readability",
                    severity=severity,
                    line=line,
                    col=col,
                    excerpt=short,
                    message=f"Sentence runs {words} words (limit {maximum}); split it.",
                    section=doc.section_at(line),
                )
            )
    return findings
