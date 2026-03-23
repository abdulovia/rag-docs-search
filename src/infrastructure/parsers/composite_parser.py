"""Композитный парсер — выбирает парсер по расширению файла"""

from pathlib import Path
from typing import List, Optional

from ...domain.entities.document import Document
from ...domain.ports import DocumentParser as DocumentParserPort
from .markdown_parser import MarkdownParser
from .pdf_parser import PDFParser


class CompositeParser:
    """Композитный парсер, выбирает нужный парсер по расширению файла"""

    def __init__(self):
        self._parsers: List[DocumentParserPort] = [
            PDFParser(),
            MarkdownParser(),
        ]

    async def parse(self, file_path: Path) -> List[Document]:
        """Парсинг файла с автоматическим выбором парсера"""
        parser = self._get_parser(file_path)
        if parser is None:
            raise ValueError(f"No parser available for: {file_path.suffix}")
        return await parser.parse(file_path)

    def supports(self, file_path: Path) -> bool:
        """Проверяет, поддерживается ли формат файла"""
        return self._get_parser(file_path) is not None

    def _get_parser(self, file_path: Path) -> Optional[DocumentParserPort]:
        """Поиск подходящего парсера"""
        for parser in self._parsers:
            if parser.supports(file_path):
                return parser
        return None
