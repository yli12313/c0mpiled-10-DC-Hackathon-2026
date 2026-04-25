#!/usr/bin/env python3
"""Load NASA Exoplanet Archive CSV into PostgreSQL."""

import csv
import os
import psycopg2

DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "c0mpiled",
    "user": "postgres",
    "password": os.environ["PGPASSWORD"],
}

CSV_PATH = "/tmp/exoplanets_slim.csv"

def parse_float(v):
    return float(v) if v and v.strip() else None

def parse_int(v):
    return int(v) if v and v.strip() else None

def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Deduplicate stars by hostname
    stars = {}
    for r in rows:
        hn = r["hostname"].strip()
        if hn not in stars:
            stars[hn] = {
                "hostname":    hn,
                "ra":          parse_float(r["ra"]),
                "dec":         parse_float(r["dec"]),
                "st_teff":     parse_float(r["st_teff"]),
                "st_rad":      parse_float(r["st_rad"]),
                "st_mass":     parse_float(r["st_mass"]),
                "st_spectype": r["st_spectype"].strip() or None,
                "sy_dist":     parse_float(r["sy_dist"]),
                "sy_snum":     parse_int(r["sy_snum"]),
                "sy_pnum":     parse_int(r["sy_pnum"]),
            }

    print(f"Inserting {len(stars)} stars...")
    cur.executemany(
        """
        INSERT INTO stars (hostname, ra, dec, st_teff, st_rad, st_mass,
                           st_spectype, sy_dist, sy_snum, sy_pnum)
        VALUES (%(hostname)s, %(ra)s, %(dec)s, %(st_teff)s, %(st_rad)s,
                %(st_mass)s, %(st_spectype)s, %(sy_dist)s, %(sy_snum)s, %(sy_pnum)s)
        ON CONFLICT (hostname) DO NOTHING
        """,
        list(stars.values()),
    )

    print(f"Inserting {len(rows)} planets...")
    planets = []
    for r in rows:
        planets.append({
            "pl_name":        r["pl_name"].strip(),
            "hostname":       r["hostname"].strip(),
            "disc_year":      parse_int(r["disc_year"]),
            "discoverymethod":r["discoverymethod"].strip() or None,
            "disc_facility":  r["disc_facility"].strip() or None,
            "disc_telescope": r["disc_telescope"].strip() or None,
            "pl_orbper":      parse_float(r["pl_orbper"]),
            "pl_orbsmax":     parse_float(r["pl_orbsmax"]),
            "pl_orbeccen":    parse_float(r["pl_orbeccen"]),
            "pl_rade":        parse_float(r["pl_rade"]),
            "pl_bmasse":      parse_float(r["pl_bmasse"]),
            "pl_eqt":         parse_float(r["pl_eqt"]),
            "pl_insol":       parse_float(r["pl_insol"]),
        })

    cur.executemany(
        """
        INSERT INTO planets (pl_name, hostname, disc_year, discoverymethod,
                             disc_facility, disc_telescope, pl_orbper, pl_orbsmax,
                             pl_orbeccen, pl_rade, pl_bmasse, pl_eqt, pl_insol)
        VALUES (%(pl_name)s, %(hostname)s, %(disc_year)s, %(discoverymethod)s,
                %(disc_facility)s, %(disc_telescope)s, %(pl_orbper)s, %(pl_orbsmax)s,
                %(pl_orbeccen)s, %(pl_rade)s, %(pl_bmasse)s, %(pl_eqt)s, %(pl_insol)s)
        ON CONFLICT (pl_name) DO NOTHING
        """,
        planets,
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
