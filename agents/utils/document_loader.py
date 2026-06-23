"""
Document loading utility.

Extracts plain text from vendor-submitted documents so downstream agents can
read the actual content instead of just a filename/description.

Supported formats:
    - PDF                  -> pypdf
    - .docx                -> python-docx
    - .png / .jpg / .jpeg  -> OCR via pytesseract + Pillow

All optional dependencies are imported lazily and failures are handled
gracefully: if a parser (or the Tesseract binary for OCR) is unavailable, the
document is marked ``unreadable`` rather than crashing the pipeline.
"""
from __future__ import annotations

import logging
import os

from agents.config.required_documents import (
    BASE_REQUIRED_DOCUMENTS,
    AUDITED_FINANCIALS,
    GDPR_DPA,
    INSURANCE_CERTIFICATE,
)

logger = logging.getLogger(__name__)

# Max characters of extracted text kept per document (keeps LLM prompts bounded).
MAX_TEXT_CHARS = 6000

_PDF_EXTS = {".pdf"}
_DOCX_EXTS = {".docx"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# All known document types (base + conditional) used for type guessing.
_ALL_DOC_TYPES = BASE_REQUIRED_DOCUMENTS + [
    INSURANCE_CERTIFICATE,
    AUDITED_FINANCIALS,
    GDPR_DPA,
]


def _extract_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


def _extract_docx(file_path: str) -> str:
    import docx  # python-docx

    document = docx.Document(file_path)
    return "\n".join(p.text for p in document.paragraphs).strip()


def _extract_image_ocr(file_path: str) -> str:
    import pytesseract
    from PIL import Image

    with Image.open(file_path) as img:
        return pytesseract.image_to_string(img).strip()


def guess_document_type(filename: str, text: str) -> str:
    """Best-effort guess of the canonical document-type key from filename + text."""
    haystack = f"{filename}\n{text}".lower()
    for entry in _ALL_DOC_TYPES:
        for keyword in entry["keywords"]:
            if keyword in haystack:
                return entry["key"]
    return "unknown"


def load_document(file_path: str) -> dict:
    """Load a single document and return a consistent structure.

    Returns::

        {
            "filename": str,
            "doc_type_guess": str,
            "extracted_text": str,
            "extraction_status": "extracted" | "empty" | "unreadable" | "unsupported",
        }
    """
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    text = ""
    status = "extracted"

    try:
        if ext in _PDF_EXTS:
            text = _extract_pdf(file_path)
        elif ext in _DOCX_EXTS:
            text = _extract_docx(file_path)
        elif ext in _IMAGE_EXTS:
            text = _extract_image_ocr(file_path)
        else:
            logger.warning("Unsupported document format '%s' for %s", ext, filename)
            status = "unsupported"
    except ImportError as exc:
        # Parser library (or Tesseract binding) not installed.
        logger.warning("Cannot read %s: missing dependency (%s)", filename, exc)
        status = "unreadable"
    except Exception as exc:  # noqa: BLE001 - never let a bad file break the pipeline
        logger.warning("Failed to extract text from %s: %s", filename, exc)
        status = "unreadable"

    if status == "extracted" and not text:
        status = "empty"

    text = text[:MAX_TEXT_CHARS]
    return {
        "filename": filename,
        "doc_type_guess": guess_document_type(filename, text),
        "extracted_text": text,
        "extraction_status": status,
    }


def load_documents(file_paths: list[str]) -> list[dict]:
    """Load multiple documents, skipping paths that no longer exist."""
    loaded: list[dict] = []
    for path in file_paths or []:
        if not path or not os.path.exists(path):
            logger.warning("Document path does not exist: %s", path)
            loaded.append(
                {
                    "filename": os.path.basename(str(path)),
                    "doc_type_guess": "unknown",
                    "extracted_text": "",
                    "extraction_status": "unreadable",
                }
            )
            continue
        loaded.append(load_document(path))
    return loaded
