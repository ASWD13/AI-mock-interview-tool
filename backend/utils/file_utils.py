"""File utilities for resume handling."""

import os
import tempfile
import base64
from typing import Optional


def save_temp_file(content: bytes, suffix: str = ".tmp") -> str:
    """Save bytes to a temporary file and return the path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, 'wb') as f:
        f.write(content)
    return path


def decode_base64_to_file(b64_string: str, suffix: str = ".wav") -> str:
    """Decode base64 string to a temp file."""
    data = base64.b64decode(b64_string)
    return save_temp_file(data, suffix=suffix)


def cleanup_temp_file(path: str):
    """Remove a temporary file."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def detect_file_type(filename: str, content: bytes) -> str:
    """Detect file type via extension + magic bytes."""
    ext = get_file_extension(filename)

    # Check magic bytes
    if content[:4] == b'%PDF':
        return 'pdf'
    if content[:2] == b'PK':  # DOCX is a ZIP
        return 'docx'

    # Fallback to extension
    ext_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'docx',
        '.txt': 'txt',
        '.text': 'txt',
    }
    return ext_map.get(ext, 'txt')
