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
- **events** — opțional, pentru Calendar Halloween (`start`/`end` ISO, sau `start_date`/`end_date`, `date_only`, `no_end`, `end_time_unknown`, `end_only`, `zvon_note`)
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

## Filtre blog

Hash linkabile: `blog.html#f=confirmat`, `#f=zvon`, `#f=trend-shorts`, `#f=vexu-live`.
