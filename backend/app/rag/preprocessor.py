from .cleaner import clean_text
from .metadata import get_metadata, detect_section


def preprocess_document(document: dict) -> dict:
    """
    Clean extracted PDF text and attach metadata.
    """

    cleaned_text = clean_text(document["text"])

    metadata = get_metadata(document["document_id"])

    section = detect_section(cleaned_text)

    return {
        "text": cleaned_text,
        "page": document["page"],
        "source": document["source"],
        "document_id": document["document_id"],
        "document_name": metadata["document_name"],
        "document_type": metadata["document_type"],
        "machine_type": metadata["machine_type"],
        "section": section,
    }