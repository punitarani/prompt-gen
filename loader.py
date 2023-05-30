"""loader.py"""

import fitz

from utils import format_text


def read_pdf(data: bytes) -> str:
    """
    Read PDF data and return text
    :param data: PDF data as bytes
    :return: Text string from PDF
    """

    with fitz.Document(stream=data) as doc:
        text_pages = [page.get_text().encode("utf-8") for page in doc]
        text = b"\n".join(text_pages).decode("utf-8")
    text = format_text(text)
    return text
