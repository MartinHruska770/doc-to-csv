#!/usr/bin/env python3
"""AI anotace metafor přes Anthropic Batch API.

Strategie minimalizace nákladů:
  • Claude Haiku 4.5  – nejlevnější schopný model ($1 / $5 per 1M tokenů)
  • Batch API         – 50 % sleva  ($0,50 / $2,50 per 1M tokenů)
  • Prompt caching    – systémový prompt cachován, ~90 % sleva na opakované čtení

Orientační cena: ~0,25 USD / 1 000 odstavců.

Použití:
    python3 annotate.py dataset.csv ai.csv

Vstup:  CSV se sloupci id,text  (výstup z převodníku)
Výstup: CSV se sloupci id,metafora,vyrazy  (pro agreement.py --ai ai.csv)

Vyžaduje:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import argparse
import csv
import io
import sys
import time
from pathlib import Path

import anthropic

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 128  # odpověď je jen krátký CSV řádek
BOM = "﻿"

# Kompaktní systémový prompt – bude cachován (ušetří ~90 % nákladů na vstupní tokeny).
# Vychází z ANOTACNI_MANUAL.md, oddíly 2–4 a 6.
_SYSTEM = """\
Jsi lingvistický anotátor konceptuálních metafor (Lakoff & Johnson).

PRAVIDLA:
- Metafora = chápání jedné věci pomocí jiné (cílová / zdrojová doména).
- Konvencionální metafory (čas utíká, padly argumenty, teplý vztah): ANO.
- Přirovnání (jako, jako by, podobně jako): NE – explicitní srovnání není metafora.
- Personifikace (vítr si hrál, čas letí): ANO (ontologická metafora).
- Idiomy s živým obrazem (hodil flintu do žita): ANO, vypiš celý idiom.
- Vlastní jména, čísla, doslovné popisy, technické termíny bez živého obrazu: NE.
- Při pochybnosti: NE.

VÝSTUP: přesně jeden CSV řádek bez záhlaví, bez komentářů:
  id,metafora,vyrazy
kde 'metafora' je 'ano' nebo 'ne' a 'vyrazy' jsou výrazy z textu oddělené středníkem (u 'ne' prázdné).

Příklady správného výstupu:
  zprava-1,ano,"čas jsou peníze; utíká nám"
  zprava-2,ne,
  zprava-3,ano,pohřbil nápad"""


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(BOM)
        writer = csv.writer(f)
        writer.writerow(["id", "metafora", "vyrazy"])
        for row in rows:
            writer.writerow([row["id"], row.get("metafora", ""), row.get("vyrazy", "")])


def _build_requests(rows: list[dict]) -> list[dict]:
    return [
        {
            "custom_id": row["id"],
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": [
                    {
                        "type": "text",
                        "text": _SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": f"id: {row['id']}\ntext: {row['text']}",
                    }
                ],
            },
        }
        for row in rows
    ]


def _parse_line(custom_id: str, text: str) -> dict:
    """Naparsuje CSV řádek vrácený modelem; vrátí 'ne' při chybě parsování.

    Prochází všechny řádky odpovědi a bere první, kde parts[1] je 'ano' nebo 'ne'.
    Ignoruje komentáře, záhlaví a jiné řádky, které model přidá navíc.
    """
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parts = next(csv.reader(io.StringIO(line)))
            if len(parts) < 2:
                continue
            metafora = parts[1].strip().lower()
            if metafora not in ("ano", "ne"):
                continue
            vyrazy = parts[2].strip() if len(parts) > 2 else ""
            return {"id": custom_id, "metafora": metafora, "vyrazy": vyrazy}
        except Exception:
            continue
    return {"id": custom_id, "metafora": "ne", "vyrazy": ""}


def annotate(input_path: str, output_path: str) -> None:
    rows = _read_csv(input_path)
    if not rows:
        sys.exit("Chyba: vstupní CSV je prázdné.")

    client = anthropic.Anthropic()

    print(f"Odesílám batch – {len(rows)} odstavců ({MODEL}) …")
    batch = client.messages.batches.create(requests=_build_requests(rows))
    print(f"Batch ID: {batch.id}  (uložte si pro případ výpadku)")

    # Batche bývají hotové do hodiny; kontrolujeme každých 30 s
    while batch.processing_status == "in_progress":
        time.sleep(30)
        batch = client.messages.batches.retrieve(batch.id)
        c = batch.request_counts
        done = c.succeeded + c.errored + c.canceled + c.expired
        print(f"  {done}/{len(rows)} hotovo, {c.errored} chyb …")

    print("Batch dokončen, stahuji výsledky …")

    results_by_id: dict[str, dict] = {}
    for result in client.messages.batches.results(batch.id):
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            results_by_id[result.custom_id] = _parse_line(result.custom_id, text)
        else:
            print(f"  Chyba u {result.custom_id}: {result.result.type}", file=sys.stderr)
            results_by_id[result.custom_id] = {
                "id": result.custom_id,
                "metafora": "",
                "vyrazy": "",
            }

    # Zachovej pořadí vstupního CSV
    output_rows = [
        results_by_id.get(row["id"], {"id": row["id"], "metafora": "", "vyrazy": ""})
        for row in rows
    ]
    _write_csv(output_path, output_rows)

    ok = sum(1 for r in output_rows if r["metafora"] in ("ano", "ne"))
    ano = sum(1 for r in output_rows if r["metafora"] == "ano")
    pct = f"{ano / ok:.0%}" if ok else "–"
    print(f"\nHotovo: {output_path}")
    print(f"  Anotováno: {ok}/{len(rows)}, z toho metafor: {ano} ({pct})")
    print(f"\nVyhodnocení shody:")
    print(f"  python3 agreement.py score anna.csv petr.csv --ai {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("vstup", help="CSV z převodníku (id,text)")
    parser.add_argument("vystup", help="výstupní CSV (id,metafora,vyrazy)")
    args = parser.parse_args()
    annotate(args.vstup, args.vystup)


if __name__ == "__main__":
    main()
