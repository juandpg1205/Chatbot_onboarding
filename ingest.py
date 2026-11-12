"""Upload the PDFs in the articles folder to a Gemini File Search store.

Usage: python ingest.py
Creates the store on the first run and saves its name in store.json.
Re-running only uploads PDFs that were not uploaded before.
To re-index from scratch, delete store.json (and the old store in AI Studio).

The PDF folder defaults to ./articles and can be changed with ARTICLES_DIR.
"""
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_DIR = Path(os.environ.get("ARTICLES_DIR", BASE_DIR / "articles"))
if not ARTICLES_DIR.is_absolute():
    ARTICLES_DIR = (BASE_DIR / ARTICLES_DIR).resolve()
STORE_FILE = BASE_DIR / "store.json"


def ascii_name(name):
    """The SDK sends the file name in an HTTP header, which must be ASCII."""
    return name.replace("\u2019", "'").encode("ascii", "ignore").decode().strip()


def main():
    client = genai.Client()  # reads GEMINI_API_KEY from the environment

    if STORE_FILE.exists():
        data = json.loads(STORE_FILE.read_text())
        print(f"Using existing store: {data['name']}")
    else:
        store = client.file_search_stores.create(config={"display_name": "articles-kb"})
        data = {"name": store.name, "uploaded": []}
        STORE_FILE.write_text(json.dumps(data, indent=2))
        print(f"Store created: {store.name}")

    pdfs = sorted(ARTICLES_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {ARTICLES_DIR}. Add some and run again.")
    pending = [p for p in pdfs if p.name not in data["uploaded"]]
    print(f"{len(pdfs)} PDFs found in {ARTICLES_DIR}, {len(pending)} pending.")

    for pdf in pending:
        print(f"Uploading: {pdf.name} ...", end=" ", flush=True)
        for attempt in range(1, 4):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    safe = Path(tmp) / ascii_name(pdf.name)
                    shutil.copy(pdf, safe)
                    op = client.file_search_stores.upload_to_file_search_store(
                        file=str(safe),
                        file_search_store_name=data["name"],
                        config={"display_name": safe.name},
                    )
                break
            except Exception as exc:
                if attempt == 3:
                    raise
                print(f"(retry {attempt}: {type(exc).__name__})", end=" ", flush=True)
                time.sleep(3 * attempt)
        while not op.done:
            time.sleep(5)
            op = client.operations.get(op)
        data["uploaded"].append(pdf.name)
        STORE_FILE.write_text(json.dumps(data, indent=2))
        print("done")

    print("Indexing complete.")


if __name__ == "__main__":
    main()
