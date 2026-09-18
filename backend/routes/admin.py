from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import os

from db import get_db
from routes.auth import verify_token

try:
    import httpx
except ImportError:
    httpx = None

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Where uploaded images live on disk (backend/uploads)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def _movie_rows(conn, extra=""):
    return [dict(r) for r in conn.execute(f"SELECT * FROM movies {extra}").fetchall()]


def _series_rows(conn, extra=""):
    return [dict(r) for r in conn.execute(f"SELECT * FROM series {extra}").fetchall()]


@router.get("/stats")
def get_stats(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()

    movie_count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    series_count = conn.execute("SELECT COUNT(*) FROM series").fetchone()[0]
    episode_count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    genre_movies = [r[0] for r in conn.execute("SELECT DISTINCT genre FROM movies WHERE genre != ''").fetchall()]
    genre_series = [r[0] for r in conn.execute("SELECT DISTINCT genre FROM series WHERE genre != ''").fetchall()]
    genre_count = len(set(genre_movies + genre_series))

    recent_movies = _movie_rows(conn, "ORDER BY created_at DESC LIMIT 5")
    recent_series = _series_rows(conn, "ORDER BY created_at DESC LIMIT 5")

    conn.close()
    return {
        "stats": {
            "movieCount": movie_count,
            "seriesCount": series_count,
            "episodeCount": episode_count,
            "genreCount": genre_count,
        },
        "recentMovies": recent_movies,
        "recentSeries": recent_series,
    }


@router.get("/image-health")
def get_image_health(authorization: Optional[str] = Header(None)):
    """
    Check every movie/series poster and backdrop that references an
    uploaded file and report which files are missing.

    Cloudinary-hosted images (full https://res.cloudinary.com/... URLs)
    are skipped - Cloudinary serves them directly from its CDN.

    Local paths (development mode only) are checked against disk.
    Root cause this guards against: files being deleted outside the app
    (e.g. a deploy to Render, where the disk is wiped) while the database
    keeps pointing at them - producing silent 404s everywhere.
    """
    verify_token(authorization)
    conn = get_db()

    broken = []
    checked = 0
    try:
        for table, label in (("movies", "movie"), ("series", "series")):
            rows = conn.execute(
                f"SELECT id, title, poster, backdrop FROM {table}"
            ).fetchall()
            for row in rows:
                for column in ("poster", "backdrop"):
                    path = row[column]
                    if not path or not path.startswith("/api/upload/images/"):
                        continue  # empty, external URL, or Cloudinary
                    checked += 1
                    rel = path[len("/api/upload/images/"):]
                    if os.path.exists(os.path.join(UPLOAD_DIR, rel)):
                        continue
                    broken.append(
                        {
                            "type": label,
                            "id": row["id"],
                            "title": row["title"],
                            "field": column,
                            "path": path,
                            "editUrl": f"/admin/edit-content.html?type={label}&id={row['id']}",
                            "note": (
                                "Not found on this server's disk. On Render the disk is wiped "
                                "on every deploy - configure CLOUDINARY_URL and re-upload this image."
                            ),
                        }
                    )
    finally:
        conn.close()

    return {"ok": len(broken) == 0, "checked": checked, "broken": broken}


@router.get("/url-health")
def get_url_health(authorization: Optional[str] = Header(None)):
    """
    Check every download_url / watch_url held by movies, series,
    and episodes and report ones that are unreachable.

    We only probe URLs that look like real web addresses (http/https)
    and that point away from this server, so we never waste time
    hitting the backend's own API. Each candidate gets one short GET
    with a per-site timeout; a second outstanding request to the same
    host is skipped since the first result usually applies.
    """
    verify_token(authorization)
    if httpx is None:
        raise RuntimeError("httpx is required for the URL health check")

    conn = get_db()

    # Targets: (type_label, id, title, field, url)
    targets = []
    for table, label in (("movies", "movie"), ("series", "series")):
        rows = conn.execute(
            f"SELECT id, title, download_url, watch_url FROM {table}"
        ).fetchall()
        for row in rows:
            for field, col in (("download_url", "download_url"), ("watch_url", "watch_url")):
                url = row[col]
                if url and url.startswith(("http://", "https://")):
                    targets.append((label, row["id"], row["title"] if row["title"] is not None else label, field, url))

    # Episodes live under their parent series; title from the parent.
    episode_rows = conn.execute(
        "SELECT e.id, e.download_url, e.watch_url, s.title AS series_title "
        "FROM episodes e JOIN seasons s ON s.id = e.season_id"
    ).fetchall()
    for row in episode_rows:
        for field, col in (("download_url", "download_url"), ("watch_url", "watch_url")):
            url = row[col]
            if url and url.startswith(("http://", "https://")):
                targets.append(("episode", row["id"], row["series_title"] or "Episode", field, url))

    conn.close()

    checked = 0
    broken = []
    in_flight: dict[str, dict] = {}  # host -> status dict from a concurrent probe
    client = httpx.Client(timeout=httpx.Timeout(4.0, connect=2.0))

    for kind, id_, title, field, url in targets:
        host = httpx.URL(url).host or ip_address(url)
        if host in in_flight:
            # Already probing this host; reuse the result.
            status = in_flight[host]
        else:
            try:
                resp = client.head(url, follow_redirects=True, headers={"User-Agent": "MovieZone-Admin-Health/1.0"})
                status = {"status": resp.status_code, "ok": 200 <= resp.status_code < 400}
            except httpx.HTTPStatusError as e:
                status = {"status": None, "ok": False, "error": f"{e.response.status_code if e.response is not None else 'ERR'}"}
            except httpx.HTTPError as e:
                status = {"status": None, "ok": False, "error": repr(e)[:60]}
            in_flight[host] = status

        checked += 1
        if not status["ok"]:
            broken.append(
                {
                    "type": kind,
                    "id": id_,
                    "title": title,
                    "field": field,
                    "url": url,
                    "detail": status.get("error") or f"HTTP {status['status']}",
                }
            )

    client.close()
    return {"ok": len(broken) == 0, "checked": checked, "broken": broken}


@router.get("/genres")
def get_genres(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_db()
    genres = [r[0] for r in conn.execute("""
        SELECT DISTINCT genre FROM movies WHERE genre != ''
        UNION
        SELECT DISTINCT genre FROM series WHERE genre != ''
        ORDER BY genre
    """).fetchall()]
    conn.close()
    return genres


@router.get("/genres/public")
def get_genres_public():
    conn = get_db()
    genres = [r[0] for r in conn.execute("""
        SELECT DISTINCT genre FROM movies WHERE genre != ''
        UNION
        SELECT DISTINCT genre FROM series WHERE genre != ''
        ORDER BY genre
    """).fetchall()]
    conn.close()
    return genres
