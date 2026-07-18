"""Document loaders: file -> Document with pages.
All loaders fulfill the BAseLoader contract, so they are interchangebale."""

from abc import ABC, abstractmethod
from pathlib import Path

import fitz

from ragcore.models import Document, Page

class BaseLoader(ABC):
    """Read a file and return a Document with per-page text"""
    @abstractmethod
    def load(self, path:str)-> Document:
        """Load a file and return a Document with per-page text"""
        ...
    
class PDFLoader(BaseLoader):
    """Loads PDFs via PyMuPDF (fitz). Our Phase 1 load_pdf, now with a contract."""
    
    def load(self, path:str) -> Document:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        doc = fitz.open(path)
        pages = [Page(number=i+1, text=page.get_text()) for i, page in enumerate(doc)]
        doc.close()
        
        return Document(id = p.stem, title=p.stem, source_path=str(p), pages=pages)
        