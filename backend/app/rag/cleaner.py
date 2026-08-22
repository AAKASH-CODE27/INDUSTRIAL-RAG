import re


def clean_text(text: str) -> str:
    """
    Clean text extracted from PDF files.
    """

    if not text:
        return ""

    # Normalize Windows/Linux line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove the synthetic project notice from our generated PDFs
    text = re.sub(
        r"Synthetic project reference document for Phase 5 RAG testing\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()