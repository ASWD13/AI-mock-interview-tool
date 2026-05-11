"""Resume parser service — PDF, DOCX, TXT extraction."""

import io
from typing import Optional


async def parse_resume(content: bytes, file_type: str) -> str:
    """Parse resume content and extract raw text.

    Args:
        content: Raw file bytes
        file_type: One of 'pdf', 'docx', 'txt'

    Returns:
        Extracted raw text string
    """
    if file_type == "pdf":
        return _parse_pdf(content)
    elif file_type == "docx":
        return _parse_docx(content)
    elif file_type == "txt":
        return content.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _parse_pdf(content: bytes) -> str:
    """Extract text from PDF using pdfplumber, with pytesseract OCR fallback."""
    import pdfplumber

    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

    # OCR fallback if pdfplumber yields < 100 chars
    if len(text.strip()) < 100:
        try:
            text = _ocr_pdf(content)
        except Exception:
            pass  # Return whatever we have

    return text.strip()


def _parse_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _ocr_pdf(content: bytes) -> str:
    """OCR fallback for scanned PDFs using pytesseract."""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(content)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
        return text.strip()
    except ImportError:
        # pdf2image not available, try basic pytesseract
        return ""
    except Exception:
        return ""
