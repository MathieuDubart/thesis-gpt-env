#!/usr/bin/env python3
import os, argparse, sys, json, time
from datetime import datetime
from rich import print

# === Chroma (RAG) ===
from chromadb import PersistentClient
from chromadb.config import Settings

# === YAML cfg ===
import yaml

# === Constantes ===
DB_PATH = "vectordb"
OUTPUT_DIR = "outputs"
MEMORY_PATH = os.path.join(OUTPUT_DIR, "memory.json")
MEMORY_KEEP = 3  # nombre d'échanges à garder

def ensure_dirs():
    os.makedirs(DB_PATH, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_chroma():
    client = PersistentClient(
        path=DB_PATH,
        settings=Settings(
            anonymized_telemetry=False,  # coupe la télémétrie
            allow_reset=True
        )
    )
    coll = client.get_or_create_collection("thesis_rag")
    return coll

def retrieve(query: str, top_k: int = 8):
    coll = make_chroma()
    # on requête en texte (suppose que les embeddings ont été ajoutés à l’ingestion)
    res = coll.query(query_texts=[query], n_results=top_k, include=["documents","metadatas"])
    items = []
    if not res["ids"]:
        return items
    for i in range(len(res["ids"][0])):
        items.append({
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
        })
    return items

def format_context(items):
    blocks = []
    for it in items:
        src = it["meta"].get("source","?")
        page = it["meta"].get("page",None)
        loc = f"{src}" + (f" p.{page}" if page else "")
        blocks.append(f"[Source: {loc}]\n{it['text']}")
    return "\n\n---\n\n".join(blocks)

# ===== Mémoire locale courte =====
def load_memory():
    if not os.path.exists(MEMORY_PATH):
        return []
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-MEMORY_KEEP:]
        return []
    except Exception:
        return []

def save_memory_entry(preset_or_model: str, question: str, answer: str):
    mem = load_memory()
    mem.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "preset_or_model": preset_or_model,
        "question": question,
        "answer": answer[:8000]  # évite un fichier énorme
    })
    # ne garder que les N derniers
    mem = mem[-MEMORY_KEEP:]
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def format_memory_for_prompt():
    mem = load_memory()
    if not mem:
        return ""
    lines = ["# MÉMOIRE RÉCENTE (3 derniers échanges)\n"]
    for i, m in enumerate(mem, 1):
        lines.append(f"## Échange {i} — {m['ts']} ({m['preset_or_model']})")
        lines.append(f"Question précédente:\n{m['question']}\n")
        lines.append(f"Réponse modèle (extrait):\n{m['answer']}\n")
        lines.append("---")
    return "\n".join(lines)

# ===== Export Markdown =====
def export_markdown(preset_or_model: str, question: str, answer: str):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = preset_or_model.replace(":", "_").replace("/", "_")
    fname = f"{ts}__{safe}.md"
    path = os.path.join(OUTPUT_DIR, fname)
    md = []
    md.append(f"# Sortie — {preset_or_model}")
    md.append(f"_Horodatage_: {datetime.now().isoformat(timespec='seconds')}")
    md.append("")
    md.append("## Question")
    md.append(question)
    md.append("")
    md.append("## Réponse")
    md.append(answer)
    md.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return path

def main():
    ensure_dirs()

    ap = argparse.ArgumentParser()
    ap.add_argument("--question","-q",required=True, help="Ta question de recherche")
    ap.add_argument("--preset",choices=["coach","sparring","reviewer","assignment"], help="Choisir un preset défini dans config/models.yaml")
    ap.add_argument("--model", help="Forcer un modèle Ollama (ex: qwen2.5:32b-instruct)")
    args = ap.parse_args()

    cfg = load_yaml(os.path.join("config","models.yaml"))
    options = dict(cfg.get("defaults", {}))

    if args.preset:
        preset_cfg = cfg["presets"][args.preset]
        model = preset_cfg["model"]
        options.update(preset_cfg.get("options", {}))
        mode_prompt_path = {
            "coach": "prompts/presets/coach.md",
            "sparring": "prompts/presets/sparring.md",
            "reviewer": "prompts/presets/reviewer.md",
            "assignment": "prompts/presets/assignment.md",
        }[args.preset]
        with open(mode_prompt_path, "r", encoding="utf-8") as f:
            mode_prompt = f.read()
        preset_or_model = f"preset:{args.preset} ({model})"
    else:
        model = args.model or cfg["presets"]["coach"]["model"]
        preset_or_model = f"model:{model}"
        mode_prompt = ""

    with open("prompts/system_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # RAG
    items = retrieve(args.question, top_k=8)
    if not items:
        print("[red]Aucun contenu indexé. Lance d'abord: make ingest[/red]")
        sys.exit(1)
    context = format_context(items)

    # Mémoire récente (2–3 derniers échanges)
    memory_block = format_memory_for_prompt()

    # --- Garde-fous de citation (Point 3) ---
    # On renforce l'instruction: toute affirmation appuyée sur le contexte doit inclure [Source: ...].
    citation_guard = """
# RÈGLE CITOYENNE (OBLIGATOIRE)
- Pour chaque fait, chiffre, extrait ou concept repris du CONTEXTE, **ajoute immédiatement** une mention `[Source: chemin p.X]`.
- Si tu avances un point **sans support** explicite dans le CONTEXTE, ajoute le tag **[à vérifier]**.
- N'invente aucune référence; ne cite rien en dehors du CONTEXTE fourni (ou des refs explicitement données par l'utilisateur).
"""

    user_prompt = f"""{mode_prompt}

{citation_guard}

# CONTEXTE À UTILISER
{context}

{memory_block}

# TÂCHE
En respectant strictement les contraintes ci-dessus:
- Commence par 2–4 questions **socratiques**.
- Propose 2–3 problématiques **courtes**.
- Donne un **plan en bullets** (2–3 niveaux) avec objectifs/méthodes/livrables.
- Décris un **dispositif appliqué** (données, instruments, métriques/critères, analyse, limites/biais, RGPD).
- Ajoute une **checklist** de validation.
- Termine par un **assignment** (tâche concrète + critères d'acceptation).

# QUESTION UTILISATEUR
{args.question}
"""

    # Appel modèle
    answer_chunks = []
    try:
        import ollama
        resp = ollama.chat(
            model=model,
            options=options,
            messages=[
                {"role":"system","content": system_prompt},
                {"role":"user","content": user_prompt}
            ],
            stream=True
        )
        for chunk in resp:
            if "message" in chunk and "content" in chunk["message"]:
                text = chunk["message"]["content"]
                answer_chunks.append(text)
                sys.stdout.write(text)
                sys.stdout.flush()
        print()
    except Exception as e:
        print(f"[yellow]Ollama non disponible ou erreur: {e}[/yellow]")
        print("\n[bold]Contexte (top matches):[/bold]\n")
        print(context)
        print("\n[bold]Suggestion:[/bold] Copie le contexte + la TÂCHE ci-dessus dans ton GPT favori.")
        sys.exit(1)

    answer = "".join(answer_chunks)

    # Petit garde-fou post-traitement: si aucune citation détectée, on ajoute un rappel.
    if "[Source:" not in answer:
        answer += "\n\n⚠️ Aucune citation détectée — ajoute `[Source: …]` aux points sourcés et `[à vérifier]` où il manque une preuve."

    # Export Markdown (Point 8)
    md_path = export_markdown(preset_or_model, args.question, answer)
    print(f"\n[green]📝 Export Markdown:[/green] {md_path}")

    # Mémoire locale courte (Point 4)
    save_memory_entry(preset_or_model, args.question, answer)

if __name__ == "__main__":
    main()
