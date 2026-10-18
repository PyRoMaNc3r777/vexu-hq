# VEXU HQ

Site static (GitHub Pages): dashboard, blog, calendar Halloween.

## Adaugă un lot de postări (Regele / Repi / MDS / Terra)

1. Pregătește un fișier JSON (array), ex. `batch.json`:

```json
[
  {
    "titlu": "🎃 Titlu cu emoji",
    "img": "game-example.png",
    "text": "Textul postării în română.",
    "eticheta": "CONFIRMAT",
    "surse": ["https://www.roblox.com/events/..."],
    "date": "2026-10-15",
    "published": "2026-10-15T14:30:00+03:00",
    "events": [
      {
        "name": "Nume eveniment",
        "game": "Joc",
        "start": "2026-10-17T18:00:00+03:00",
        "end": "2026-10-24T17:00:00+03:00"
      }
    ]
  }
]
```

Câmpuri:
- **titlu**, **text**, **img**, **eticheta** (`CONFIRMAT` | `ZVON` | `TREND SHORTS` | `VEXU LIVE` sau listă mixtă), **surse** — obligatorii
- **published** — ISO cu offset RO (`+03:00` până pe 25 oct 2026, apoi `+02:00`). Dacă lipsește, `build_posts.py` pune ora curentă Bucharest
- **date** — `YYYY-MM-DD` (ziua din feed); dacă lipsește, se ia din `published`
- **featured** — opțional, un singur post
- **section**: `"shorts"` pentru TREND SHORTS
- **events** — opțional, pentru Calendar Halloween (`start`/`end` ISO, sau `start_date`/`end_date`, `date_only`, `no_end`, `end_time_unknown`, `end_only`, `zvon_note`, `coming_soon` pentru dată neanunțată, `announced` + `start` pentru anunțuri oficiale)
- **old_slugs** — redirect de la slug-uri vechi
- **confirmat** / **zvon** — blocuri separate pe pagina postării

2. Descarcă imaginile în rădăcina repo-ului (numele din `img`).
3. Rulează:

```bash
python3 build_posts.py --append batch.json
# sau editează posts.json manual, apoi:
python3 build_posts.py
```

4. Commit + push pe `main` (fără force-push). Pages publică automat.

## Filtre și căutare blog

Chip-urile de filtrare se generează din etichetele reale din `posts-index.json` (`Toate` + fiecare `eticheta` folosită), cu numărul de postări.
Căutarea („Caută în știri…”) filtrează pe loc după titlu și text, fără diacritice; textul complet vine din `posts-search.json` (generat de `build_posts.py`, încărcat doar la prima căutare).

Hash linkabile: `blog.html#f=confirmat`, `#f=zvon`, `#f=trend-shorts`, `#f=vexu-live`, plus căutare: `#q=halloween` sau combinat `#f=zvon&q=forsaken`.

## Istoric jucători (dashboard)

`fetch_data.py` (rulat de `.github/workflows/refresh-data.yml` la ~10 min) adaugă în `history.json` câte un punct real per rulare, doar când API-ul Roblox a răspuns: `{"t":"<ISO UTC>","p":<jucători>,"v":<vizite>}`. Punctele mai vechi de 48h se șterg automat; fișierul e JSON compact. Dashboard-ul desenează ultimele 24h (SVG inline, ora României); cu mai puțin de 3 puncte afișează „Se adună date…”. Fiecare măsurătoare reală e marcată cu punct; golurile de peste 5h nu se unesc cu linie. Notă: GitHub rulează cron-ul de 10 min cu întârzieri mari (de obicei la 2–4h), deci istoricul poate fi rar.
