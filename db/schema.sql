-- NASA Exoplanet Archive schema
-- Two tables: stars (host systems) and planets

CREATE TABLE IF NOT EXISTS stars (
    hostname        TEXT PRIMARY KEY,
    ra              DOUBLE PRECISION,
    dec             DOUBLE PRECISION,
    st_teff         DOUBLE PRECISION,   -- effective temperature (K)
    st_rad          DOUBLE PRECISION,   -- stellar radius (solar radii)
    st_mass         DOUBLE PRECISION,   -- stellar mass (solar masses)
    st_spectype     TEXT,               -- spectral type
    sy_dist         DOUBLE PRECISION,   -- distance (parsecs)
    sy_snum         INTEGER,            -- stars in system
    sy_pnum         INTEGER             -- known planets in system
);

CREATE TABLE IF NOT EXISTS planets (
    pl_name         TEXT PRIMARY KEY,
    hostname        TEXT REFERENCES stars(hostname),
    disc_year       INTEGER,
    discoverymethod TEXT,
    disc_facility   TEXT,
    disc_telescope  TEXT,
    pl_orbper       DOUBLE PRECISION,   -- orbital period (days)
    pl_orbsmax      DOUBLE PRECISION,   -- semi-major axis (AU)
    pl_orbeccen     DOUBLE PRECISION,   -- orbital eccentricity
    pl_rade         DOUBLE PRECISION,   -- planet radius (Earth radii)
    pl_bmasse       DOUBLE PRECISION,   -- planet mass (Earth masses)
    pl_eqt          DOUBLE PRECISION,   -- equilibrium temperature (K)
    pl_insol        DOUBLE PRECISION    -- insolation flux (Earth flux)
);

CREATE INDEX IF NOT EXISTS idx_planets_hostname    ON planets(hostname);
CREATE INDEX IF NOT EXISTS idx_planets_disc_year   ON planets(disc_year);
CREATE INDEX IF NOT EXISTS idx_planets_method      ON planets(discoverymethod);
CREATE INDEX IF NOT EXISTS idx_planets_pl_rade     ON planets(pl_rade);
CREATE INDEX IF NOT EXISTS idx_planets_pl_eqt      ON planets(pl_eqt);

-- Major planet-hunting space missions
CREATE TABLE IF NOT EXISTS missions (
    mission_name    TEXT PRIMARY KEY,
    agency          TEXT,
    launch_date     DATE,
    end_date        DATE,               -- NULL if still active
    status          TEXT,               -- active / retired / extended
    mission_type    TEXT,               -- space / ground
    detection_method TEXT,
    disc_facility   TEXT,               -- matches planets.disc_facility for joins
    description     TEXT
);

-- TESS Objects of Interest — unconfirmed planet candidates
CREATE TABLE IF NOT EXISTS planet_candidates (
    toi             DOUBLE PRECISION PRIMARY KEY,
    toidisplay      TEXT,
    disposition     TEXT,               -- PC=candidate, CP=confirmed, FP=false positive, FA=false alarm
    ra              DOUBLE PRECISION,
    dec             DOUBLE PRECISION,
    st_tmag         DOUBLE PRECISION,   -- TESS magnitude of host star
    pl_orbper       DOUBLE PRECISION,   -- orbital period (days)
    pl_rade         DOUBLE PRECISION,   -- planet radius (Earth radii)
    pl_eqt          DOUBLE PRECISION,   -- equilibrium temperature (K)
    st_teff         DOUBLE PRECISION,   -- host star effective temperature (K)
    st_logg         DOUBLE PRECISION,   -- host star surface gravity
    st_rad          DOUBLE PRECISION    -- host star radius (solar radii)
);

CREATE INDEX IF NOT EXISTS idx_candidates_disp   ON planet_candidates(disposition);
CREATE INDEX IF NOT EXISTS idx_candidates_orbper ON planet_candidates(pl_orbper);
CREATE INDEX IF NOT EXISTS idx_candidates_rade   ON planet_candidates(pl_rade);

-- Near Earth Object close approach events
CREATE TABLE IF NOT EXISTS neo_close_approaches (
    id                      SERIAL PRIMARY KEY,
    neo_id                  TEXT,
    name                    TEXT,
    is_potentially_hazardous BOOLEAN,
    diameter_min_km         DOUBLE PRECISION,
    diameter_max_km         DOUBLE PRECISION,
    close_approach_date     DATE,
    relative_velocity_kph   DOUBLE PRECISION,
    miss_distance_km        DOUBLE PRECISION,
    miss_distance_lunar     DOUBLE PRECISION,   -- in lunar distances
    orbiting_body           TEXT
);

CREATE INDEX IF NOT EXISTS idx_neo_date      ON neo_close_approaches(close_approach_date);
CREATE INDEX IF NOT EXISTS idx_neo_hazardous ON neo_close_approaches(is_potentially_hazardous);
CREATE INDEX IF NOT EXISTS idx_neo_miss_km   ON neo_close_approaches(miss_distance_km);
