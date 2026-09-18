"""
MOVIE ZONE - Reviews Route
Handles user ratings and comments for movies and series.
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
import uuid

from db import get_db
from routes.auth import verify_token

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("")
def create_review(
    movie_id: Optional[str] = Query(None),
    series_id: Optional[str] = Query(None),
    rating: Optional[int] = Query(None),
    comment: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Submit a review/rating for a movie or series."""
    if not movie_id and not series_id:
        raise HTTPException(status_code=400, detail="movie_id or series_id required.")
    if not rating or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5.")

    conn = get_db()

    # Verify the content exists
    if movie_id:
        exists = conn.execute("SELECT id FROM movies WHERE id = ?", (movie_id,)).fetchone()
    elif series_id:
        exists = conn.execute("SELECT id FROM series WHERE id = ?", (series_id,)).fetchone()
    conn.close()
    if not exists:
        raise HTTPException(status_code=404, detail="Content not found.")

    uid = user_id or str(uuid.uuid4())
    review_id = str(uuid.uuid4())
    now = __import__("datetime").datetime.utcnow().isoformat()

    conn = get_db()
    conn.execute(
        """INSERT INTO reviews (id, movie_id, series_id, user_id, rating, comment, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (review_id, movie_id or None, series_id or None, uid, rating, comment or "", now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/movies/{movie_id}")
def get_movie_reviews(
    movie_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(6, ge=1, le=50),
):
    """Get paginated reviews for a movie."""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE movie_id = ?", (movie_id,)).fetchone()[0]
    total_pages = max(1, (count + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM reviews WHERE movie_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (movie_id, per_page, offset),
    ).fetchall()
    conn.close()
    reviews = [dict(r) for r in rows]
    return {
        "reviews": reviews,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


@router.get("/series/{series_id}")
def get_series_reviews(
    series_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(6, ge=1, le=50),
):
    """Get paginated reviews for a series."""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE series_id = ?", (series_id,)).fetchone()[0]
    total_pages = max(1, (count + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM reviews WHERE series_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (series_id, per_page, offset),
    ).fetchall()
    conn.close()
    reviews = [dict(r) for r in rows]
    return {
        "reviews": reviews,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
