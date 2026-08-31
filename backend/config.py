"""Application configuration constants."""

from pathlib import Path

# Project root (parent of backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"

# Security limits
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
ALLOWED_PDF_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF"
