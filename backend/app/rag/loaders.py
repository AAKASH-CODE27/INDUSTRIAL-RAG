from pathlib import Path
from pypdf import PdfReader


def load_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from every page of a PDF.

    Returns one dictionary per page so that page-level
    source information is preserved for RAG citations.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))

    documents = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        documents.append(
            {
                "text": text.strip(),
                "page": page_number,
                "source": path.name,
                "document_id": path.stem,
            }
        )

    return documents


def load_documents(directory: str) -> list[dict]:
    """
    Load every PDF from a directory.
    """

    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(
            f"Documents directory not found: {directory_path}"
        )

    pdf_files = sorted(directory_path.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {directory_path}"
        )

    all_documents = []

    for pdf_file in pdf_files:
        pages = load_pdf(str(pdf_file))
        all_documents.extend(pages)

    return all_documents