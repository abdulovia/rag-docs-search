"""Markdown парсер"""

from pathlib import Path
from typing import List

from ...domain.entities.document import Document, DocumentMetadata


class MarkdownParser:
    """Парсинг Markdown документов с сохранением структуры заголовков"""

    async def parse(self, file_path: Path) -> List[Document]:
        """Парсинг Markdown файла"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            return []

        # Разбиваем по заголовкам для сохранения структуры
        sections = self._split_by_headers(content)

        documents = []
        for i, (title, section_content) in enumerate(sections):
            if not section_content.strip():
                continue

            metadata = DocumentMetadata(
                source=file_path.name,
                title=title if title else file_path.stem,
                doc_type="markdown",
                extra={"section_index": i},
            )

            documents.append(
                Document(
                    page_content=section_content.strip(),
                    metadata=metadata,
                )
            )

        # Если не удалось разбить по секциям, возвращаем как один документ
        if not documents:
            metadata = DocumentMetadata(
                source=file_path.name,
                title=file_path.stem,
                doc_type="markdown",
            )
            documents.append(
                Document(
                    page_content=content.strip(),
                    metadata=metadata,
                )
            )

        return documents

    def _split_by_headers(self, content: str) -> List[tuple[str, str]]:
        """Разбиение по заголовкам"""
        import re

        # Паттерн для заголовков (# ...)
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        sections = []
        current_title = ""
        current_content = []
        last_pos = 0

        for match in header_pattern.finditer(content):
            # Сохраняем предыдущую секцию
            if current_content:
                section_text = content[last_pos:match.start()]
                sections.append((current_title, section_text))

            current_title = match.group(2).strip()
            last_pos = match.start()
            current_content = []

        # Последняя секция
        if last_pos < len(content):
            sections.append((current_title, content[last_pos:]))

        return sections

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".md", ".markdown")
