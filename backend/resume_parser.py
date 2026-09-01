"""
PDF resume text extraction using PyMuPDF.

Handles validation, multi-page extraction, text cleaning, and clear errors.
"""

import re
from dataclasses import dataclass

import pymupdf

from backend.config import (
    ALLOWED_PDF_CONTENT_TYPES,
    ALLOWED_PDF_EXTENSION,
    MAX_UPLOAD_SIZE_BYTES,
    PDF_MAGIC_BYTES,
)


class ResumeParserError(Exception):
    """Base error for resume parsing failures."""


class InvalidPDFError(ResumeParserError):
    """Raised when the uploaded file is not a valid PDF."""


class EmptyPDFError(ResumeParserError):
    """Raised when the PDF contains no extractable text."""


class FileTooLargeError(ResumeParserError):
    """Raised when the uploaded file exceeds the size limit."""


@dataclass
class ParsedResume:
    """Structured result from PDF text extraction."""

    text: str
    page_count: int
    character_count: int


def validate_pdf_upload(
    filename: str | None,
    content_type: str | None,
    file_bytes: bytes,
) -> None:
    """
    Validate uploaded file before parsing.

    Checks extension, content type, magic bytes, and file size.
    """
    if not file_bytes:
        raise InvalidPDFError("No file was uploaded or the file is empty.")

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_mb} MB.")

    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise InvalidPDFError("Invalid file type. Only PDF files are accepted.")

    if filename:
        if not filename.lower().endswith(ALLOWED_PDF_EXTENSION):
            raise InvalidPDFError("Invalid file extension. Only .pdf files are accepted.")

    if content_type and content_type not in ALLOWED_PDF_CONTENT_TYPES:
        # Some browsers send application/octet-stream; magic-byte check is authoritative.
        if content_type != "application/octet-stream":
            raise InvalidPDFError("Invalid content type. Only PDF files are accepted.")


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and remove noisy characters from extracted text."""
    if not raw_text:
        return ""

    # Replace non-breaking spaces
    text = raw_text.replace("\xa0", " ")

    # Collapse multiple spaces/tabs on the same line
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line breaks (max two consecutive newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line, then overall
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> ParsedResume:
    """
    Extract text from a PDF byte stream.

    Supports multi-page resumes. Raises clear errors for invalid or empty PDFs.
    """
    doc = None
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        page_count = doc.page_count

        if page_count == 0:
            raise EmptyPDFError("The PDF has no pages.")

        page_texts: list[str] = []
        for page_index in range(page_count):
            page = doc.load_page(page_index)
            page_texts.append(page.get_text("text"))

        raw_text = "\n".join(page_texts)
        cleaned = clean_text(raw_text)

        if not cleaned:
            raise EmptyPDFError(
                "No text could be extracted from this PDF. "
                "It may be image-only or scanned without OCR."
            )

        return ParsedResume(
            text=cleaned,
            page_count=page_count,
            character_count=len(cleaned),
        )

    except pymupdf.FileDataError as exc:
        raise InvalidPDFError("The uploaded file is corrupted or not a valid PDF.") from exc
    except ResumeParserError:
        raise
    except Exception as exc:
        raise InvalidPDFError(f"Failed to read PDF: {exc}") from exc
    finally:
        if doc is not None:
            doc.close()


def parse_resume_upload(
    filename: str | None,
    content_type: str | None,
    file_bytes: bytes,
) -> ParsedResume:
    """Validate an uploaded resume file and extract its text."""
    validate_pdf_upload(filename, content_type, file_bytes)
    return extract_text_from_pdf(file_bytes)
