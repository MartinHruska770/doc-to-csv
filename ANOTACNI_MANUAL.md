# Anotační manuál: metafory v textu

Tento manuál platí **shodně pro lidského anotátora i pro AI**. Cílem je, aby dva
nezávislí anotátoři došli u stejného odstavce ke stejnému výsledku – jen tak lze
poměřit přesnost modelu (viz [agreement.py](agreement.py)).

## 1. Cíl

U **každého odstavce** rozhodni:

1. **Obsahuje metaforu?** → `ano` / `ne`
2. Pokud ano, **vypiš konkrétní metaforické výrazy** z odstavce.

Jednotkou je odstavec (jeden řádek vstupního CSV se sloupci `id,text`). Posuzuje
se text odstavce sám o sobě, bez širšího kontextu dokumentu.

## 2. Co je metafora

Vycházíme z pojetí **konceptuální metafory** (Lakoff & Johnson, *Metafory,
kterými žijeme*). Metafora = **chápání a popis jedné věci (cílová doména) pomocí
jiné (zdrojová doména)**. Nejde o ozdobu řeči, ale o běžný způsob myšlení.

> Příklad: *„Tváří v tvář **velké překážce** musel **změnit směr**."*
> Cílová doména = životní situace; zdrojová doména = pohyb v prostoru / cesta.

### Tři typy (slouží k rozpoznání, do výstupu se nepíšou)

| Typ | Princip | Příklad |
|-----|---------|---------|
| **Strukturní** | Jeden pojem strukturován pomocí jiného | „**Obhájil** svůj názor." (SPOR = VÁLKA) |
| **Orientační** | Pojmy uspořádané v prostoru | „Měl **povznesenou** náladu." (RADOST = NAHOŘE) |
| **Ontologická** | Abstraktní jev jako věc / látka / osoba | „Tu myšlenku **nemůžu uchopit**." / „Čas **utíká**." |

Typy znát nemusíš kvůli výstupu (ten je binární), ale pomáhají metaforu odhalit:
když výraz odpovídá některému vzorci výše, jde nejspíš o metaforu.

## 3. Postup krok za krokem

Pro každý výraz v odstavci:

1. **Má slovo/sousloví základní, konkrétnější význam** než ten v odstavci?
   (např. „uchopit" = fyzicky vzít rukou)
2. **Liší se význam v textu od toho základního?** (zde „uchopit" = pochopit)
3. **Dá se význam v textu pochopit přes srovnání se základním?**
   Pokud ano na všechny tři → **metaforický výraz**, odstavec je `ano`.

## 4. Hraniční případy (závazná pravidla)

Aby byla shoda měřitelná, řiď se těmito pravidly – ne intuicí:

- **Konvenční / „zaběhnuté" metafory: ANO.** „Čas utíká", „padly argumenty",
  „teplý vztah" jsou pořád metafory, i když je nevnímáme jako neobvyklé.
- **Lexikalizované termíny (mrtvé metafory): ANO, ale jen pokud je srovnání
  stále čitelné.** „Noha stolu", „myš u počítače" → `ano`. Naopak čistě
  technický termín bez živého obrazu (např. „jádro procesoru") nezapočítávej,
  pokud bys ho bez znalosti původu nerozpoznal jako přenos.
- **Přirovnání („jako…", „jako by…"): NE.** Je to explicitní srovnání, ne
  metafora. („Byl silný **jako** medvěd." → `ne`.)
- **Personifikace: ANO** (spadá pod ontologické metafory). „Vítr **si pohrával**
  s listím."
- **Idiomy s živým obrazem: ANO** a vypiš celý idiom. („**Hodil flintu do
  žita**.")
- **Vlastní jména, doslovné popisy, čísla, fakta: NE.**

Při pochybnosti (krok 3 je nejasný) raději **`ne`** – snižuje to falešně
pozitivní nálezy a drží shodu konzistentní.

## 5. Výstupní formát

Anotace = vstupní CSV rozšířené o dva sloupce. Zachovej sloupec `id`, ať jdou
odpovědi spárovat napříč anotátory.

```
id,text,metafora,vyrazy
vzorek-1,"Čas jsou peníze. Utíká nám.",ano,"čas jsou peníze; utíká"
vzorek-2,"Schůze začne v 9:00.",ne,
vzorek-3,"Pohřbil ten nápad.",ano,pohřbil nápad
```

- `metafora`: pouze `ano` nebo `ne` (malými písmeny).
- `vyrazy`: metaforické výrazy oddělené **středníkem**; u `ne` nech prázdné.
  Vypisuj výraz tak, jak je v textu (klidně víceslovný).

Šablonu k vyplnění a kontrolu shody dělá [agreement.py](agreement.py).

## 6. Pokyny navíc pro AI anotátor

- Vrať **přesně** sloupce `id,metafora,vyrazy`, jeden řádek na vstupní `id`,
  nic nepřidávej ani nevynechávej.
- Žádný komentář, vysvětlení ani text mimo CSV.
- Drž se pravidel z odd. 4 doslova; při pochybnosti `ne`.
- Neměň znění odstavce ani `id`.

## 7. Ověření shody

Smysl víc anotátorů: když se model a člověk neshodnou, víc lidských anotátorů
ukáže, **jestli je problém v modelu, nebo v zadání**. Když se neshodnou i lidé
mezi sebou, je nejednoznačné samo pravidlo a je třeba upřesnit tento manuál.

Postup je v [README.md](README.md#vyhodnocení-shody-anotátorů).
