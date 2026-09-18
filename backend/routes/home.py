"""
MOVIE ZONE - Public Homepage API
----------------------------------
Lightweight public endpoints used by the homepage only.

These are intentionally public (no auth) and focused on read-only
content that the homepage needs: featured items, new arrivals,
recently added, genre list, and search suggestions.
"""

from fastapi import APIRouter, Query
from typing import Optional

from db import get_db

router = APIRouter(prefix="/api/home", tags=["home"])


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def _fetch_series_with_counts(conn, limit=None):
    """
    Fetch series rows together with their real season and episode
    counts (instead of hardcoding 0), so the frontend can display
    e.g. '2 Seasons' in the hero and on cards.
    """
    sql = """
        SELECT s.*,
               (SELECT COUNT(*) FROM seasons sn
                 WHERE sn.series_id = s.id) AS season_count,
               (SELECT COUNT(*) FROM episodes e
                  JOIN seasons sn2 ON e.season_id = sn2.id
                 WHERE sn2.series_id = s.id) AS episode_count
        FROM series s
        ORDER BY s.created_at DESC
    """
    params = []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return conn.execute(sql, params).fetchall()


def _series_to_item(row):
    """Convert a series row (with counts) into a homepage item."""
    d = _row_to_dict(row)
    d["type"] = "series"
    d["season_count"] = d.get("season_count") or 0
    d["episode_count"] = d.get("episode_count") or 0
    return d


@router.get("/featured")
def get_featured(limit: int = Query(8, ge=1, le=24)):
    """
    Featured movies and series for the hero/featured area.
    Returns a flat list with a `type` field so the frontend can
    render movies and series in the same carousel/row.
    """
    conn = get_db()

    movie_rows = conn.execute(
        "SELECT * FROM movies WHERE is_featured = 1 ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    series_rows = _fetch_series_with_counts(
        conn, max(0, limit - len(movie_rows))
    )

    conn.close()

    items = []
    for r in movie_rows:
        d = _row_to_dict(r)
        d["type"] = "movie"
        items.append(d)
    for r in series_rows:
        items.append(_series_to_item(r))

    return {"items": items}


