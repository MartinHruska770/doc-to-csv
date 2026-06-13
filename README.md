# Convertor

Webová aplikace, která z Wordu, PDF nebo TXT vytáhne text, rozdělí ho **po
odstavcích** a vrátí ke stažení jako CSV. Slouží jako příprava dat pro
**anotaci metafor** – každý odstavec je jednotka, kterou anotuje člověk i AI.

## Co umí

- Vstup: `.docx`, `.pdf`, `.txt`
- Výstup: `.csv` v UTF-8 s BOM (Excel zobrazí diakritiku správně), sloupce
  `id,text` – jeden odstavec na řádek
- Jednoznačné `id` s prefixem podle názvu souboru (`zprava-1`, `zprava-2`…),
  takže ID zůstanou unikátní i po sloučení víc dokumentů
- U PDF spojuje slova rozdělená pomlčkou na konci řádku
- Limit uploadu 25 MB

Příklad výstupu:

```
id,text
zprava-1,"Čas jsou peníze. Utíká nám."
zprava-2,"Schůze začne v 9:00."
```

> Dělení na věty (s ohledem na české zkratky `Mgr.`, `např.`, `Ph.D.`,
> číslovky a roky) zůstává k dispozici v [converters.py](converters.py)
> jako `split_sentences` / `sentences_to_csv`.

## Instalace

```bash
pip install -r requirements.txt
```

## Spuštění

```bash
python app.py
```

Aplikace běží na `http://127.0.0.1:5000`.

V produkci pust přes WSGI server (např. gunicorn) a nastav `SECRET_KEY`:

```bash
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') \
    gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

## Anotace metafor

Stažené CSV (`id,text`) je vstup pro anotaci. Pravidla – co je metafora, jak ji
poznat, formát výstupu – jsou v [ANOTACNI_MANUAL.md](ANOTACNI_MANUAL.md) a platí
**shodně pro člověka i AI**. Anotace = totéž CSV doplněné o sloupce
`metafora` (`ano`/`ne`) a `vyrazy`.

## AI anotace

Skript [annotate.py](annotate.py) pošle celý korpus do Anthropic Batch API a
vrátí vyplněné CSV. Používá tři vrstvy úspor:

| Vrstva | Úspora |
|---|---|
| Claude Haiku 4.5 | nejlevnější schopný model |
| Batch API | 50 % sleva oproti standardní ceně |
| Prompt caching | ~90 % sleva na systémový prompt (pravidla manuálu) |

Orientační cena: **~0,25 USD / 1 000 odstavců**.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pip install anthropic

python3 annotate.py dataset.csv ai.csv
```

Batch bývá hotový do hodiny; Batch ID se vypíše na stdout pro případ výpadku.

## Vyhodnocení shody anotátorů

Skript [agreement.py](agreement.py) připraví anotační šablony a spočítá shodu
(procentuální, Cohenova a Fleissova kappa s interpretací podle Landise & Kocha).

```bash
# 1) z datasetu vyrob prázdné anotační soubory
python3 agreement.py template dataset.csv anna petr ai

# 2) po vyplnění spočítej shodu (model vs. lidé zvlášť)
python3 agreement.py score anna.csv petr.csv --ai ai.csv
```

Víc lidských anotátorů odliší **chybu modelu** (lidé se shodnou, AI ne) od
**chyby zadání** (neshodnou se i lidé → upřesni manuál).

## Testy

```bash
pytest
```

## Struktura

```
app.py                     # Flask routy
converters.py              # extrakce textu, odstavce/věty, CSV
annotate.py                # AI anotace přes Batch API (Haiku + caching)
agreement.py               # šablony a výpočet shody anotátorů
ANOTACNI_MANUAL.md         # pravidla anotace metafor (člověk i AI)
templates/index.html       # nahrávací stránka
static/                    # styl a drag & drop
tests/                     # jednotkové testy
```

## Omezení

- Skenovaná PDF bez textové vrstvy nezvládne (chybí OCR).
- Starý formát `.doc` není podporován, jen `.docx`.
- Dělení vět je heuristické – u neobvyklých zkratek nebo zkratek na konci
  věty může seknout vedle.

## Licence

MIT
