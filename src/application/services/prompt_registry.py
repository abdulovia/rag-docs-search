"""Prompt Registry — управление Jinja2 шаблонами промптов"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class PromptRegistry:
    """Централизованное управление промптами с Jinja2"""

    def __init__(self, templates_dir: Path):
        self._templates_dir = Path(templates_dir)
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._metadata = self._load_metadata()

    def render(self, prompt_name: str, **kwargs: Any) -> str:
        """Рендер промпта с параметрами

        Args:
            prompt_name: Имя шаблона (например "rag/answer_generation")
            **kwargs: Параметры для шаблона

        Returns:
            Отрендеренный промпт
        """
        template_path = f"{prompt_name}.jinja2"

        try:
            template = self._env.get_template(template_path)
        except TemplateNotFound:
            raise ValueError(f"Prompt template not found: {prompt_name}")

        return template.render(**kwargs)

    def list_prompts(self) -> list[str]:
        """Список доступных промптов"""
        return list(self._metadata.keys())

    def get_prompt_info(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """Информация о промпте"""
        return self._metadata.get(prompt_name)

    def _load_metadata(self) -> Dict[str, Any]:
        """Загрузка метаданных промптов"""
        metadata_path = self._templates_dir / "metadata.yaml"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