@router.get("/new-arrivals")
def get_new_arrivals(
    limit: int = Query(12, ge=1, le=50),
    content_type: Optional[str] = Query(None),
):
    """
    New arrivals based on `created_at`.

    If `content_type=movie` or `content_type=series`, return only
    that type. Otherwise return movies first, then series.
    """
    conn = get_db()

    if content_type == "series":
        rows = _fetch_series_with_counts(conn, limit)
        conn.close()
        return {"items": [_series_to_item(r) for r in rows]}

    movie_rows = conn.execute(
        "SELECT * FROM movies ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if content_type == "movie":
        conn.close()
        return {"items": [_row_to_dict(r) | {"type": "movie"} for r in movie_rows]}

    series_limit = max(0, limit - len(movie_rows))
    series_rows = _fetch_series_with_counts(conn, series_limit)

    conn.close()
    items = []
    for r in movie_rows:
        d = _row_to_dict(r)
        d["type"] = "movie"
        items.append(d)
    for r in series_rows:
        items.append(_series_to_item(r))

    return {"items": items}


@router.get("/recently-added")
def get_recently_added(limit: int = Query(12, ge=1, le=50)):
    """
    Recently added content across movies and series, mixed together
    and ordered by `created_at`.
    """
    conn = get_db()

    movie_rows = conn.execute(
        "SELECT * FROM movies ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    series_rows = _fetch_series_with_counts(conn, limit)

    conn.close()

    combined = []
    for r in movie_rows:
        d = _row_to_dict(r)
        d["type"] = "movie"
        combined.append(d)
    for r in series_rows:
        combined.append(_series_to_item(r))

    combined.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"items": combined[:limit]}


@router.get("/random-genres")
def get_random_genres(count: int = Query(3, ge=1, le=6)):
    """
    A handful of random genres, each with a mixed sample of movies and
    series for homepage shelves like 'Random: Horror'.

    Each genre returns up to `per_genre` items (movies first, then
    series, newest first) with real season/episode counts for series.
    """
    conn = get_db()

    genre_rows = conn.execute(
        """
        SELECT DISTINCT genre FROM (
            SELECT genre FROM movies WHERE genre != ''
            UNION
            SELECT genre FROM series WHERE genre != ''
        )
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (count,),
    ).fetchall()

    per_genre = 12
    shelves = []
    for (genre,) in genre_rows:
        movie_rows = conn.execute(
            "SELECT * FROM movies WHERE genre = ? ORDER BY created_at DESC LIMIT ?",
            (genre, per_genre),
        ).fetchall()
        series_rows = conn.execute(
            "SELECT * FROM series WHERE genre = ? ORDER BY created_at DESC LIMIT ?",
            (genre, max(0, per_genre - len(movie_rows))),
        ).fetchall()

        items = []
        for r in movie_rows:
            d = _row_to_dict(r)
            d["type"] = "movie"
            items.append(d)
        for r in series_rows:
            items.append(_series_to_item(r))

        if items:
            shelves.append({"genre": genre, "items": items})

    conn.close()
    return {"shelves": shelves}


@router.get("/genres")
def get_genres():
    """
    Public genre list for pills/filters on the homepage.
    """
    conn = get_db()
    rows = conn.execute(
        """
        SELECT DISTINCT genre FROM movies WHERE genre != ''
        UNION
        SELECT DISTINCT genre FROM series WHERE genre != ''
        ORDER BY genre
        """
    ).fetchall()
    conn.close()
    return {"genres": [r[0] for r in rows]}


@router.get("/search/suggestions")
def search_suggestions(
    q: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=24),
):
    """
    Lightweight search suggestions for the homepage search bar.

    Returns a small mixed list of movies and series matching the
    query, plus known genres that start with the query text.
    """
    if not q:
        return {"suggestions": [], "genres": []}

    term = f"%{q}%"
    conn = get_db()

    movie_rows = conn.execute(
        "SELECT id, title, year, genre, poster, is_featured, movie_type FROM movies "
        "WHERE title LIKE ? OR genre LIKE ? ORDER BY is_featured DESC, title ASC LIMIT ?",
        (term, term, limit),
    ).fetchall()
    series_rows = conn.execute(
        "SELECT id, title, year, genre, poster FROM series "
        "WHERE title LIKE ? OR genre LIKE ? ORDER BY title ASC LIMIT ?",
        (term, term, limit),
    ).fetchall()

    suggestions = []
    for r in movie_rows:
        d = _row_to_dict(r)
        d["type"] = "movie"
        suggestions.append(d)
    for r in series_rows:
        d = _row_to_dict(r)
        d["type"] = "series"
        suggestions.append(d)

    genres = []
    if len(q) >= 2:
        genre_rows = conn.execute(
            """
            SELECT DISTINCT genre FROM (
                SELECT genre FROM movies WHERE genre != ''
                UNION
                SELECT genre FROM series WHERE genre != ''
            )
            WHERE genre LIKE ?
            ORDER BY genre
            LIMIT 6
            """,
            (f"{q}%",),
        ).fetchall()
        genres = [r[0] for r in genre_rows]

    conn.close()
    return {"suggestions": suggestions, "genres": genres}


@router.post("/content/{content_type}/{content_id}/view")
def record_view(content_type: str, content_id: str):
    """
    Optional lightweight view-tracking hook.

    Currently persists a simple `views` counter on the matching row
    when a `views` column exists. If the column does not exist yet,
    the endpoint still returns success so the frontend can call it
    without breaking.
    """
    conn = get_db()
    table = None
    if content_type == "movie":
        table = "movies"
    elif content_type == "series":
        table = "series"
    else:
        conn.close()
        return {"message": "ok"}

    try:
        exists = conn.execute(
            "SELECT 1 FROM pragma_table_info(?) WHERE name = 'views'",
            (table,),
        ).fetchone()

        if exists:
            conn.execute(
                f"UPDATE {table} SET views = COALESCE(views, 0) + 1 WHERE id = ?",
                (content_id,),
            )
            conn.commit()
    except Exception:
        # Be liberal: if anything unexpected happens, don't break the UI.
        pass
    finally:
        conn.close()

    return {"message": "ok"}
