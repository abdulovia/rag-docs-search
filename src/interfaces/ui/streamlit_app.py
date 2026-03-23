"""Streamlit UI для RAG Document Search"""

import streamlit as st
import httpx
import os

# API URL - можно переопределить через переменную окружения
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Document Search",
    page_icon="📚",
    layout="wide",
)

st.title("📚 RAG Document Search")


def get_documents():
    """Получить список документов через API"""
    try:
        response = httpx.get(f"{API_URL}/api/v1/documents", timeout=10)
        if response.status_code == 200:
            return response.json().get("documents", [])
    except Exception as e:
        st.error(f"Ошибка загрузки документов: {e}")
    return []


def upload_document(file):
    """Загрузить документ через API"""
    try:
        files = {"file": (file.name, file.getvalue())}
        response = httpx.post(
            f"{API_URL}/api/v1/documents/upload",
            files=files,
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка: {response.text}")
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
    return None


def delete_document(filename):
    """Удалить документ через API"""
    try:
        response = httpx.delete(
            f"{API_URL}/api/v1/documents/{filename}",
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка: {response.text}")
    except Exception as e:
        st.error(f"Ошибка удаления: {e}")
    return None


def ask_question(question, top_k=5, enable_web_search=False):
    """Задать вопрос через API"""
    try:
        response = httpx.post(
            f"{API_URL}/api/v1/ask",
            json={
                "question": question,
                "top_k": top_k,
                "enable_web_search": enable_web_search,
            },
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка: {response.text}")
    except Exception as e:
        st.error(f"Ошибка: {e}")
    return None


# Sidebar для управления документами
with st.sidebar:
    st.header("📄 Документы")

    # Загрузка нового документа
    uploaded_file = st.file_uploader(
        "Загрузить PDF или Markdown",
        type=["pdf", "md", "markdown"],
    )

    if uploaded_file:
        if st.button("📤 Загрузить и проиндексировать", use_container_width=True):
            with st.spinner("Индексация..."):
                result = upload_document(uploaded_file)
                if result:
                    st.success(f"✓ {result.get('chunks_count', 0)} чанков создано")
                    st.rerun()

    st.divider()

    # Список всех документов
    st.subheader("📋 Индексированные документы")

    documents = get_documents()

    if not documents:
        st.info("Нет документов. Загрузите файл выше.")
    else:
        for doc in documents:
            col1, col2 = st.columns([4, 1])

            with col1:
                chunks = doc.get("chunks_count", 0)
                status = "✅" if doc.get("indexed") else "⏳"
                st.text(f"{status} {doc['filename']} ({chunks} чанков)")

            with col2:
                if st.button("🗑️", key=f"del_{doc['filename']}", help="Удалить"):
                    with st.spinner("Удаление..."):
                        result = delete_document(doc["filename"])
                        if result:
                            st.success(f"Удалено {result.get('chunks_deleted', 0)} чанков")
                            st.rerun()

    st.divider()

    # Настройки
    st.header("⚙️ Настройки")
    top_k = st.slider("Количество источников", 1, 10, 5)
    enable_web_search = st.toggle("🌐 Веб-поиск", help="Искать в интернете если нет в документах")

    if st.button("🔄 Переиндексировать всё", use_container_width=True):
        with st.spinner("Переиндексация..."):
            try:
                response = httpx.post(
                    f"{API_URL}/api/v1/documents/reindex",
                    timeout=300,
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Переиндексировано: {result.get('total_chunks', 0)} чанков")
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")

# Основной чат
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Источники"):
                for src in message["sources"]:
                    page_info = f" (стр. {src['page']})" if src.get("page") else ""
                    st.write(f"[{src['index']}] {src['source']}{page_info}")

# Ввод вопроса
if prompt := st.chat_input("Задайте вопрос о ваших документах..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Поиск..."):
            result = ask_question(prompt, top_k, enable_web_search)

            if result:
                # Отображение источника
                source_label = result.get("metadata", {}).get("source_label", "")
                if source_label:
                    if source_label == "Из документов":
                        st.success(f"📄 {source_label}")
                    elif source_label == "Из интернета":
                        st.info(f"🌐 {source_label}")
                    elif source_label == "Сгенерировано":
                        st.warning(f"🤖 {source_label}")
                
                st.markdown(result["answer"])

                # Отображение источников
                if result.get("citations"):
                    with st.expander("📚 Источники"):
                        for cite in result["citations"]:
                            page_info = f" (стр. {cite['page']})" if cite.get("page") else ""
                            st.write(f"[{cite['index']}] {cite['source']}{page_info}")

                # Информация о времени
                if result.get("processing_time_ms"):
                    st.caption(f"⏱️ {result['processing_time_ms']/1000:.1f} сек")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("citations", []),
                })
            else:
                st.error("Не удалось получить ответ")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Ошибка при обработке запроса",
                })
