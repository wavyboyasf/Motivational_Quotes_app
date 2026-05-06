"""
ingest.py — Indeksowanie PDF-ów do bazy ChromaDB

Skanuje foldery z książkami, wyciąga tekst z PDF-ów (zachowując numery stron),
dzieli na chunki i zapisuje embeddingi do ChromaDB.

Użycie:
    python ingest.py          # indeksuj wszystkie książki
    python ingest.py --force  # wymuś ponowne indeksowanie (kasuje starą bazę)
"""

import os
import sys
import shutil
import time
import pymupdf
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

from config import (
    BASE_DIR,
    CHROMA_DB_DIR,
    BOOK_FOLDERS,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SKIP_FILES,
)


def clean_book_title(filename: str) -> str:
    """Wyciąga czytelny tytuł książki z nazwy pliku."""
    title = filename.replace(".pdf", "")
    # Usuń typowe prefiksy z portali
    for prefix in ["dokumen.pub_", "ebin.pub_"]:
        if title.startswith(prefix):
            title = title[len(prefix):]
    # Usuń numery ISBN i inne śmieci z końca
    # Szukaj wzorców typu -9780... lub _9780...
    import re
    title = re.split(r'[-_]\d{10,}', title)[0]
    # Zamień myślniki i podkreślenia na spacje
    title = title.replace("-", " ").replace("_", " ")
    # Usuń "(Z-Library)" i podobne
    title = re.sub(r'\(Z[- ]Library\)', '', title)
    title = re.sub(r'\(PDF Room\)', '', title)
    # Usuń nadmiarowe spacje
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Wyciąga tekst z PDF-a strona po stronie.
    Zwraca listę słowników: {page: int, text: str}
    """
    pages = []
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text = page.get_text()
            if text and text.strip():
                pages.append({
                    "page": page.number + 1,  # 1-indexed
                    "text": text.strip(),
                })
        doc.close()
    except Exception as e:
        print(f"  ⚠ Błąd odczytu PDF: {e}")
    return pages


def find_all_pdfs() -> list[dict]:
    """Znajduje wszystkie PDF-y do indeksowania (pomijając duplikaty)."""
    pdf_files = []
    for folder in BOOK_FOLDERS:
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"  ⚠ Folder nie istnieje: {folder}")
            continue
        category = folder_path.name
        for pdf_file in folder_path.rglob("*.pdf"):
            if pdf_file.name in SKIP_FILES:
                print(f"  ⏭ Pomijam duplikat: {pdf_file.name}")
                continue
            pdf_files.append({
                "path": str(pdf_file),
                "filename": pdf_file.name,
                "category": category,
                "title": clean_book_title(pdf_file.name),
            })
    return pdf_files


def create_documents(pdf_info: dict) -> list[Document]:
    """Tworzy dokumenty LangChain z PDF-a, z metadanymi."""
    pages = extract_text_from_pdf(pdf_info["path"])
    if not pages:
        return []

    documents = []
    for page_data in pages:
        doc = Document(
            page_content=page_data["text"],
            metadata={
                "book_title": pdf_info["title"],
                "page_number": page_data["page"],
                "category": pdf_info["category"],
                "source_file": pdf_info["filename"],
            },
        )
        documents.append(doc)
    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Dzieli dokumenty na mniejsze chunki, zachowując metadane."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  📚 Book Quote Finder — Indeksowanie PDF-ów")
    print("=" * 60)

    # Sprawdź czy baza już istnieje
    if os.path.exists(CHROMA_DB_DIR):
        if force:
            print("\n🗑️  Usuwam starą bazę (--force)...")
            shutil.rmtree(CHROMA_DB_DIR)
        else:
            print("\n✅ Baza ChromaDB już istnieje.")
            print("   Użyj --force aby wymusić ponowne indeksowanie.")
            return

    # Znajdź wszystkie PDF-y
    print("\n🔍 Szukam plików PDF...\n")
    pdf_files = find_all_pdfs()
    print(f"\n📄 Znaleziono {len(pdf_files)} książek do indeksowania.\n")

    if not pdf_files:
        print("❌ Nie znaleziono żadnych PDF-ów!")
        return

    # Inicjalizuj embeddings
    print(f"🤖 Inicjalizuję model embeddingów: {EMBEDDING_MODEL}")
    print("   (pierwsze uruchomienie może potrwać — model jest pobierany)\n")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    # Przetwarzaj PDF-y
    all_chunks = []
    for i, pdf_info in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] 📖 {pdf_info['title']}")
        print(f"          Kategoria: {pdf_info['category']}")

        start_time = time.time()
        documents = create_documents(pdf_info)
        chunks = chunk_documents(documents)
        all_chunks.extend(chunks)

        elapsed = time.time() - start_time
        print(f"          → {len(documents)} stron → {len(chunks)} chunków ({elapsed:.1f}s)")
        print()

    print(f"📊 Łącznie: {len(all_chunks)} chunków do zaindeksowania.")
    print(f"   Zapisuję do ChromaDB (to może potrwać kilka minut)...\n")

    # Zapisz do ChromaDB w batchach (ChromaDB ma limit na batch)
    BATCH_SIZE = 500
    vectorstore = None

    for batch_start in range(0, len(all_chunks), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(all_chunks))
        batch = all_chunks[batch_start:batch_end]
        print(f"   Zapisuję batch {batch_start+1}-{batch_end} z {len(all_chunks)}...")

        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=CHROMA_DB_DIR,
                collection_name="book_quotes",
            )
        else:
            vectorstore.add_documents(batch)

    print(f"\n✅ Indeksowanie zakończone!")
    print(f"   Baza zapisana w: {CHROMA_DB_DIR}")
    print(f"   Łączna liczba chunków: {len(all_chunks)}")
    print(f"\n   Teraz możesz uruchomić: python quote_finder.py")


if __name__ == "__main__":
    main()
