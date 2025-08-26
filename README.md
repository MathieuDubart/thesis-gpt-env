# Thesis-GPT Env — Environnement local (Mac, Ollama)

Cet environnement te permet de travailler ton mémoire appliqué avec un assistant GPT **local** (sans cloud), basé sur :
- **RAG** (Recherche Augmentée par Génération) → indexe tes PDF/notes et pose des questions dessus.
- **Presets de modèles** pour alterner entre 3 modes :
  - **Coach** → itérations rapides (Qwen2.5 14B ou Llama3.1 13B)
  - **Sparring** → structuration/profondeur (Qwen2.5 32B)
  - **Reviewer** → audit final exigeant (Llama3.1 70B, quantisation légère Q2_K)

---

## 🚀 Installation

### 1) Dépendances
- macOS (testé sur Apple Silicon, 48 Go RAM ok)
- Python 3.10+
- [Ollama](https://ollama.com/) (serveur de modèles locaux)

### 2) Préparer l’environnement
```bash
# Cloner ou créer le dossier
cd ~/Documents/thesis-gpt-env

# Créer et activer l’environnement virtuel Python
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

## Prompts

Toutes les commandes passent par make.
⚡ Ajoute q="..." pour poser ta question.

Indexer tes sources
make ingest


→ Parcourt ./data/ (PDF, .md, .txt), crée une base Chroma pour le RAG.

Mode Coach (rapide, cadrage)
make coach q="Propose-moi 3 problématiques possibles sur l’usage de l’IA générative"


Utilise Qwen2.5 14B (ou Llama3.1 13B selon config).

Objectif : clarifier, proposer un plan, découper le travail.

Mode Sparring (rigueur, alternatives)
make sparring q="Voici ma problématique provisoire : … Propose 2 alternatives et critique-la"


Utilise Qwen2.5 32B.

Objectif : stress-test de la problématique, proposer alternatives et hypothèses.

Mode Reviewer (audit final)
make reviewer q="Évalue mon protocole méthodologique : entretiens + analyse comparative"


Utilise Llama3.1 70B (Q2_K).

Objectif : audit type jury (méthodo, biais, éthique, RGPD).

Mode Ask (choisir explicitement un modèle)
make ask model=qwen2.5:32b-instruct q="Comment formuler une hypothèse testable à partir de X ?"


Tu forces le modèle.

Exemple : llama3.1:13b-instruct, qwen2.5:14b-instruct, etc.

## 🛠 Workflow conseillé

Coach → cadrer la problématique, obtenir un plan initial.

Sparring → tester la solidité, obtenir variantes & critiques.

Reviewer → audit final avant rédaction.

💡 Sauvegarde régulièrement tes versions (problématique, plan, hypothèses) dans ./data/*.md, puis refais make ingest → ça donne une mémoire longue durée à ton assistant via RAG.

## 🧠 Mémoire locale courte
- Le script garde les **3 derniers échanges** dans `outputs/memory.json`.
- Cette mémoire est **réinjectée** en tête du prompt (section “MÉMOIRE RÉCENTE”) pour conserver le fil.
- Rien n’est envoyé au cloud.

## 📝 Exports Markdown
- Chaque réponse est sauvegardée dans `outputs/` sous la forme:
  `YYYYMMDD-HHMMSS__{preset_ou_model}.md`
- Contient la question + la réponse complète (utile pour relire/annoter).

## 🔍 Citations obligatoires
- Le prompt exige de **citer** `[Source: chemin p.X]` pour tout point fondé sur le CONTEXTE RAG.
- En l’absence de preuve, marquer **[à vérifier]**.
