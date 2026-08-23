import re


SECTION_PATTERN = re.compile(
    r"(?m)^\s*(\d+)\.\s+(.+?)\s*$"
)


def split_into_sections(text: str) -> list[dict]:
    """
    Split cleaned document text into numbered sections.

    Example:

        1. Machine Overview
        Some content...

        2. Operating Parameters
        Some content...

    becomes:

        [
            {
                "section_number": 1,
                "section": "Machine Overview",
                "text": "..."
            },
            ...
        ]
    """

    matches = list(SECTION_PATTERN.finditer(text))

    if not matches:
        return [
            {
                "section_number": None,
                "section": "Unknown",
                "text": text.strip(),
            }
        ]

    sections = []

    for index, match in enumerate(matches):

        section_number = int(match.group(1))
        section_name = match.group(2).strip()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        section_text = text[start:end].strip()

        if section_text:
            sections.append(
                {
                    "section_number": section_number,
                    "section": section_name,
                    "text": section_text,
                }
            )

    return sections


def chunk_document(document: dict) -> list[dict]:
    """
    Convert one preprocessed document into section-level chunks.
    """

    sections = split_into_sections(document["text"])

    chunks = []

    for chunk_index, section in enumerate(sections, start=1):

        chunk = {
            "chunk_id": (
                f"{document['document_id']}"
                f"_page_{document['page']}"
                f"_chunk_{chunk_index}"
            ),
            "text": section["text"],
            "section": section["section"],
            "section_number": section["section_number"],
            "page": document["page"],
            "source": document["source"],
            "document_id": document["document_id"],
            "document_name": document["document_name"],
            "document_type": document["document_type"],
            "machine_type": document["machine_type"],
        }

        chunks.append(chunk)

    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk all preprocessed documents.
    """

    all_chunks = []

    for document in documents:
        chunks = chunk_document(document)
        all_chunks.extend(chunks)

    return all_chunks