from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional, List
import uuid
from datetime import datetime

from db import get_db
from models import MovieCreate, MovieUpdate
from routes.auth import verify_token

router = APIRouter(prefix="/api/movies", tags=["movies"])


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def _bool_param(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    v = value.strip().lower()
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no", ""):
        return False
    return None


@router.get("")
def get_movies(
    genre: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    featured_str: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=500),
):
    """
    Get movies with pagination.
    Returns paginated results with total count, current page, and total pages.
    """
    conn = get_db()
    base_query = "SELECT * FROM movies WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM movies WHERE 1=1"
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
    featured_val = _bool_param(featured_str)
    if featured is True:
        base_query += " AND is_featured = 1"
        count_query += " AND is_featured = 1"
    elif featured_val is True:
        base_query += " AND is_featured = 1"
        count_query += " AND is_featured = 1"
    elif featured_val is False:
        base_query += " AND is_featured = 0"
        count_query += " AND is_featured = 0"
    if search:
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

    movies = [row_to_dict(r) for r in conn.execute(base_query, params).fetchall()]
    conn.close()
    applied = []
    if genre:
        applied.append(("genre", genre))
    if year is not None:
        applied.append(("year", year))
    if year_min is not None:
        applied.append(("year_min", year_min))
    if year_max is not None:
        applied.append(("year_max", year_max))
    if search:
        applied.append(("search", search))
    if featured is not None:
        applied.append(("featured", featured))
    if featured_str:
        applied.append(("featured_str", featured_str))

    return {
        "movies": movies,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "filters": {
            "total": total_count,
            "applied": applied,
        },
    }


@router.get("/{movie_id}")
def get_movie(movie_id: str):
    conn = get_db()
    movie = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    conn.close()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return row_to_dict(movie)


@router.post("")
def create_movie(req: MovieCreate, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Title is required.")

    conn = get_db()
    movie_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute(
        """INSERT INTO movies (id, title, year, description, genre, poster, backdrop,
           movie_type, download_url, watch_url, is_featured, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'movie', ?, ?, ?, ?, ?)""",
        (movie_id, req.title, req.year, req.description or "", req.genre or "",
         req.poster or "", req.backdrop or "", req.download_url or "",
         req.watch_url, 1 if req.is_featured else 0, now, now),
    )
    conn.commit()
    movie = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    conn.close()
    return row_to_dict(movie)


@router.put("/{movie_id}")
def update_movie(movie_id: str, req: MovieUpdate, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()
    existing = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found.")

    e = dict(existing)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE movies SET title=?, year=?, description=?, genre=?, poster=?, backdrop=?,
           download_url=?, watch_url=?, is_featured=?, updated_at=? WHERE id=?""",
        (
            req.title if req.title is not None else e["title"],
            req.year if req.year is not None else e["year"],
            req.description if req.description is not None else e["description"],
            req.genre if req.genre is not None else e["genre"],
            req.poster if req.poster is not None else e["poster"],
            req.backdrop if req.backdrop is not None else e["backdrop"],
            req.download_url if req.download_url is not None else e["download_url"],
            req.watch_url if req.watch_url is not None else e["watch_url"],
            (1 if req.is_featured else 0) if req.is_featured is not None else e["is_featured"],
            now,
            movie_id,
        ),
    )
    conn.commit()
    movie = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    conn.close()
    return row_to_dict(movie)


@router.delete("/{movie_id}")
def delete_movie(movie_id: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()
    existing = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found.")

    conn.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()
    return {"message": "Movie deleted successfully."}
