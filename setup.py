"""
setup.py — Konfiguracja środowiska Book Quote Finder

Skrypt sprawdza i instaluje wszystkie zależności:
1. Pakiety Python (pip install)
2. Ollama (jeśli brak)
3. Modele Ollama (gemma3:4b + nomic-embed-text)

Użycie:
    python setup.py

Można uruchomić wielokrotnie — pomija już zainstalowane komponenty.
"""

import subprocess
import sys
import shutil
import os


# ── Kolory w konsoli ──────────────────────────────────────────────────────────
class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_step(icon, msg):
    print(f"\n{C.CYAN}{C.BOLD}{icon} {msg}{C.END}")


def print_ok(msg):
    print(f"  {C.GREEN}✔ {msg}{C.END}")


def print_warn(msg):
    print(f"  {C.YELLOW}⚠ {msg}{C.END}")


def print_err(msg):
    print(f"  {C.RED}✖ {msg}{C.END}")


# ── 1. Pakiety Python ────────────────────────────────────────────────────────
def install_python_packages():
    print_step("📦", "Sprawdzam pakiety Python...")

    packages = [
        "pymupdf",
        "chromadb",
        "langchain",
        "langchain-community",
        "langchain-ollama",
        "langchain-chroma",
    ]

    missing = []
    for pkg in packages:
        import_name = pkg.replace("-", "_")
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if not missing:
        print_ok("Wszystkie pakiety Python są zainstalowane.")
        return True

    print_warn(f"Brakujące pakiety: {', '.join(missing)}")
    print(f"  Instaluję...")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print_ok("Pakiety zainstalowane pomyślnie.")
        return True
    else:
        print_err(f"Błąd instalacji: {result.stderr}")
        return False


# ── 2. Ollama ─────────────────────────────────────────────────────────────────
def find_ollama() -> str | None:
    """Szuka ollama w PATH i typowych lokalizacjach."""
    # Sprawdź PATH
    ollama_path = shutil.which("ollama")
    if ollama_path:
        return ollama_path

    # Typowe lokalizacje na Windows
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs", "Ollama", "ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p

    return None


def check_ollama():
    print_step("🤖", "Sprawdzam Ollama...")

    ollama_path = find_ollama()

    if ollama_path:
        print_ok(f"Ollama znaleziona: {ollama_path}")
        return ollama_path

    print_err("Ollama nie jest zainstalowana!")
    print()
    print(f"  {C.BOLD}Zainstaluj Ollama ręcznie:{C.END}")
    print()
    print(f"  {C.CYAN}Opcja 1 — Installer (rekomendowane):{C.END}")
    print(f"    Pobierz z: {C.BOLD}https://ollama.com/download{C.END}")
    print(f"    Uruchom OllamaSetup.exe i postępuj wg instrukcji.")
    print()
    print(f"  {C.CYAN}Opcja 2 — Winget:{C.END}")
    print(f"    {C.BOLD}winget install Ollama.Ollama{C.END}")
    print()
    print(f"  Po instalacji uruchom ten skrypt ponownie: {C.BOLD}python setup.py{C.END}")
    return None


# ── 3. Modele Ollama ──────────────────────────────────────────────────────────
def get_installed_models(ollama_path: str) -> list[str]:
    """Zwraca listę zainstalowanych modeli."""
    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        models = []
        for line in result.stdout.strip().split("\n")[1:]:  # pomijamy nagłówek
            if line.strip():
                model_name = line.split()[0]
                models.append(model_name)
        return models
    except Exception:
        return []


def pull_model(ollama_path: str, model_name: str) -> bool:
    """Pobiera model z paskiem postępu (output z ollama pull)."""
    print(f"\n  Pobieram model: {C.BOLD}{model_name}{C.END}")
    print(f"  (to może potrwać kilka minut w zależności od łącza)\n")

    process = subprocess.Popen(
        [ollama_path, "pull", model_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            # Ollama wyświetla pasek postępu sam z siebie
            print(f"  {line}")

    process.wait()
    return process.returncode == 0


def setup_models(ollama_path: str):
    print_step("📥", "Sprawdzam modele Ollama...")

    required_models = {
        "nomic-embed-text": "Model embeddingów (~274 MB)",
        "gemma3:4b": "Model LLM do generowania odpowiedzi (~3.3 GB)",
    }

    installed = get_installed_models(ollama_path)
    installed_base = [m.split(":")[0] if ":" not in m else m for m in installed]

    all_ok = True
    for model, description in required_models.items():
        # Sprawdź czy model jest zainstalowany (z lub bez tagu)
        model_base = model.split(":")[0]
        if any(model in m or model_base in m for m in installed):
            print_ok(f"{model} — zainstalowany ({description})")
        else:
            print_warn(f"{model} — brak ({description})")
            success = pull_model(ollama_path, model)
            if success:
                print_ok(f"{model} — pobrano pomyślnie!")
            else:
                print_err(f"Nie udało się pobrać {model}")
                print(f"  Spróbuj ręcznie: {C.BOLD}ollama pull {model}{C.END}")
                all_ok = False

    return all_ok


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print()
    print(f"{C.BOLD}{'=' * 60}{C.END}")
    print(f"{C.BOLD}  📚 Book Quote Finder — Setup{C.END}")
    print(f"{C.BOLD}{'=' * 60}{C.END}")

    # Krok 1: Python packages
    if not install_python_packages():
        print_err("Nie udało się zainstalować pakietów Python. Przerwano.")
        sys.exit(1)

    # Krok 2: Ollama
    ollama_path = check_ollama()
    if not ollama_path:
        sys.exit(1)

    # Krok 3: Modele
    if not setup_models(ollama_path):
        print_warn("Niektóre modele nie zostały pobrane. Sprawdź powyżej.")
        sys.exit(1)

    # Gotowe!
    print()
    print(f"{C.GREEN}{C.BOLD}{'=' * 60}{C.END}")
    print(f"{C.GREEN}{C.BOLD}  ✅ Setup zakończony pomyślnie!{C.END}")
    print(f"{C.GREEN}{C.BOLD}{'=' * 60}{C.END}")
    print()
    print(f"  Następne kroki:")
    print(f"  {C.BOLD}1.{C.END} Zaindeksuj książki:  {C.CYAN}python ingest.py{C.END}")
    print(f"  {C.BOLD}2.{C.END} Szukaj cytatów:      {C.CYAN}python quote_finder.py{C.END}")
    print()


if __name__ == "__main__":
    main()
