# Part of the EH AI Suite by ERP Heritage.
"""Structure-aware text chunking with overlap.

Improves on naive fixed-window splitting: paragraphs are kept whole where they
fit, oversized paragraphs are split on sentence boundaries (then hard-sliced as
a last resort), and a configurable character overlap is carried between adjacent
chunks so retrieval does not lose context at boundaries.
"""
import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE = re.compile(r"[ \t]+")


def _clean(text):
    if not text:
        return ""
    text = text.replace("\x00", "")
    lines = [_WHITESPACE.sub(" ", line).strip() for line in text.splitlines()]
    # Collapse runs of blank lines into a single paragraph break.
    paragraphs = []
    buffer = []
    for line in lines:
        if line:
            buffer.append(line)
        elif buffer:
            paragraphs.append(" ".join(buffer))
            buffer = []
    if buffer:
        paragraphs.append(" ".join(buffer))
    return "\n\n".join(paragraphs)


def _slice(text, size):
    return [text[i:i + size] for i in range(0, len(text), size)]


def _split_long(paragraph, target):
    units = []
    current = ""
    for sentence in _SENTENCE_BOUNDARY.split(paragraph):
        if not sentence:
            continue
        if len(sentence) > target:
            if current:
                units.append(current)
                current = ""
            units.extend(_slice(sentence, target))
        elif current and len(current) + 1 + len(sentence) > target:
            units.append(current)
            current = sentence
        else:
            current = (current + " " + sentence) if current else sentence
    if current:
        units.append(current)
    return units


def chunk_text(text, target=1500, overlap=150, hard_max=4000):
    """Split ``text`` into overlapping chunks roughly ``target`` characters long."""
    text = _clean(text)
    if not text:
        return []

    units = []
    for paragraph in text.split("\n\n"):
        if len(paragraph) <= hard_max:
            units.append(paragraph)
        else:
            units.extend(_split_long(paragraph, target))

    chunks = []
    current = ""
    for unit in units:
        if current and len(current) + 2 + len(unit) > target:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = (tail + "\n\n" + unit).strip() if tail else unit
        else:
            current = (current + "\n\n" + unit) if current else unit
    if current:
        chunks.append(current)

    final = []
    for chunk in chunks:
        if len(chunk) <= hard_max:
            final.append(chunk)
        else:
            final.extend(_slice(chunk, hard_max))
    return [chunk for chunk in final if chunk.strip()]
