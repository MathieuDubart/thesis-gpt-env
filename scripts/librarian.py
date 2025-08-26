import argparse, json, textwrap, re, datetime

ENGINES = ["OpenAlex", "Crossref", "Google Scholar", "HAL", "arXiv"]

def mk_queries(topic):
    # Déplie un sujet en 3 angles + mots-clés + booléens
    topic_clean = topic.strip()

    angles = [
        ("Théorique", [topic_clean, "framework", "theory", "model", "conceptual"]),
        ("Méthodologique", [topic_clean, "methodology", "protocol", "measurement", "evaluation"]),
        ("Applicatif/Industriel", [topic_clean, "case study", "best practices", "benchmark", "production"]),
    ]
    out=[]
    for label, kws in angles:
        base = " ".join(kws)
        bool_v1 = f'("{topic_clean}") AND (framework OR theory OR model)'
        bool_v2 = f'("{topic_clean}") AND (method* OR protocol OR evaluation)'
        bool_v3 = f'("{topic_clean}") AND ("case study" OR benchmark OR "best practice*")'
        out.append({
            "angle": label,
            "keywords": kws,
            "boolean_queries": [bool_v1, bool_v2, bool_v3]
        })
    return out

def how_to_search(engine, boolean_query):
    if engine=="OpenAlex":
        return f"https://openalex.org/works?search={boolean_query}"
    if engine=="Crossref":
        return f"https://api.crossref.org/works?query={boolean_query}"
    if engine=="Google Scholar":
        return f"https://scholar.google.com/scholar?q={boolean_query}"
    if engine=="HAL":
        return f"https://hal.science/search/index/?q={boolean_query}"
    if engine=="arXiv":
        return f"https://arxiv.org/search/?query={boolean_query}&searchtype=all"
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--years", default="2015-2025")  # période cible suggérée
    args = ap.parse_args()

    suggest = mk_queries(args.topic)
    today = datetime.date.today().isoformat()

    # Affichage Markdown
    print(f"# Librarian — pistes de recherche\n\n**Sujet:** {args.topic}\n**Période cible:** {args.years}\n**Date:** {today}\n")

    for block in suggest:
        print(f"## Angle: {block['angle']}")
        print(f"- Mots-clés: {', '.join(block['keywords'])}")
        print(f"- Requêtes booléennes:")
        for b in block["boolean_queries"]:
            print(f"  - `{b}`")
        print(f"- Où chercher:")
        for b in block["boolean_queries"]:
            for eng in ENGINES:
                url = how_to_search(eng, b.replace(" ", "+"))
                print(f"  - {eng}: {url}")
        print("\n**Pourquoi c’est pertinent:**")
        if block["angle"]=="Théorique":
            print("- Cartographier les cadres conceptuels dominants, repérer les controverses, établir un glossaire rigoureux.")
        elif block["angle"]=="Méthodologique":
            print("- Identifier les protocoles éprouvés, les indicateurs/métriques utilisés, et les menaces à la validité.")
        else:
            print("- Trouver des cas comparables, extraire critères de succès/échec et retours d’expérience.")
        print("\n---\n")

if __name__=="__main__":
    main()

