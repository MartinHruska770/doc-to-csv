"""Vyhodnocení shody anotátorů metafor (člověk vs. člověk, člověk vs. AI).

Dva režimy:

  template  – z datasetu (id,text) vyrobí prázdné anotační soubory k vyplnění
  score     – spočítá shodu na sloupci `metafora` mezi anotačními soubory

Příklad:
  python3 agreement.py template dataset.csv anna petr ai
  python3 agreement.py score anna.csv petr.csv --ai ai.csv
"""

import argparse
import csv
import sys
from itertools import combinations
from pathlib import Path

BOM = "﻿"

_YES = {"ano", "yes", "1", "true", "ano."}
_NO = {"ne", "no", "0", "false", "ne."}


def _read_dataset(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _normalize(value):
    """Vrátí 1 pro 'ano', 0 pro 'ne', None pro nerozpoznané/prázdné."""
    key = (value or "").strip().casefold()
    if key in _YES:
        return 1
    if key in _NO:
        return 0
    return None


def _load_labels(path):
    """Načte {id: 0/1} ze sloupce `metafora`; přeskočí nevyplněné řádky."""
    labels = {}
    for row in _read_dataset(path):
        ident = (row.get("id") or "").strip()
        label = _normalize(row.get("metafora"))
        if ident and label is not None:
            labels[ident] = label
    return labels


def make_template(dataset_path, names):
    rows = _read_dataset(dataset_path)
    for name in names:
        out = Path(f"{name}.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            f.write(BOM)
            writer = csv.writer(f)
            writer.writerow(["id", "text", "metafora", "vyrazy"])
            for row in rows:
                writer.writerow([row.get("id", ""), row.get("text", ""), "", ""])
        print(f"vytvořeno: {out}  ({len(rows)} odstavců)")


def _percent_agreement(a, b):
    same = sum(1 for x, y in zip(a, b) if x == y)
    return same / len(a) if a else 0.0


def cohen_kappa(a, b):
    """Cohenova kappa pro dvojici anotátorů (binární značky 0/1)."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = _percent_agreement(a, b)
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe == 1.0:
        return 1.0  # všichni shodně jedna kategorie
    return (po - pe) / (1 - pe)


def fleiss_kappa(columns):
    """Fleissova kappa pro ≥2 anotátory; columns = seznam seznamů značek 0/1."""
    n_ann = len(columns)
    n_items = len(columns[0])
    if n_ann < 2 or n_items == 0:
        return float("nan")
    # počty kladných hlasů na položku
    pos = [sum(col[i] for col in columns) for i in range(n_items)]
    p_yes = sum(pos) / (n_items * n_ann)
    p_no = 1 - p_yes
    pe = p_yes**2 + p_no**2
    # míra shody uvnitř položky
    pi = [
        (pos[i] ** 2 + (n_ann - pos[i]) ** 2 - n_ann) / (n_ann * (n_ann - 1))
        for i in range(n_items)
    ]
    pbar = sum(pi) / n_items
    if pe == 1.0:
        return 1.0
    return (pbar - pe) / (1 - pe)


def _interpret(kappa):
    """Landis & Koch (1977)."""
    if kappa != kappa:  # NaN
        return "nelze určit"
    bands = [
        (0.0, "žádná (poor)"),
        (0.20, "slabá (slight)"),
        (0.40, "průměrná (fair)"),
        (0.60, "střední (moderate)"),
        (0.80, "značná (substantial)"),
        (1.01, "téměř dokonalá (almost perfect)"),
    ]
    for threshold, label in bands:
        if kappa < threshold:
            return label
    return bands[-1][1]


def _aligned(labels_a, labels_b):
    common = sorted(set(labels_a) & set(labels_b))
    return [labels_a[i] for i in common], [labels_b[i] for i in common], common


def score(human_paths, ai_path=None):
    annotators = {Path(p).stem: _load_labels(p) for p in human_paths}
    if ai_path:
        annotators[f"{Path(ai_path).stem} (AI)"] = _load_labels(ai_path)

    if len(annotators) < 2:
        sys.exit("Potřebuju aspoň dva anotační soubory.")

    print(f"Anotátoři: {', '.join(annotators)}\n")

    print("== Párová shoda ==")
    for name_a, name_b in combinations(annotators, 2):
        a, b, common = _aligned(annotators[name_a], annotators[name_b])
        if not common:
            print(f"{name_a} ↔ {name_b}: žádné společné id")
            continue
        k = cohen_kappa(a, b)
        print(
            f"{name_a} ↔ {name_b}: shoda {_percent_agreement(a, b):.0%}, "
            f"κ={k:.2f} ({_interpret(k)}), n={len(common)}"
        )

    # Fleissova kappa přes všechny na společné průniku id
    common = sorted(set.intersection(*(set(v) for v in annotators.values())))
    if len(annotators) >= 3 and common:
        cols = [[labels[i] for i in common] for labels in annotators.values()]
        k = fleiss_kappa(cols)
        print(f"\n== Celková shoda (Fleiss) ==\nκ={k:.2f} ({_interpret(k)}), "
              f"n={len(common)}")

    if ai_path:
        print("\n== Model vs. lidé ==")
        ai_name = f"{Path(ai_path).stem} (AI)"
        ai = annotators[ai_name]
        for name in annotators:
            if name == ai_name:
                continue
            a, b, common = _aligned(ai, annotators[name])
            if not common:
                continue
            k = cohen_kappa(a, b)
            print(f"AI ↔ {name}: shoda {_percent_agreement(a, b):.0%}, "
                  f"κ={k:.2f} ({_interpret(k)})")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("template", help="vyrob prázdné anotační soubory")
    t.add_argument("dataset", help="CSV z převodu (id,text)")
    t.add_argument("names", nargs="+", help="jména anotátorů → názvy souborů")

    s = sub.add_parser("score", help="spočítej shodu")
    s.add_argument("files", nargs="+", help="anotační CSV (lidé)")
    s.add_argument("--ai", help="anotační CSV od modelu (vyhodnotí se zvlášť)")

    args = parser.parse_args(argv)
    if args.cmd == "template":
        make_template(args.dataset, args.names)
    else:
        score(args.files, args.ai)


if __name__ == "__main__":
    main()
