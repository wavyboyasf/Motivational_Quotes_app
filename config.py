"""
Konfiguracja Book Quote Finder
"""
import os

# ── Ścieżki ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# Foldery z książkami do indeksowania
BOOK_FOLDERS = [
    os.path.join(BASE_DIR, "communication"),
    os.path.join(BASE_DIR, "emotional-intelligence"),
    os.path.join(BASE_DIR, "habits"),
    os.path.join(BASE_DIR, "mental-health"),
    os.path.join(BASE_DIR, "thinking"),
]

# ── Modele Ollama ─────────────────────────────────────────────────────────────
LLM_MODEL = "gemma3:4b"
EMBEDDING_MODEL = "nomic-embed-text"

# ── Parametry chunkowania ─────────────────────────────────────────────────────
CHUNK_SIZE = 1000        # znaków na chunk
CHUNK_OVERLAP = 200      # overlap między chunkami
TOP_K_RESULTS = 5        # ile chunków pobieramy z bazy

# ── Duplikaty do pominięcia ───────────────────────────────────────────────────
# Pliki do pominięcia (duplikaty / gorsze wersje tych samych książek)
SKIP_FILES = [
    # 7 Habits — zachowujemy wersję 30th anniversary edition
    "Seven Habits of Highly Effective People (Covey, Stephen R) (Z-Library).pdf",
    "The Seven Habits of Highly Effective People Restoring the Character Ethic (Stephen R. Covey) (Z-Library).pdf",
    # Power of Habit — zachowujemy wersję Duhigg
    "Charles-Duhigg.The-Power-of-Habit.pdf",
    # Rich Habits — zachowujemy wersję PDF Room
    "dokumen.pub_rich-habits-the-daily-success-habits-of-wealthy-individuals-978-1-62652-746-1.pdf",
    # Clear Thinking — zachowujemy krótszą nazwę
    "dokumen.pub_clear-thinking-turning-ordinary-moments-into-extraordinary-results-9780593086117-9780593086124-9780593716212.pdf",
]

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Jesteś ekspertem od książek z dziedziny rozwoju osobistego. \
Użytkownik poda Ci temat po polsku. Na podstawie dostarczonych fragmentów książek:

1. Znajdź najbardziej trafny i inspirujący cytat — podaj go DOSŁOWNIE po angielsku, tak jak pojawia się w tekście.
2. Wyjaśnij krótko po polsku (2-3 zdania), dlaczego ten cytat jest istotny w kontekście podanego tematu.
3. Podaj tytuł książki i numer strony.

Format odpowiedzi (ZAWSZE używaj tego formatu):

📖 Książka: [Tytuł książki]
📄 Strona: [numer strony]

💬 Cytat:
"[dokładny cytat po angielsku z tekstu]"

📝 Kontekst:
[krótkie wyjaśnienie po polsku, 2-3 zdania]

WAŻNE ZASADY:
- Cytat MUSI być dosłowny — nie parafrazuj, nie tłumacz.
- Jeśli w podanych fragmentach nie ma trafnego cytatu, powiedz o tym szczerze.
- Odpowiadaj WYŁĄCZNIE na podstawie dostarczonych fragmentów, nie wymyślaj cytatów.
- Cała konwersacja (poza cytatem) powinna być po polsku.
"""
