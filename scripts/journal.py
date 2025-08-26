import argparse, os, re, datetime, textwrap, json

SECTIONS = [
    ("Questions de cadrage", r"(?:^|\n)#{0,3}\s*Questions de cadrage.*?(?=\n#|\Z)"),
    ("Options", r"(?:^|\n)#{0,3}\s*Options.*?(?=\n#|\Z)"),
    ("Plan", r"(?:^|\n)#{0,3}\s*Plan.*?(?=\n#|\Z)"),
    ("TODO étudiant", r"(?:^|\n)#{0,3}\s*TODO étudiant.*?(?=\n#|\Z)"),
    ("Check", r"(?:^|\n)#{0,3}\s*Check.*?(?=\n#|\Z)"),
]

def extract_section(name, text):
    pat = dict(SECTIONS)[name]
    m = re.search(pat, text, flags=re.IGNORECASE|re.DOTALL)
    if not m: return ""
    chunk = m.group(0).strip()
    # Compacte un peu
    lines = [l.rstrip() for l in chunk.splitlines()[:40]]
    return "\n".join(lines).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--answer", required=True)
    ap.add_argument("--decisions", default="")  # optionnel: décisions que TU valides après coup
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    os.makedirs(f"outputs/journal", exist_ok=True)
    path = f"outputs/journal/{today}.md"

    # Mini résumé automatique (1–3 lignes)
    short = args.answer.splitlines()
    short = " ".join([l.strip() for l in short if l.strip()][:8])[:600]

    blocks = []
    for name, _ in SECTIONS:
        sec = extract_section(name, args.answer)
        if sec:
            blocks.append(sec)

    now = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"""\
---
time: {now}
---

### Prompt
{args.prompt.strip()}

### Synthèse rapide
{short}

{("\n\n".join(blocks) if blocks else "")}

### Décisions (à valider par toi)
{args.decisions or "- (à compléter)"}

### Next steps (issu du TODO étudiant si présent)
{extract_section("TODO étudiant", args.answer) or "- (à compléter)"}

---

"""

    header_needed = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if header_needed:
            f.write(f"# Journal des décisions — {today}\n\n")
        f.write(entry)

if __name__ == "__main__":
    main()
