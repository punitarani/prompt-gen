"""loader.py"""

import re

import fitz

from utils import format_text


def read_file(data: bytes, extension: str) -> str:
    """
    Read file data and return text
    :param data: File data as bytes string
    :param extension: File type extension
    :return: Text string from file
    """
    if extension == "pdf":
        return read_pdf(data)
    elif extension == "txt":
        return format_text(data.decode("utf-8"))
    else:
        raise NotImplementedError(f"File type {type} not supported")


def read_pdf(data: bytes) -> str:
    """
    Read PDF data and return text
    :param data: PDF data as bytes string
    :return: Text string from PDF
    """

    with fitz.Document(stream=data) as doc:
        text_pages = [page.get_text().encode("utf-8") for page in doc]
        text = b"\n".join(text_pages).decode("utf-8")
    text = format_text(text)
    return text


def chunk_text(text: str, min_chars: int = 40, max_chars: int = 160) -> list[str]:
    """
    Chunk text into smaller chunks
    :param text: The text to chunk
    :param min_chars: The minimum number of characters per chunk
    :param max_chars: The maximum number of characters per chunk
    :return: A list of text chunks
    """
    # Regular expression pattern to split text into sentences
    sentence_pattern = r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s"

    # Splitting the text into sentences using the pattern
    sentences = re.split(sentence_pattern, text)

    # List to store the chunks of sentences
    chunks = []

    def split_sentences(sentence_list, current_chunk):
        """
        Split sentences into chunks recursively
        :param sentence_list: List of sentences
        :param current_chunk: The current chunk of sentences
        """
        if len(current_chunk) > max_chars:
            # If the current chunk exceeds the max_chars limit, split it recursively
            chunks.append(current_chunk[:max_chars].strip())
            remaining_text = current_chunk[max_chars:]
            split_sentences(sentence_list, remaining_text)
        elif len(sentence_list) > 0:
            # If there are remaining sentences, add them to the current chunk
            current_sentence = sentence_list.pop(0)
            if len(current_chunk) + len(current_sentence) <= max_chars:
                current_chunk += current_sentence
            else:
                # If the current chunk reaches the max_chars limit, add it to the chunks list
                if len(current_chunk) >= min_chars:
                    chunks.append(current_chunk.strip())
                current_chunk = current_sentence
            split_sentences(sentence_list, current_chunk)
        else:
            # Add the last chunk to the list
            if len(current_chunk) >= min_chars:
                chunks.append(current_chunk.strip())

    split_sentences(sentences, "")
    return chunks
