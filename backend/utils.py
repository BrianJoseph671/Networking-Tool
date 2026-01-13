import pdfplumber
import io
from typing import Optional


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from a PDF file

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Extracted text content
    """
    try:
        text_content = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)

        return "\n\n".join(text_content)

    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def is_valid_pdf(file_bytes: bytes) -> bool:
    """
    Check if the provided bytes represent a valid PDF file

    Args:
        file_bytes: File content as bytes

    Returns:
        True if valid PDF, False otherwise
    """
    # PDF files start with %PDF-
    return file_bytes.startswith(b'%PDF-')
