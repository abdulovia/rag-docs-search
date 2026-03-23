"""Unit тесты для prompt registry"""

from pathlib import Path

import pytest

from src.application.services.prompt_registry import PromptRegistry


@pytest.fixture
def registry():
    templates_dir = Path("src/infrastructure/prompts/templates")
    return PromptRegistry(templates_dir=templates_dir)


def test_render_basic_prompt(registry):
    prompt = registry.render(
        "rag/answer_generation",
        context="Test context",
        question="Test question",
    )
    assert "Test context" in prompt
    assert "Test question" in prompt


def test_render_prompt_with_citations(registry):
    prompt = registry.render(
        "rag/answer_with_citations",
        context="Context",
        question="Question",
    )
    assert "[N]" in prompt


def test_render_prompt_with_history(registry):
    from src.domain.entities.response import Message
    history = [Message(role="user", content="Hello")]
    prompt = registry.render(
        "rag/answer_generation",
        context="Context",
        question="Question",
        conversation_history=history,
    )
    assert "user: Hello" in prompt


def test_render_grading_prompt(registry):
    score_text = registry.render(
        "grading/document_relevance",
        question="What is RAG?",
        document="RAG is retrieval augmented generation.",
    )
    assert "What is RAG?" in score_text


def test_invalid_prompt_name(registry):
    with pytest.raises(ValueError):
        registry.render("nonexistent/prompt", context="test")
