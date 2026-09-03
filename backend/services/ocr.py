"""
OCR Pipeline
─────────────
Stage 1: Tesseract (primary — fast, good on clean scans)
Stage 2: EasyOCR (fallback — better on skewed/low-quality images)

Returns raw text for NuExtract extraction.
"""
import re
import os
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    _reader = None
except ImportError:
    EASYOCR_AVAILABLE = False
    _reader = None


def _get_easyocr_reader():
    global _reader
    if _reader is None and EASYOCR_AVAILABLE:
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader


def _tesseract_ocr(image_path: str) -> tuple[str, float]:
    """Run Tesseract. Returns (text, confidence 0-1)."""
    if not TESSERACT_AVAILABLE:
        return "", 0.0
    try:
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(img)
        confs = [c for c in data["conf"] if c != -1]
        avg_conf = (sum(confs) / len(confs) / 100) if confs else 0.0
        return text, avg_conf
    except Exception as e:
        return "", 0.0


def _easyocr_fallback(image_path: str) -> str:
    """Run EasyOCR as fallback. Returns joined text."""
    reader = _get_easyocr_reader()
    if not reader:
        return ""
    try:
        results = reader.readtext(image_path)
        return " ".join([r[1] for r in results])
    except Exception:
        return ""


def extract_text(file_path: str) -> dict:
    """
    Run OCR pipeline on uploaded document.
    Returns {"text": str, "method": str, "confidence": float}
    """
    ext = Path(file_path).suffix.lower()

    # For PDFs — extract first page as image (simplified: treat as image)
    # In production: use pdf2image to convert pages
    if ext == ".pdf":
        # Try Tesseract on PDF directly
        if TESSERACT_AVAILABLE:
            try:
                text = pytesseract.image_to_string(file_path)
                if text.strip():
                    return {"text": text, "method": "tesseract_pdf", "confidence": 0.8}
            except Exception:
                pass
        return {"text": "", "method": "unsupported_pdf", "confidence": 0.0}

    # Image files
    text, conf = _tesseract_ocr(file_path)

    # Sanity check: if confidence < 60% or very little text, try EasyOCR
    if conf < 0.6 or len(text.strip()) < 20:
        fallback_text = _easyocr_fallback(file_path)
        if len(fallback_text.strip()) > len(text.strip()):
            return {"text": fallback_text, "method": "easyocr_fallback", "confidence": 0.7}

    return {"text": text, "method": "tesseract", "confidence": conf}
