"""SQLite database models for Geli — game rankings storage."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "geli.db")


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            igdb_id     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            cover_url   TEXT,
            platforms   TEXT,
            genres      TEXT,
            release_year INTEGER,
            summary     TEXT,
            tier        TEXT NOT NULL CHECK(tier IN ('like','neutral','dislike')),
            rank_position INTEGER NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def add_game(game_data, tier, rank_position):
    """Insert a new game into the database."""
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO games
           (igdb_id, name, cover_url, platforms, genres, release_year, summary, tier, rank_position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            game_data["igdb_id"],
            game_data["name"],
            game_data.get("cover_url"),
            game_data.get("platforms", ""),
            game_data.get("genres", ""),
            game_data.get("release_year"),
            game_data.get("summary", ""),
            tier,
            rank_position,
        ),
    )
    conn.commit()
    conn.close()


def get_games_by_tier(tier):
    """Get all games in a tier, ordered by rank_position (1 = best)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM games WHERE tier = ? ORDER BY rank_position ASC", (tier,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_ranked_games():
    """Get all games ordered: like (by rank), then neutral (by rank), then dislike (by rank)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT *,
            CASE tier
                WHEN 'like' THEN 1
                WHEN 'neutral' THEN 2
                WHEN 'dislike' THEN 3
            END as tier_order
        FROM games
        ORDER BY tier_order ASC, rank_position ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_games():
    """Return total number of ranked games."""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    conn.close()
    return count


def count_games_in_tier(tier):
    """Return number of games in a specific tier."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM games WHERE tier = ?", (tier,)
    ).fetchone()[0]
    conn.close()
    return count


def get_game_at_rank(tier, rank_position):
    """Get the game at a specific rank position within a tier."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM games WHERE tier = ? AND rank_position = ?",
        (tier, rank_position),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def shift_ranks_down(tier, from_position):
    """Shift all games at or after from_position down by 1 (to make room for insertion)."""
    conn = get_db()
    conn.execute(
        """UPDATE games SET rank_position = rank_position + 1
           WHERE tier = ? AND rank_position >= ?""",
        (tier, from_position),
    )
    conn.commit()
    conn.close()


def game_exists(igdb_id):
    """Check if a game is already ranked."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM games WHERE igdb_id = ?", (igdb_id,)
    ).fetchone()
    conn.close()
    return row is not None


def remove_game(igdb_id):
    """Remove a game from rankings."""
    conn = get_db()
    game = conn.execute(
        "SELECT tier, rank_position FROM games WHERE igdb_id = ?", (igdb_id,)
    ).fetchone()
    if game:
        conn.execute("DELETE FROM games WHERE igdb_id = ?", (igdb_id,))
        # Shift remaining games up
        conn.execute(
            """UPDATE games SET rank_position = rank_position - 1
               WHERE tier = ? AND rank_position > ?""",
            (game["tier"], game["rank_position"]),
        )
        conn.commit()
    conn.close()
