"""PDF парсер на основе PyMuPDF"""

from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from ...domain.entities.document import Document, DocumentMetadata


class PDFParser:
    """Парсинг PDF документов с извлечением текста и метаданных"""

    async def parse(self, file_path: Path) -> List[Document]:
        """Парсинг PDF файла"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        documents = []
        pdf_doc = fitz.open(str(file_path))

        try:
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text()

                if not text.strip():
                    continue

                # Извлекаем метаданные
                metadata = DocumentMetadata(
                    source=file_path.name,
                    page=page_num + 1,
                    doc_type="pdf",
                )

                # Пытаемся извлечь заголовок из первой строки
                lines = text.strip().split("\n")
                if lines:
                    potential_title = lines[0].strip()
                    if len(potential_title) < 200:
                        metadata.title = potential_title

                documents.append(
                    Document(
                        page_content=text.strip(),
                        metadata=metadata,
                    )
                )
        finally:
            pdf_doc.close()

        return documents

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"
