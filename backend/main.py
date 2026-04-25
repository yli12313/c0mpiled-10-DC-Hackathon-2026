import os
import json
import psycopg2
import psycopg2.extras
from groq import Groq
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SCHEMA = """
You have access to a PostgreSQL database called 'c0mpiled' with the following tables:

TABLE: stars (4,701 rows — host star systems)
  hostname     TEXT PRIMARY KEY
  ra           DOUBLE PRECISION  -- right ascension (degrees)
  dec          DOUBLE PRECISION  -- declination (degrees)
  st_teff      DOUBLE PRECISION  -- effective temperature (Kelvin)
  st_rad       DOUBLE PRECISION  -- radius (solar radii)
  st_mass      DOUBLE PRECISION  -- mass (solar masses)
  st_spectype  TEXT              -- spectral type (e.g. G2V, K5V, M3)
  sy_dist      DOUBLE PRECISION  -- distance from Earth (parsecs)
  sy_snum      INTEGER           -- number of stars in system
  sy_pnum      INTEGER           -- number of known planets in system

TABLE: planets (6,273 rows — confirmed exoplanets)
  pl_name         TEXT PRIMARY KEY
  hostname        TEXT            -- FK → stars.hostname
  disc_year       INTEGER         -- year discovered
  discoverymethod TEXT            -- Transit, Radial Velocity, Microlensing, Imaging, etc.
  disc_facility   TEXT            -- e.g. Kepler, TESS, W. M. Keck Observatory
  disc_telescope  TEXT
  pl_orbper       DOUBLE PRECISION  -- orbital period (days)
  pl_orbsmax      DOUBLE PRECISION  -- semi-major axis (AU)
  pl_orbeccen     DOUBLE PRECISION  -- eccentricity (0=circular, 1=parabolic)
  pl_rade         DOUBLE PRECISION  -- radius (Earth radii); ~11 = Jupiter-sized
  pl_bmasse       DOUBLE PRECISION  -- mass (Earth masses); ~318 = Jupiter mass
  pl_eqt          DOUBLE PRECISION  -- equilibrium temperature (Kelvin)
  pl_insol        DOUBLE PRECISION  -- insolation flux (Earth = 1.0); 0.27–1.77 = habitable zone

TABLE: missions (14 rows — major planet-hunting missions)
  mission_name     TEXT PRIMARY KEY
  agency           TEXT   -- NASA, ESA, etc.
  launch_date      DATE
  end_date         DATE   -- NULL if still active
  status           TEXT   -- active / retired / extended
  mission_type     TEXT   -- space / ground
  detection_method TEXT
  disc_facility    TEXT   -- matches planets.disc_facility for joins
  description      TEXT

TABLE: planet_candidates (7,927 rows — unconfirmed TESS Objects of Interest)
  toi          DOUBLE PRECISION PRIMARY KEY  -- TOI number
  toidisplay   TEXT    -- display name e.g. TOI-1234.01
  disposition  TEXT    -- PC=planet candidate, CP=confirmed, FP=false positive, FA=false alarm
  ra           DOUBLE PRECISION
  dec          DOUBLE PRECISION
  st_tmag      DOUBLE PRECISION  -- host star TESS magnitude (brightness)
  pl_orbper    DOUBLE PRECISION  -- orbital period (days)
  pl_rade      DOUBLE PRECISION  -- planet radius (Earth radii)
  pl_eqt       DOUBLE PRECISION  -- equilibrium temperature (Kelvin)
  st_teff      DOUBLE PRECISION  -- host star temperature (Kelvin)
  st_logg      DOUBLE PRECISION  -- host star surface gravity
  st_rad       DOUBLE PRECISION  -- host star radius (solar radii)

TABLE: neo_close_approaches (1,473 rows — asteroid close approach events 2024–2025)
  id                      SERIAL PRIMARY KEY
  neo_id                  TEXT
  name                    TEXT    -- asteroid name
  is_potentially_hazardous BOOLEAN
  diameter_min_km         DOUBLE PRECISION
  diameter_max_km         DOUBLE PRECISION
  close_approach_date     DATE
  relative_velocity_kph   DOUBLE PRECISION
  miss_distance_km        DOUBLE PRECISION
  miss_distance_lunar     DOUBLE PRECISION  -- 1.0 = distance to Moon
  orbiting_body           TEXT              -- usually 'Earth'
"""

SQL_SYSTEM = f"""{SCHEMA}

Convert the user's question into a single valid PostgreSQL SELECT query.
Output ONLY the raw SQL — no markdown, no backticks, no explanation.
Rules:
- LIMIT to 50 rows unless explicitly asked for more
- Use IS NOT NULL when filtering numeric columns
- Use ILIKE for case-insensitive text matching
- To find habitable zone planets: pl_insol BETWEEN 0.27 AND 1.77
- For joins between planets and missions: planets.disc_facility = missions.disc_facility
"""

ANSWER_SYSTEM = """You are a space science communicator for a NASA data demo.
Given the user's question, the SQL that was run, and the query results,
write a vivid 2-3 sentence answer in plain English.
Be specific — cite actual names, numbers, and dates from the results.
End with one brief surprising or delightful fact if the data supports it.
Do not mention SQL or databases."""


def get_db():
    return psycopg2.connect(
        host="localhost", port=5432, dbname="c0mpiled",
        user="postgres", password="postgres"
    )


def run_sql(sql: str):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchmany(50)
        columns = [desc[0] for desc in cur.description]
        return [dict(r) for r in rows], columns
    finally:
        conn.close()


MODEL = "llama-3.3-70b-versatile"


def generate_sql(question: str, error: str = None) -> str:
    messages = [{"role": "user", "content": question}]
    if error:
        messages.append({"role": "assistant", "content": "-- previous attempt failed"})
        messages.append({"role": "user", "content": f"That query failed with: {error}\nPlease fix it and return only the corrected SQL."})

    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "system", "content": SQL_SYSTEM}] + messages,
    )
    sql = resp.choices[0].message.content.strip()
    # strip markdown fences if model slips
    if sql.startswith("```"):
        sql = "\n".join(sql.split("\n")[1:])
    if sql.endswith("```"):
        sql = "\n".join(sql.split("\n")[:-1])
    return sql.strip()


def generate_answer(question: str, sql: str, results: list, columns: list) -> str:
    sample = results[:10]
    context = f"Question: {question}\n\nSQL used:\n{sql}\n\nResults ({len(results)} rows returned):\n{json.dumps(sample, default=str, indent=2)}"
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM},
            {"role": "user",   "content": context},
        ],
    )
    return resp.choices[0].message.content.strip()


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
async def query(req: QueryRequest):
    question = req.question.strip()
    if not question:
        return JSONResponse({"error": "Empty question"}, status_code=400)

    sql = generate_sql(question)
    try:
        results, columns = run_sql(sql)
    except Exception as e:
        # one retry with the error message
        try:
            sql = generate_sql(question, error=str(e))
            results, columns = run_sql(sql)
        except Exception as e2:
            return JSONResponse({
                "question": question,
                "sql": sql,
                "error": str(e2),
                "results": [],
                "columns": [],
                "answer": "",
            })

    answer = generate_answer(question, sql, results, columns)

    return {
        "question": question,
        "sql": sql,
        "results": results,
        "columns": columns,
        "answer": answer,
        "error": None,
    }


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../frontend")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "../frontend/index.html"))
