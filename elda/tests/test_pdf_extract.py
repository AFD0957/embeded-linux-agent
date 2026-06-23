"""Tests for PDF extract fallback chain."""

from __future__ import annotations

from elda.ingest.pdf_extract import available_pdf_backends


def test_available_pdf_backends_is_list():
    assert isinstance(available_pdf_backends(), list)
