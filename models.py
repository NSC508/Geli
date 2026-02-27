"""SQLite database models for Geli — multi-media rankings storage."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "geli.db")

VALID_MEDIA_TYPES = {"games", "books", "movies", "tv"}


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist and migrate if needed."""
    conn = get_db()

    # Check if we need to migrate from the old schema
    cursor = conn.execute("PRAGMA table_info(games)")
    columns = {row["name"] for row in cursor.fetchall()}

    if not columns:
        # Fresh install — create the new schema
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                external_id  TEXT NOT NULL,
                media_type   TEXT NOT NULL CHECK(media_type IN ('games','books','movies','tv')),
                name         TEXT NOT NULL,
                cover_url    TEXT,
                meta_line    TEXT,
                genres       TEXT,
                release_year INTEGER,
                summary      TEXT,
                tier         TEXT NOT NULL CHECK(tier IN ('like','neutral','dislike')),
                rank_position INTEGER NOT NULL,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (external_id, media_type)
            );
        """)
    elif "media_type" not in columns:
        # Migrate from old single-table games schema → new multi-media schema
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                external_id  TEXT NOT NULL,
                media_type   TEXT NOT NULL CHECK(media_type IN ('games','books','movies','tv')),
                name         TEXT NOT NULL,
                cover_url    TEXT,
                meta_line    TEXT,
                genres       TEXT,
                release_year INTEGER,
                summary      TEXT,
                tier         TEXT NOT NULL CHECK(tier IN ('like','neutral','dislike')),
                rank_position INTEGER NOT NULL,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (external_id, media_type)
            );

            INSERT OR IGNORE INTO items
                (external_id, media_type, name, cover_url, meta_line, genres,
                 release_year, summary, tier, rank_position, created_at)
            SELECT
                CAST(igdb_id AS TEXT), 'games', name, cover_url, platforms, genres,
                release_year, summary, tier, rank_position, created_at
            FROM games;

            DROP TABLE IF EXISTS games;
        """)
    # If 'items' table already exists with media_type, nothing to do

    conn.commit()
    conn.close()


def add_item(item_data, media_type, tier, rank_position):
    """Insert a new item into the database."""
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO items
           (external_id, media_type, name, cover_url, meta_line, genres,
            release_year, summary, tier, rank_position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(item_data["external_id"]),
            media_type,
            item_data["name"],
            item_data.get("cover_url"),
            item_data.get("meta_line", ""),
            item_data.get("genres", ""),
            item_data.get("release_year"),
            item_data.get("summary", ""),
            tier,
            rank_position,
        ),
    )
    conn.commit()
    conn.close()


def get_items_by_tier(media_type, tier):
    """Get all items in a tier for a media type, ordered by rank_position."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM items WHERE media_type = ? AND tier = ? ORDER BY rank_position ASC",
        (media_type, tier),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_ranked_items(media_type):
    """Get all items for a media type ordered by tier then rank."""
    conn = get_db()
    rows = conn.execute("""
        SELECT *,
            CASE tier
                WHEN 'like' THEN 1
                WHEN 'neutral' THEN 2
                WHEN 'dislike' THEN 3
            END as tier_order
        FROM items
        WHERE media_type = ?
        ORDER BY tier_order ASC, rank_position ASC
    """, (media_type,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_items(media_type):
    """Return total number of ranked items for a media type."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM items WHERE media_type = ?", (media_type,)
    ).fetchone()[0]
    conn.close()
    return count


def count_items_in_tier(media_type, tier):
    """Return number of items in a specific tier for a media type."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM items WHERE media_type = ? AND tier = ?",
        (media_type, tier),
    ).fetchone()[0]
    conn.close()
    return count


def get_item_at_rank(media_type, tier, rank_position):
    """Get the item at a specific rank position within a tier."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM items WHERE media_type = ? AND tier = ? AND rank_position = ?",
        (media_type, tier, rank_position),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def shift_ranks_down(media_type, tier, from_position):
    """Shift all items at or after from_position down by 1."""
    conn = get_db()
    conn.execute(
        """UPDATE items SET rank_position = rank_position + 1
           WHERE media_type = ? AND tier = ? AND rank_position >= ?""",
        (media_type, tier, from_position),
    )
    conn.commit()
    conn.close()


def item_exists(media_type, external_id):
    """Check if an item is already ranked."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM items WHERE media_type = ? AND external_id = ?",
        (media_type, str(external_id)),
    ).fetchone()
    conn.close()
    return row is not None


def remove_item(media_type, external_id):
    """Remove an item from rankings."""
    conn = get_db()
    item = conn.execute(
        "SELECT tier, rank_position FROM items WHERE media_type = ? AND external_id = ?",
        (media_type, str(external_id)),
    ).fetchone()
    if item:
        conn.execute(
            "DELETE FROM items WHERE media_type = ? AND external_id = ?",
            (media_type, str(external_id)),
        )
        conn.execute(
            """UPDATE items SET rank_position = rank_position - 1
               WHERE media_type = ? AND tier = ? AND rank_position > ?""",
            (media_type, item["tier"], item["rank_position"]),
        )
        conn.commit()
    conn.close()
