from io import BytesIO

from docx import Document
from pdfminer.high_level import extract_text as _pdf_extract
from pptx import Presentation


def extract_text(data: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return _from_pdf(data)
    if content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return _from_docx(data)
    if content_type in (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
    ):
        return _from_pptx(data)
    raise ValueError(f"Unsupported content type for text extraction: {content_type}")


def _from_pdf(data: bytes) -> str:
    return _pdf_extract(BytesIO(data)) or ""


def _from_docx(data: bytes) -> str:
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _from_pptx(data: bytes) -> str:
    prs = Presentation(BytesIO(data))
    parts: list[str] = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        parts.append(text)
    return "\n".join(parts)
