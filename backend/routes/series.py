from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
import uuid
from datetime import datetime

from db import get_db
from models import SeriesCreate, SeriesUpdate
from routes.auth import verify_token

router = APIRouter(prefix="/api/series", tags=["series"])


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def get_seasons_with_episodes(conn, series_id: str) -> list:
    seasons = [row_to_dict(s) for s in conn.execute(
        "SELECT * FROM seasons WHERE series_id = ? ORDER BY season_number", (series_id,)
    ).fetchall()]

    for season in seasons:
        episodes = [row_to_dict(e) for e in conn.execute(
            "SELECT * FROM episodes WHERE season_id = ? ORDER BY episode_number", (season["id"],)
        ).fetchall()]
        season["episodes"] = episodes

    return seasons


@router.get("")
def get_series(
    genre: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=500),
):
    """
    Get series with pagination.
    Returns paginated results with total count, current page, and total pages.
    """
    conn = get_db()
    base_query = "SELECT * FROM series WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM series WHERE 1=1"
    params: list = []
    count_params: list = []

    if genre:
        base_query += " AND genre = ?"
        count_query += " AND genre = ?"
        params.append(genre)
        count_params.append(genre)
    if year is not None:
        base_query += " AND year = ?"
        count_query += " AND year = ?"
        params.append(year)
        count_params.append(year)
    if year_min is not None:
        base_query += " AND year >= ?"
        count_query += " AND year >= ?"
        params.append(year_min)
        count_params.append(year_min)
    if year_max is not None:
        base_query += " AND year <= ?"
        count_query += " AND year <= ?"
        params.append(year_max)
        count_params.append(year_max)
    if featured is not None:
        base_query += " AND is_featured = ?"
        count_query += " AND is_featured = ?"
        params.append(1 if featured else 0)
        count_params.append(1 if featured else 0)

    if search:
        base_query += " AND (title LIKE ? OR genre LIKE ? OR description LIKE ?)"
        count_query += " AND (title LIKE ? OR genre LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
        count_params.extend([term, term, term])

    # Include is_featured if the column exists.
    try:
        conn.execute("SELECT is_featured FROM series LIMIT 0").fetchone()
        has_featured = True
    except Exception:
        has_featured = False

    # Get total count for pagination info
        base_query += " AND (title LIKE ? OR genre LIKE ? OR description LIKE ?)"
        count_query += " AND (title LIKE ? OR genre LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
        count_params.extend([term, term, term])

    # Get total count for pagination info
    total_count = conn.execute(count_query, count_params).fetchone()[0]
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    # Apply pagination: LIMIT and OFFSET
    offset = (page - 1) * per_page
    base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    raw_rows = conn.execute(base_query, params).fetchall()
    series_list = [row_to_dict(s) for s in raw_rows]

    # Keep is_featured explicitly if the column exists.
    if has_featured:
        for s in series_list:
            s["is_featured"] = bool(s.get("is_featured"))

    # Attach seasons and episodes
    for s in series_list:
        seasons = get_seasons_with_episodes(conn, s["id"])
        s["seasons"] = seasons
        s["season_count"] = len(seasons)
        s["episode_count"] = sum(len(se["episodes"]) for se in seasons)

    conn.close()

    return {
        "series": series_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


@router.get("/{series_id}")
def get_series_detail(series_id: str):
    conn = get_db()
    series = conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
    if not series:
        conn.close()
        raise HTTPException(status_code=404, detail="Series not found.")

    result = row_to_dict(series)
    result["seasons"] = get_seasons_with_episodes(conn, series_id)
    conn.close()
    return result


@router.post("")
def create_series(req: SeriesCreate, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Title is required.")

    conn = get_db()
    series_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    conn.execute(
        """INSERT INTO series (id, title, year, description, genre, poster, backdrop, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (series_id, req.title, req.year, req.description or "", req.genre or "",
         req.poster or "", req.backdrop or "", now, now),
    )

    if req.seasons:
        for season in req.seasons:
            season_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO seasons (id, series_id, season_number, title, created_at) VALUES (?, ?, ?, ?, ?)",
                (season_id, series_id, season.season_number, season.title or f"Season {season.season_number}", now),
            )
            if season.episodes:
                for ep in season.episodes:
                    conn.execute(
                        """INSERT INTO episodes (id, season_id, episode_number, title, description,
                           download_url, watch_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), season_id, ep.episode_number, ep.title,
                         ep.description or "", ep.download_url or "", ep.watch_url, now),
                    )

    conn.commit()
    series = row_to_dict(conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone())
    series["seasons"] = get_seasons_with_episodes(conn, series_id)
    conn.close()
    return series


@router.put("/{series_id}")
def update_series(series_id: str, req: SeriesUpdate, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()
    existing = conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Series not found.")

    e = dict(existing)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE series SET title=?, year=?, description=?, genre=?, poster=?, backdrop=?,
           updated_at=? WHERE id=?""",
        (
            req.title if req.title is not None else e["title"],
            req.year if req.year is not None else e["year"],
            req.description if req.description is not None else e["description"],
            req.genre if req.genre is not None else e["genre"],
            req.poster if req.poster is not None else e["poster"],
            req.backdrop if req.backdrop is not None else e["backdrop"],
            now,
            series_id,
        ),
    )

    # Replace seasons if provided
    if req.seasons is not None:
        old_season_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM seasons WHERE series_id = ?", (series_id,)
        ).fetchall()]

        # Delete old episodes and seasons
        for sid in old_season_ids:
            conn.execute("DELETE FROM episodes WHERE season_id = ?", (sid,))
        conn.execute("DELETE FROM seasons WHERE series_id = ?", (series_id,))

        # Insert new
        for season in req.seasons:
            season_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO seasons (id, series_id, season_number, title, created_at) VALUES (?, ?, ?, ?, ?)",
                (season_id, series_id, season.season_number, season.title or f"Season {season.season_number}", now),
            )
            if season.episodes:
                for ep in season.episodes:
                    conn.execute(
                        """INSERT INTO episodes (id, season_id, episode_number, title, description,
                           download_url, watch_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), season_id, ep.episode_number, ep.title,
                         ep.description or "", ep.download_url or "", ep.watch_url, now),
                    )

    conn.commit()
    series = row_to_dict(conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone())
    series["seasons"] = get_seasons_with_episodes(conn, series_id)
    conn.close()
    return series


@router.delete("/{series_id}")
def delete_series(series_id: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()
    existing = conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Series not found.")

    # Cascading delete
    season_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM seasons WHERE series_id = ?", (series_id,)
    ).fetchall()]
    for sid in season_ids:
        conn.execute("DELETE FROM episodes WHERE season_id = ?", (sid,))
    conn.execute("DELETE FROM seasons WHERE series_id = ?", (series_id,))
    conn.execute("DELETE FROM series WHERE id = ?", (series_id,))
    conn.commit()
    conn.close()
    return {"message": "Series deleted successfully."}
