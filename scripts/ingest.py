#!/usr/bin/env python3
import os, glob, hashlib
from typing import List, Dict
from rich import print
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF

DB_DIR = "vectordb"
DATA_DIR = "data"

def file_id(path: str) -> str:
    return hashlib.md5(path.encode("utf-8")).hexdigest()

def split_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+max_chars]
        chunks.append(chunk)
        i += max_chars - overlap
    return [c.strip() for c in chunks if c.strip()]

def load_pdf(path: str) -> List[Dict]:
    docs = []
    with fitz.open(path) as doc:
        for page in doc:
            text = page.get_text()
            for idx, c in enumerate(split_text(text)):
                docs.append({
                    "id": f"{file_id(path)}:p{page.number}:c{idx}",
                    "text": c,
                    "meta": {"source": path, "page": page.number+1}
                })
    return docs

def load_text(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return [{
        "id": f"{file_id(path)}:c{idx}",
        "text": c,
        "meta": {"source": path}
    } for idx, c in enumerate(split_text(text))]

def main():
    os.makedirs(DB_DIR, exist_ok=True)
    client = PersistentClient(path=DB_DIR)
    coll = client.get_or_create_collection("thesis_rag")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    files = []
    for ext in ("**/*.pdf","**/*.md","**/*.txt"):
        files += glob.glob(os.path.join(DATA_DIR, ext), recursive=True)

    if not files:
        print("[yellow]Aucun fichier trouvé dans ./data[/yellow]")
        return

    added = 0
    for path in files:
        try:
            docs = load_pdf(path) if path.endswith(".pdf") else load_text(path)
        except Exception as e:
            print(f"[red]Erreur {path}: {e}[/red]")
            continue
        for d in docs:
            if coll.get(ids=[d["id"]])["ids"]:
                continue
            emb = model.encode([d["text"]]).tolist()[0]
            coll.add(ids=[d["id"]], embeddings=[emb], metadatas=[d["meta"]], documents=[d["text"]])
            added += 1
    print(f"[green]Indexation terminée. {added} chunks ajoutés.[/green]")

if __name__ == "__main__":
    main()

