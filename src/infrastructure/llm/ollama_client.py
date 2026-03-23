"""Ollama LLM клиент"""

import json
from typing import Any, AsyncIterator, Type, TypeVar

import httpx

T = TypeVar("T")


class OllamaClient:
    """Ollama API клиент для генерации текста"""

    def __init__(
        self,
        model: str = "llama3.2:3b-instruct-fp16",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        """Генерация ответа"""
        response = await self._client.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        return response.json()["response"]

    async def generate_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Потоковая генерация ответа"""
        async with self._client.stream(
            "POST",
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", 0.0),
                    "num_predict": kwargs.get("max_tokens", 2048),
                },
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        """Генерация структурированного ответа"""
        schema = response_model.model_json_schema()

        structured_prompt = f"""{prompt}

Respond ONLY with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

JSON:"""

        response_text = await self.generate(
            structured_prompt,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2048),
        )

        # Очищаем ответ от markdown обёрток
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)
        return response_model(**data)

    async def close(self):
        """Закрытие клиента"""
        await self._client.aclose()
