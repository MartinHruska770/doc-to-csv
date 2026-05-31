# Convertor

Webová aplikace, která z Wordu nebo PDF vytáhne text, rozdělí ho na věty
a vrátí ke stažení jako CSV (jedna věta = jeden řádek).

## Co umí

- Vstup: `.docx`, `.pdf`
- Výstup: `.csv` v UTF-8 s BOM (Excel zobrazí diakritiku správně)
- Rozdělení na věty s ohledem na české zkratky (`Mgr.`, `např.`, `Ph.D.`),
  pořadové číslovky (`1. ledna`) a roky (`v roce 2024.`)
- Limit uploadu 25 MB

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

## Testy

```bash
pytest
```

## Struktura

```
app.py                     # Flask routy
converters.py              # extrakce textu, dělení vět, CSV
templates/index.html       # nahrávací stránka
static/                    # styl a drag & drop
tests/test_converters.py   # jednotkové testy
```

## Omezení

- Skenovaná PDF bez textové vrstvy nezvládne (chybí OCR).
- Starý formát `.doc` není podporován, jen `.docx`.
- Dělení vět je heuristické – u neobvyklých zkratek nebo zkratek na konci
  věty může seknout vedle.

## Licence

MIT
