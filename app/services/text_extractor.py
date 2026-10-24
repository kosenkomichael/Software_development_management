import zipfile
from io import BytesIO

from docx import Document
from pptx import Presentation

IMAGE_MIME_BY_EXT = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}


def extract_text(data: bytes, content_type: str) -> str:
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


def extract_images(data: bytes, content_type: str) -> list[tuple[bytes, str]]:
    """Extract embedded images as (raw_bytes, mime) in document order."""
    if content_type == "application/pdf":
        return _images_from_pdf(data)
    if content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ):
        return _images_from_office(data)
    return []


def _images_from_pdf(data: bytes) -> list[tuple[bytes, str]]:
    import pymupdf

    images: list[tuple[bytes, str]] = []
    seen_xrefs: set[int] = set()
    with pymupdf.Document(stream=data, filetype="pdf") as doc:
        for page in doc:
            for info in page.get_images(full=True):
                xref = info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                pix = pymupdf.Pixmap(doc, xref)
                if pix.colorspace and pix.colorspace.n > 3:  # CMYK etc.
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                if pix.alpha:
                    pix = pymupdf.Pixmap(pix, 0)
                images.append((pix.tobytes("jpeg"), "image/jpeg"))
    return images


def _images_from_office(data: bytes) -> list[tuple[bytes, str]]:
    images: list[tuple[bytes, str]] = []
    with zipfile.ZipFile(BytesIO(data)) as zf:
        for name in zf.namelist():
            dot = name.rfind(".")
            if dot == -1:
                continue
            mime = IMAGE_MIME_BY_EXT.get(name[dot:].lower())
            if mime is not None and (
                name.startswith("word/media/") or name.startswith("ppt/media/")
            ):
                images.append((zf.read(name), mime))
    return images


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
