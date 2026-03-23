"""Web Search через DuckDuckGo (ddgs)"""

from typing import List

from ...domain.entities.document import Document, DocumentMetadata


class DuckDuckGoSearch:
    """Веб-поиск через DuckDuckGo"""

    async def search(self, query: str, max_results: int = 5) -> List[Document]:
        """Поиск в DuckDuckGo"""
        try:
            from ddgs import DDGS

            results = []
            ddgs = DDGS()
            search_results = ddgs.text(query, max_results=max_results)

            for r in search_results:
                metadata = DocumentMetadata(
                    source=r.get("href", "web"),
                    doc_type="web_search",
                    title=r.get("title", ""),
                )

                results.append(
                    Document(
                        page_content=r.get("body", ""),
                        metadata=metadata,
                    )
                )

            return results
        except Exception as e:
            print(f"Web search error: {e}")
            return []
