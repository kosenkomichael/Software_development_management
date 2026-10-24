import base64


def pdf_file_part(filename: str, data: bytes) -> dict:
    """PDF as an inline base64 file content part."""
    b64 = base64.b64encode(data).decode()
    return {
        "type": "file",
        "file": {
            "filename": filename,
            "file_data": f"data:application/pdf;base64,{b64}",
        },
    }


def image_url_part(data: bytes, mime: str) -> dict:
    """Image as an inline base64 image_url content part."""
    b64 = base64.b64encode(data).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    }
