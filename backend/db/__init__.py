"""
MOVIE ZONE - Database Layer
============================

This file handles all database operations using SQLite (a simple database
that stores everything in a single file).

WHAT IS A DATABASE?
- A database is like a collection of spreadsheets
- Each "table" is like a spreadsheet with columns and rows
- We use SQL commands to add, read, update, and delete data

OUR TABLES:
- admins: Admin login accounts (username + password)
- movies: All individual movies
- series: All TV series (show names)
- seasons: Seasons within a series (Season 1, Season 2, etc.)
- episodes: Individual episodes within seasons

HOW TABLES RELATE:
  series (Dark Protocol)
    -> seasons (Season 1, Season 2)
       -> episodes (Episode 1, Episode 2, Episode 3, etc.)
"""

import sqlite3
import os
import uuid
import bcrypt
from datetime import datetime

# The database file will be stored here
DB_PATH = os.path.join(os.path.dirname(__file__), "moviezone.db")


def get_db():
    """
    Get a connection to the database.
    Every time we need to read or write data, we call this function.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Makes results easier to work with
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return conn


def init_db():
    """
    Initialize the database:
    1. Create tables if they don't exist
    2. Create default admin account
    3. Add sample movies/series for testing
    """
    conn = get_db()
    cursor = conn.cursor()

    # ============================================
    # CREATE TABLES
    # Each CREATE TABLE statement creates a new "spreadsheet"
    # ============================================

    cursor.executescript("""
        -- Admin accounts (for the admin dashboard)
        CREATE TABLE IF NOT EXISTS admins (
            id TEXT PRIMARY KEY,           -- Unique ID for each admin
            username TEXT UNIQUE NOT NULL, -- Login username (must be unique)
            password TEXT NOT NULL,        -- Hashed password (not plain text!)
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Movies (individual films)
        CREATE TABLE IF NOT EXISTS movies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,           -- Movie title (required)
            year INTEGER,                  -- Release year
            description TEXT,              -- Plot summary
            genre TEXT,                    -- Genre (Action, Comedy, etc.)
            poster TEXT,                   -- URL to poster image
            backdrop TEXT,                 -- URL to backdrop/banner image
            movie_type TEXT DEFAULT 'movie',
            download_url TEXT,             -- Where users can download the movie
            watch_url TEXT,                -- Where users can watch/preview
            is_featured INTEGER DEFAULT 0, -- 1 = show on homepage hero
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- TV Series (show names like "Dark Protocol")
        CREATE TABLE IF NOT EXISTS series (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER,
            description TEXT,
            genre TEXT,
            poster TEXT,
            backdrop TEXT,
            is_featured INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Seasons (within a series)
        CREATE TABLE IF NOT EXISTS seasons (
            id TEXT PRIMARY KEY,
            series_id TEXT NOT NULL,        -- Which series this season belongs to
            season_number INTEGER NOT NULL, -- Season 1, Season 2, etc.
            title TEXT,                     -- Optional title override
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        );

        -- Episodes (within a season)
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            season_id TEXT NOT NULL,        -- Which season this episode belongs to
            episode_number INTEGER NOT NULL, -- Episode 1, Episode 2, etc.
            title TEXT NOT NULL,
            description TEXT,
            download_url TEXT,              -- Where users can download the episode
            watch_url TEXT,                 -- Where users can watch the episode
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE
        );

        -- User reviews & ratings
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            movie_id TEXT,                -- Reference to movie (if rating a movie)
            series_id TEXT,               -- Reference to series (if rating a series)
            user_id TEXT,                 -- Anonymous user identifier
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        );
    """)

    # ============================================
    # CREATE DEFAULT ADMIN ACCOUNT
    # Username: admin
    # Password: admin123
    # ============================================
    admin_count = cursor.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    if admin_count == 0:
        # Hash the password with bcrypt (never store plain text passwords!)
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO admins (id, username, password) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), "admin", hashed),
        )
        print("  Default admin created: admin / admin123")

    # ============================================
    # SEED SAMPLE DATA
    # Add 18 movies and 2 series so the site has content to display
    # ============================================
    movie_count = cursor.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    if movie_count == 0:
        _seed_data(cursor)

    conn.commit()

    # Optional: add lightweight view-tracking column if it is missing.
    # This keeps the public homepage view hook working without breaking
    # existing databases.
    try:
        if conn.execute(
            "SELECT 1 FROM pragma_table_info('movies') WHERE name = 'views'"
        ).fetchone() is None:
            conn.execute("ALTER TABLE movies ADD COLUMN views INTEGER DEFAULT 0")
        if conn.execute(
            "SELECT 1 FROM pragma_table_info('series') WHERE name = 'views'"
        ).fetchone() is None:
            conn.execute("ALTER TABLE series ADD COLUMN views INTEGER DEFAULT 0")

        if conn.execute(
            "SELECT 1 FROM pragma_table_info('series') WHERE name = 'is_featured'"
        ).fetchone() is None:
            conn.execute("ALTER TABLE series ADD COLUMN is_featured INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        # If migration fails for any reason, continue without optional columns.
        pass

    conn.close()


def _seed_data(cursor):
    """
    Add sample movies and series to the database.
    This gives us content to test with.
    """
    now = datetime.utcnow().isoformat()

    # ============================================
    # SAMPLE MOVIES (18 movies across different genres)
    # Each tuple contains: (title, year, genre, description, poster, backdrop, download_url, watch_url, is_featured)
    # ============================================
    movies = [
        ("Crimson Horizon", 2024, "Action", "A former intelligence agent is pulled back into the world of espionage when a shadowy organization threatens global security.", "https://picsum.photos/seed/crimson/400/600", "https://picsum.photos/seed/crimson-bg/1920/1080", "https://example.com/download/crimson-horizon", "https://example.com/watch/crimson-horizon", 1),
        ("The Last Garden", 2024, "Drama", "In a world where nature has been privatized, a botanist fights to preserve the last wild garden on Earth.", "https://picsum.photos/seed/garden/400/600", "https://picsum.photos/seed/garden-bg/1920/1080", "https://example.com/download/last-garden", "https://example.com/watch/last-garden", 1),
        ("Neon Shadows", 2023, "Sci-Fi", "In a cyberpunk future, a detective with synthetic memories investigates a series of impossible murders.", "https://picsum.photos/seed/neon/400/600", "https://picsum.photos/seed/neon-bg/1920/1080", "https://example.com/download/neon-shadows", None, 0),
        ("Laughing Matters", 2024, "Comedy", "A struggling stand-up comedian discovers that her awkward life stories are the key to comedy gold.", "https://picsum.photos/seed/laugh/400/600", "https://picsum.photos/seed/laugh-bg/1920/1080", "https://example.com/download/laughing-matters", "https://example.com/watch/laughing-matters", 0),
        ("The Abyss Below", 2024, "Horror", "A deep-sea research vessel uncovers an ancient evil lurking in the ocean depths.", "https://picsum.photos/seed/abyss/400/600", "https://picsum.photos/seed/abyss-bg/1920/1080", "https://example.com/download/abyss-below", None, 0),
        ("Burning Bridges", 2023, "Romance", "Two rival architects are forced to work together on a landmark project.", "https://picsum.photos/seed/bridges/400/600", "https://picsum.photos/seed/bridges-bg/1920/1080", "https://example.com/download/burning-bridges", "https://example.com/watch/burning-bridges", 0),
        ("Code Red", 2024, "Thriller", "A cybersecurity expert races against time when a massive data breach threatens classified secrets.", "https://picsum.photos/seed/codered/400/600", "https://picsum.photos/seed/codered-bg/1920/1080", "https://example.com/download/code-red", None, 0),
        ("Wild Hearts", 2024, "Adventure", "Three friends embark on an epic journey across untamed wilderness.", "https://picsum.photos/seed/wildhearts/400/600", "https://picsum.photos/seed/wildhearts-bg/1920/1080", "https://example.com/download/wild-hearts", "https://example.com/watch/wild-hearts", 0),
        ("Lagos Nights", 2024, "Drama", "In the vibrant streets of Lagos, a young musician navigates love, ambition, and cultural identity.", "https://picsum.photos/seed/lagos/400/600", "https://picsum.photos/seed/lagos-bg/1920/1080", "https://example.com/download/lagos-nights", "https://example.com/watch/lagos-nights", 1),
        ("Pixel Dreams", 2023, "Anime", "A lonely pixel character discovers a hidden world inside a vintage game console.", "https://picsum.photos/seed/pixel/400/600", "https://picsum.photos/seed/pixel-bg/1920/1080", "https://example.com/download/pixel-dreams", "https://example.com/watch/pixel-dreams", 0),
        ("Under the Radar", 2024, "Thriller", "A pilot flying a secret cargo discovers her manifest is a lie.", "https://picsum.photos/seed/radar/400/600", "https://picsum.photos/seed/radar-bg/1920/1080", "https://example.com/download/under-radar", None, 0),
        ("The Comedy Club", 2023, "Comedy", "When a legendary comedy club faces closure, its regulars band together for one epic night.", "https://picsum.photos/seed/comedyclub/400/600", "https://picsum.photos/seed/comedyclub-bg/1920/1080", "https://example.com/download/comedy-club", "https://example.com/watch/comedy-club", 0),
        ("Steel Resolve", 2024, "Action", "An elite martial artist is drawn into an underground fighting tournament.", "https://picsum.photos/seed/steel/400/600", "https://picsum.photos/seed/steel-bg/1920/1080", "https://example.com/download/steel-resolve", "https://example.com/watch/steel-resolve", 0),
        ("Whispers in the Dark", 2024, "Horror", "A family moves into a centuries-old estate with its own dark agenda.", "https://picsum.photos/seed/whispers/400/600", "https://picsum.photos/seed/whispers-bg/1920/1080", "https://example.com/download/whispers-dark", None, 0),
        ("Starlight Express", 2023, "Sci-Fi", "The first interstellar passenger train departs Earth with 500 colonists.", "https://picsum.photos/seed/starlight/400/600", "https://picsum.photos/seed/starlight-bg/1920/1080", "https://example.com/download/starlight", "https://example.com/watch/starlight", 0),
        ("Abuja Rising", 2024, "Nigerian", "A young lawyer returns to Abuja to fight for justice in a landmark corruption case.", "https://picsum.photos/seed/abuja/400/600", "https://picsum.photos/seed/abuja-bg/1920/1080", "https://example.com/download/abuja-rising", "https://example.com/watch/abuja-rising", 0),
        ("The Mosaic", 2024, "Crime", "A retired detective is called back when art heists reveal connections to her unsolved case.", "https://picsum.photos/seed/mosaic/400/600", "https://picsum.photos/seed/mosaic-bg/1920/1080", "https://example.com/download/mosaic", None, 0),
        ("Velocity", 2023, "Action", "A street racer enters the world's most dangerous underground racing circuit.", "https://picsum.photos/seed/velocity/400/600", "https://picsum.photos/seed/velocity-bg/1920/1080", "https://example.com/download/velocity", "https://example.com/watch/velocity", 0),
    ]

    # Insert each movie into the database
    for m in movies:
        cursor.execute(
            """INSERT INTO movies (id, title, year, genre, description, poster, backdrop,
               movie_type, download_url, watch_url, is_featured, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'movie', ?, ?, ?, ?)""",
            (str(uuid.uuid4()), m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], now),
        )

    # ============================================
    # SAMPLE SERIES (2 series with seasons and episodes)
    # ============================================
    series_id_1 = str(uuid.uuid4())
    series_id_2 = str(uuid.uuid4())

    # Insert the two series
    cursor.execute(
        """INSERT INTO series (id, title, year, description, genre, poster, backdrop, is_featured, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (series_id_1, "Dark Protocol", 2023,
         "An elite team of covert operatives uncovers a global conspiracy that threatens to reshape the world order.",
         "Thriller", "https://picsum.photos/seed/darkprotocol/400/600",
         "https://picsum.photos/seed/darkprotocol-bg/1920/1080", now),
    )
    cursor.execute(
        """INSERT INTO series (id, title, year, description, genre, poster, backdrop, is_featured, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
        (series_id_2, "City of Dreams", 2024,
         "An interconnected drama following diverse characters in a bustling metropolis.",
         "Drama", "https://picsum.photos/seed/citydreams/400/600",
         "https://picsum.photos/seed/citydreams-bg/1920/1080", now),
    )

    # ============================================
    # SEASONS AND EPISODES
    # Each series has 2 seasons with multiple episodes
    # ============================================
    s1_id = str(uuid.uuid4())  # Dark Protocol Season 1
    s2_id = str(uuid.uuid4())  # Dark Protocol Season 2
    s3_id = str(uuid.uuid4())  # City of Dreams Season 1
    s4_id = str(uuid.uuid4())  # City of Dreams Season 2

    # Insert seasons
    cursor.execute("INSERT INTO seasons (id, series_id, season_number, title) VALUES (?, ?, 1, 'Season 1')", (s1_id, series_id_1))
    cursor.execute("INSERT INTO seasons (id, series_id, season_number, title) VALUES (?, ?, 2, 'Season 2')", (s2_id, series_id_1))
    cursor.execute("INSERT INTO seasons (id, series_id, season_number, title) VALUES (?, ?, 1, 'Season 1')", (s3_id, series_id_2))
    cursor.execute("INSERT INTO seasons (id, series_id, season_number, title) VALUES (?, ?, 2, 'Season 2')", (s4_id, series_id_2))

    # Episode data: (episode_number, title, description, download_url, watch_url)
    dp_s1 = [
        (1, "The Initiation", "A new recruit joins the team and must prove her worth.", "https://example.com/dp/s1e1", "https://example.com/dp/s1e1/watch"),
        (2, "Dead Signal", "A coded message from a missing agent leads to an abandoned facility.", "https://example.com/dp/s1e2", "https://example.com/dp/s1e2/watch"),
        (3, "Trust No One", "Paranoia sets in when the team suspects a mole.", "https://example.com/dp/s1e3", None),
        (4, "The Decode", "Breaking the encryption reveals a conspiracy.", "https://example.com/dp/s1e4", "https://example.com/dp/s1e4/watch"),
    ]
    dp_s2 = [
        (1, "New World Order", "The team resurfaces to face a more powerful enemy.", "https://example.com/dp/s2e1", "https://example.com/dp/s2e1/watch"),
        (2, "Ghost Protocol", "Past identities resurface when an old ally turns enemy.", "https://example.com/dp/s2e2", None),
        (3, "Endgame", "The final confrontation determines the fate of the world.", "https://example.com/dp/s2e3", "https://example.com/dp/s2e3/watch"),
    ]
    cd_s1 = [
        (1, "Arrival", "Newcomers arrive in the city with big dreams.", "https://example.com/cod/s1e1", "https://example.com/cod/s1e1/watch"),
        (2, "The Grind", "Making it in the city proves harder than imagined.", "https://example.com/cod/s1e2", "https://example.com/cod/s1e2/watch"),
        (3, "Connections", "Unexpected friendships form across cultural boundaries.", "https://example.com/cod/s1e3", None),
    ]
    cd_s2 = [
        (1, "Rising Tides", "Success and failure are two sides of the same coin.", "https://example.com/cod/s2e1", None),
        (2, "Crossroads", "Major life decisions test every relationship.", "https://example.com/cod/s2e2", "https://example.com/cod/s2e2/watch"),
    ]

    # Insert episodes into each season
    for ep_num, title, desc, dl, wl in dp_s1:
        cursor.execute("INSERT INTO episodes (id, season_id, episode_number, title, description, download_url, watch_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), s1_id, ep_num, title, desc, dl, wl))
    for ep_num, title, desc, dl, wl in dp_s2:
        cursor.execute("INSERT INTO episodes (id, season_id, episode_number, title, description, download_url, watch_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), s2_id, ep_num, title, desc, dl, wl))
    for ep_num, title, desc, dl, wl in cd_s1:
        cursor.execute("INSERT INTO episodes (id, season_id, episode_number, title, description, download_url, watch_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), s3_id, ep_num, title, desc, dl, wl))
    for ep_num, title, desc, dl, wl in cd_s2:
        cursor.execute("INSERT INTO episodes (id, season_id, episode_number, title, description, download_url, watch_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), s4_id, ep_num, title, desc, dl, wl))

    print("  Sample data seeded: 18 movies, 2 series, 4 seasons, 12 episodes")
