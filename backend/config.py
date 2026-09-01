"""Application configuration constants."""

from pathlib import Path

# Project root (parent of backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Auto-create uploads directory if it doesn't exist

# Security limits
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
ALLOWED_PDF_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF"

# CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",  # Live Server default port
    "http://127.0.0.1:5500",
]
