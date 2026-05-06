import os
import subprocess
from pathlib import Path

def get_calibre_path():
    # Sprawdź czy ebook-convert jest w systemowym PATH
    try:
        subprocess.run(["ebook-convert", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "ebook-convert"
    except FileNotFoundError:
        pass
        
    # Standardowe ścieżki instalacji Calibre na Windowsie
    paths = [
        r"C:\Program Files\Calibre2\ebook-convert.exe",
        r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"
    ]
        
    for p in paths:
        if os.path.exists(p):
            return p
            
    return None

def convert_epub_to_pdf(root_dir):
    """
    Znajduje wszystkie pliki .epub w folderze i jego podfolderach,
    konwertuje je do PDF za pomocą Calibre, a po sukcesie usuwa oryginał.
    """
    calibre_path = get_calibre_path()
    
    if not calibre_path:
        print("==========================================================")
        print(" BŁĄD: Nie znaleziono programu Calibre!")
        print(" Pobierz i zainstaluj Calibre z podanej poniżej strony:")
        print(" https://calibre-ebook.com/download_windows")
        print(" Po instalacji spróbuj uruchomić skrypt ponownie.")
        print("==========================================================")
        return
        
    root_path = Path(root_dir)
    epub_files = list(root_path.rglob("*.epub"))
    
    if not epub_files:
        print(f"Nie znaleziono plików EPUB w {root_dir}")
        return

    print(f"Znaleziono {len(epub_files)} plików EPUB do konwersji.")
    print(f"Używam narzędzia Calibre ze ścieżki: {calibre_path}\n")

    for epub_file in epub_files:
        print(f"Przetwarzam: {epub_file.name} ...")
        
        pdf_file = epub_file.with_suffix('.pdf')
        
        # Wywołanie narzędzia konwersji Calibre
        command = [
            calibre_path,
            str(epub_file),
            str(pdf_file)
        ]
        
        try:
            # Konwersja może chwilę zająć w zależności od wielkości książki
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f" ✔ Utworzono PDF: {pdf_file.name}")
            
            if pdf_file.exists():
                epub_file.unlink()
                print(f" ✔ Usunięto stary plik EPUB.")
            
            print("-" * 40)
                
        except subprocess.CalledProcessError as e:
            print(f" ✖ Błąd podczas konwersji {epub_file.name}")
            print(e.stderr)
            print("-" * 40)

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    convert_epub_to_pdf(current_directory)
    print("\nGotowe!")
