import csv
import io
import re
from collections.abc import Iterable, Iterator
from typing import BinaryIO

import pdfplumber
from docx import Document

BOM = "﻿"

_BOUNDARY = re.compile(r"(?P<punct>[.!?]+)\s+(?=[A-ZÁ-Ž0-9„\"'(])")
_LAST_TOKEN = re.compile(r"([A-Za-zÁ-Žá-ž]+|\d+)$")
_DOTTED_ACRONYM = re.compile(r"[A-Za-zÁ-Žá-ž]\.[A-Za-zÁ-Žá-ž]{1,3}$")

_ABBREVIATIONS = {
    "mgr", "bc", "ing", "ph", "phd", "csc", "drsc",
    "mudr", "judr", "phdr", "rndr", "mvdr", "paeddr",
    "prof", "doc", "dr",
    "např", "atd", "atp", "apod", "aj", "tj", "tzv", "tzn",
    "resp", "popř", "příp", "kupř", "zvl", "zejm",
    "vč", "mj", "cca", "max", "min", "event", "ev",
    "str", "s", "č", "kap", "odst", "písm", "obr", "tab",
    "roč", "sv", "vyd", "ed", "pozn",
    "n", "l", "p", "pí", "sl", "stol",
}


class UnsupportedFormat(ValueError):
    ...


def _from_pdf(stream):
    with pdfplumber.open(stream) as pdf:
        for page in pdf.pages:
            yield from (page.extract_text() or "").splitlines()


def _from_docx(stream):
    document = Document(stream)
    for paragraph in document.paragraphs:
        yield paragraph.text
    for table in document.tables:
        for row in table.rows:
            yield " ".join(cell.text for cell in row.cells)


_EXTRACTORS = {
    ".pdf": _from_pdf,
    ".docx": _from_docx,
}

SUPPORTED_EXTENSIONS = set(_EXTRACTORS)


def extract_lines(stream: BinaryIO, extension: str) -> Iterator[str]:
    try:
        extractor = _EXTRACTORS[extension.lower()]
    except KeyError as exc:
        raise UnsupportedFormat(extension) from exc
    return extractor(stream)


def _is_real_boundary(text_before):
    if _DOTTED_ACRONYM.search(text_before):
        return False
    token = _LAST_TOKEN.search(text_before)
    if token is None:
        return True
    value = token.group(0)
    if value.isdigit():
        return len(value) > 3
    return value.casefold() not in _ABBREVIATIONS


def split_sentences(lines: Iterable[str]) -> Iterator[str]:
    text = " ".join(line.strip() for line in lines if line and line.strip())
    if not text:
        return

    cursor = 0
    for match in _BOUNDARY.finditer(text):
        if not _is_real_boundary(text[cursor:match.start()]):
            continue
        sentence = text[cursor:match.end("punct")].strip()
        if sentence:
            yield sentence
        cursor = match.end()

    tail = text[cursor:].strip()
    if tail:
        yield tail


def sentences_to_csv(sentences: Iterable[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for sentence in sentences:
        writer.writerow([sentence])
    data = buffer.getvalue()
    return BOM + data if data else ""
