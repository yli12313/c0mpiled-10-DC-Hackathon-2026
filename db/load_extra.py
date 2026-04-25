#!/usr/bin/env python3
"""Load missions, planet_candidates, and neo_close_approaches into PostgreSQL."""

import csv
import json
import os
import psycopg2
from datetime import date

DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "c0mpiled",
    "user": "postgres",
    "password": os.environ["PGPASSWORD"],
}

MISSIONS = [
    ("Kepler",       "NASA", "2009-03-07", "2018-10-30", "retired",  "space",  "Transit",         "Kepler",          "Surveyed 150,000 stars for transiting planets in the Cygnus constellation."),
    ("K2",           "NASA", "2014-06-01", "2018-10-30", "retired",  "space",  "Transit",         "K2",              "Extended Kepler mission surveying ecliptic fields after reaction wheel failure."),
    ("TESS",         "NASA", "2018-04-18", None,         "active",   "space",  "Transit",         "Transiting Exoplanet Survey Satellite (TESS)", "All-sky survey targeting nearby bright stars for transiting exoplanets."),
    ("Hubble",       "NASA", "1990-04-24", None,         "active",   "space",  "Multiple",        "Hubble Space Telescope",  "Multi-purpose observatory; contributes to exoplanet atmosphere studies."),
    ("Spitzer",      "NASA", "2003-08-25", "2020-01-30", "retired",  "space",  "Transit/Imaging", "Spitzer Space Telescope", "Infrared telescope used for exoplanet atmosphere characterization."),
    ("CoRoT",        "ESA",  "2006-12-27", "2013-11-17", "retired",  "space",  "Transit",         "CoRoT",           "First space mission dedicated to exoplanet detection via photometry."),
    ("Gaia",         "ESA",  "2013-12-19", None,         "active",   "space",  "Astrometry",      "Gaia",            "Astrometric survey detecting planets through stellar wobble at micro-arcsecond precision."),
    ("CHEOPS",       "ESA",  "2019-12-18", None,         "active",   "space",  "Transit",         "CHEOPS",          "Characterising known exoplanet host stars with high-precision photometry."),
    ("JWST",         "NASA", "2021-12-25", None,         "active",   "space",  "Multiple",        "James Webb Space Telescope", "Flagship infrared observatory enabling detailed exoplanet atmosphere spectroscopy."),
    ("HARPS",        "ESO",  "2003-02-11", None,         "active",   "ground", "Radial Velocity", "La Silla Observatory", "High Accuracy Radial velocity Planet Searcher; most prolific RV instrument."),
    ("HIRES",        "NASA", "1994-01-01", None,         "active",   "ground", "Radial Velocity", "W. M. Keck Observatory", "High Resolution Echelle Spectrometer at Keck; key instrument for RV planet hunting."),
    ("WASP",         "INT",  "2006-01-01", None,         "active",   "ground", "Transit",         "SuperWASP",       "Wide Angle Search for Planets; wide-field ground-based photometric survey."),
    ("HATNet",       "CfA",  "2003-01-01", None,         "active",   "ground", "Transit",         "HATNet",          "Hungarian-made Automated Telescope Network; ground-based transit survey."),
    ("Hipparcos",    "ESA",  "1989-08-08", "1993-03-17", "retired",  "space",  "Astrometry",      "Hipparcos",       "Early astrometric mission; precursor to Gaia with planet detection contributions."),
]

def parse_float(v):
    return float(v) if v and str(v).strip() else None

def parse_int(v):
    return int(v) if v and str(v).strip() else None

def load_missions(cur):
    print("Inserting missions...")
    for m in MISSIONS:
        cur.execute(
            """
            INSERT INTO missions (mission_name, agency, launch_date, end_date, status,
                                  mission_type, detection_method, disc_facility, description)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (mission_name) DO NOTHING
            """,
            m,
        )
    print(f"  {len(MISSIONS)} missions inserted.")

def load_candidates(cur):
    print("Inserting planet candidates...")
    with open("/tmp/toi.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    records = []
    for r in rows:
        records.append((
            parse_float(r["toi"]),
            r["toidisplay"].strip() or None,
            r["tfopwg_disp"].strip() or None,
            parse_float(r["ra"]),
            parse_float(r["dec"]),
            parse_float(r["st_tmag"]),
            parse_float(r["pl_orbper"]),
            parse_float(r["pl_rade"]),
            parse_float(r["pl_eqt"]),
            parse_float(r["st_teff"]),
            parse_float(r["st_logg"]),
            parse_float(r["st_rad"]),
        ))

    cur.executemany(
        """
        INSERT INTO planet_candidates
            (toi, toidisplay, disposition, ra, dec, st_tmag, pl_orbper,
             pl_rade, pl_eqt, st_teff, st_logg, st_rad)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (toi) DO NOTHING
        """,
        records,
    )
    print(f"  {len(records)} candidates inserted.")

def load_neo(cur):
    print("Inserting NEO close approaches...")
    with open("/tmp/neo.json") as f:
        neos = json.load(f)

    records = []
    for n in neos:
        records.append((
            n["neo_id"],
            n["name"],
            n["is_potentially_hazardous"],
            n["diameter_min_km"],
            n["diameter_max_km"],
            n["close_approach_date"],
            n["relative_velocity_kph"],
            n["miss_distance_km"],
            n["miss_distance_lunar"],
            n["orbiting_body"],
        ))

    cur.executemany(
        """
        INSERT INTO neo_close_approaches
            (neo_id, name, is_potentially_hazardous, diameter_min_km, diameter_max_km,
             close_approach_date, relative_velocity_kph, miss_distance_km,
             miss_distance_lunar, orbiting_body)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        records,
    )
    print(f"  {len(records)} NEO approaches inserted.")

def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    load_missions(cur)
    load_candidates(cur)
    load_neo(cur)
    conn.commit()
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
