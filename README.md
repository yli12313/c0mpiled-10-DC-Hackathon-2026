# NASA Exoplanet Query Interface
### c0mpiled-10/DC Hackathon 2026

* **Prompt:** LLM-powered compliance alternatives / Modern public-facing infrastructure  
* **Agency:** NASA  
* **Problem:** Legacy Microsoft SQL Server systems block downstream AI applications. This project demonstrates what's possible when NASA data lives in modern PostgreSQL — queryable by anyone, in plain English.

<img width="989" height="527" alt="image" src="https://github.com/user-attachments/assets/44b37708-0367-4e29-9e8d-d93997e90b7e" />

---

## What It Does

A natural language query interface over real NASA data. Type a question in plain English, get an AI-generated SQL query, live results, and a plain-English answer — no SQL knowledge required.

---

## Project Structure

```
├── backend/
│   └── main.py              # FastAPI server — text-to-SQL + answer generation
├── db/
│   ├── schema.sql           # PostgreSQL table definitions
│   ├── load.py              # Loads planets + stars from NASA Exoplanet Archive
│   ├── load_extra.py        # Loads missions, TESS candidates, NEO approaches
│   └── make_pitch.py        # Generates NASA_Exoplanet_Pitch.pptx
├── frontend/
│   ├── index.html           # Main UI — space-themed, no build step
│   ├── pitch.html           # In-browser pitch deck (5 slides)
│   ├── nasa-logo.png        # NASA meatball logo (transparent)
│   ├── exoplanet-bg.webm    # NASA Earth-like exoplanet animation
│   └── exoplanet-bg2.webm   # NASA WFIRST exoplanet/star animation
├── NASA_Exoplanet_Pitch.pptx
├── start.sh
└── README.md
```

---

## The Data

| Table | Rows | Source |
|---|---|---|
| `planets` | 6,273 | NASA Exoplanet Archive — confirmed planets |
| `planet_candidates` | 7,927 | TESS Objects of Interest (unconfirmed) |
| `stars` | 4,701 | NASA Exoplanet Archive — host star systems |
| `missions` | 14 | Major planet-hunting missions (Kepler, TESS, JWST…) |
| `neo_close_approaches` | 1,473 | NASA NeoWs API — asteroid events 2024–2025 |

---

## Stack

- **Backend:** FastAPI + Groq (Llama 3.3 70B) — text-to-SQL generation and natural language answers
- **Database:** PostgreSQL (`localhost:5432`, database `c0mpiled`)
- **Frontend:** Vanilla HTML/CSS/JS with animated starfield and NASA video background — no build step
- **Pitch Deck:** `python-pptx` generated `.pptx` + in-browser HTML deck

---

## Setup

**1. Install dependencies**
```bash
pip install fastapi uvicorn groq psycopg2-binary python-pptx Pillow
```

**2. Create the schema**
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d c0mpiled -f db/schema.sql
```

**3. Load the data**
```bash
PGPASSWORD=postgres python3 db/load.py
PGPASSWORD=postgres python3 db/load_extra.py
```

**4. Start the server**
```bash
GROQ_API_KEY=your_key_here bash start.sh
```

This starts a FastAPI server on port 8000 with hot-reload. The server serves both the API (`/query`) and the frontend (`/`) from a single process. Make sure PostgreSQL is running before starting.

**5. Open the app**

| URL | What it is |
|---|---|
| `http://localhost:8000` | Main query interface |
| `http://localhost:8000/static/pitch.html` | In-browser pitch deck |

Type any question in the search bar and press Enter or click **QUERY →**. The app generates SQL, runs it, and returns a natural-language answer with a results table. Click **↓ CSV** to download or **✕** to dismiss.

---

## Example Queries

- *Which mission has discovered the most confirmed planets?*
- *Find Earth-sized planets in the habitable zone*
- *Which asteroids passed closer than the Moon in 2024?*
- *How many TESS candidates are still unconfirmed?*
- *Which star has the most known planets?*
- *What are the fastest asteroids that passed Earth?*
