"""
quote_finder.py — Wyszukiwarka Cytatów z Książek

Interaktywne narzędzie konsolowe. Podajesz temat po polsku,
dostajesz trafny cytat po angielsku z tytułem książki i numerem strony.

Użycie:
    python quote_finder.py
"""

import sys
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.schema import HumanMessage, SystemMessage

from config import (
    CHROMA_DB_DIR,
    EMBEDDING_MODEL,
    LLM_MODEL,
    TOP_K_RESULTS,
    SYSTEM_PROMPT,
)


def load_vectorstore():
    """Ładuje istniejącą bazę ChromaDB."""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="book_quotes",
    )
    return vectorstore


def format_context(results) -> str:
    """Formatuje wyniki wyszukiwania jako kontekst dla LLM-a."""
    context_parts = []
    for i, doc in enumerate(results, 1):
        meta = doc.metadata
        context_parts.append(
            f"--- Fragment {i} ---\n"
            f"Książka: {meta.get('book_title', 'Nieznana')}\n"
            f"Strona: {meta.get('page_number', '?')}\n"
            f"Kategoria: {meta.get('category', '?')}\n"
            f"Treść:\n{doc.page_content}\n"
        )
    return "\n".join(context_parts)


def query_llm(llm, context: str, user_query: str) -> str:
    """Wysyła zapytanie do LLM-a z kontekstem z książek."""
    user_message = (
        f"Temat podany przez użytkownika: {user_query}\n\n"
        f"Oto fragmenty książek, na podstawie których masz odpowiedzieć:\n\n"
        f"{context}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    return response.content


def print_banner():
    """Wyświetla baner powitalny."""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        📚 Book Quote Finder — Wyszukiwarka Cytatów      ║")
    print("║                                                          ║")
    print("║   Podaj temat po polsku, a znajdę trafny cytat          ║")
    print("║   z Twojej biblioteki książek.                           ║")
    print("║                                                          ║")
    print("║   Wpisz 'quit' lub 'q' aby zakończyć.                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def main():
    print_banner()

    # Sprawdź czy baza istnieje
    import os
    if not os.path.exists(CHROMA_DB_DIR):
        print("❌ Baza ChromaDB nie istnieje!")
        print("   Najpierw uruchom: python ingest.py")
        sys.exit(1)

    # Ładowanie komponentów
    print("⏳ Ładuję bazę danych i model LLM...")
    vectorstore = load_vectorstore()
    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=0.3,  # niska temperatura — precyzyjne cytaty
    )
    print(f"✅ Gotowe! Model: {LLM_MODEL}\n")

    # Pętla interaktywna
    while True:
        try:
            query = input("🔍 Podaj temat/hasło (lub 'quit'): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Do zobaczenia!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "q", "exit", "koniec"):
            print("\n👋 Do zobaczenia!")
            break

        print(f"\n⏳ Szukam cytatów na temat: \"{query}\"...\n")

        try:
            # Wyszukaj najbardziej trafne fragmenty
            results = vectorstore.similarity_search(query, k=TOP_K_RESULTS)

            if not results:
                print("😕 Nie znaleziono trafnych fragmentów w bazie.\n")
                continue

            # Przygotuj kontekst i wyślij do LLM-a
            context = format_context(results)
            answer = query_llm(llm, context, query)

            # Wyświetl odpowiedź
            print("─" * 60)
            print(answer)
            print("─" * 60)
            print()

        except Exception as e:
            print(f"❌ Błąd: {e}")
            print("   Upewnij się, że Ollama jest uruchomiony (ollama serve)\n")


if __name__ == "__main__":
    main()
