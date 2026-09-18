"""
Combined test: starts the FastAPI server in-process, runs API tests via HTTP, then exits.
"""
import sys
import os
import threading
import time
import uvicorn

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Ensure fresh database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "moviezone.db")
if os.path.exists(db_path):
    os.remove(db_path)

from db import init_db
init_db()

from main import app

# Start server in a background thread
config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
server = uvicorn.Server(config)

thread = threading.Thread(target=server.run, daemon=True)
thread.start()

# Wait for server to be ready
time.sleep(3)

# Run tests
import requests

BASE = "http://127.0.0.1:8000"
passed = 0
total = 0


def test(method, path, body=None, token=None, expect_status=None):
    global passed, total
    total += 1
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE}{path}"
    if method == "GET":
        r = requests.get(url, headers=headers, timeout=10)
    elif method == "POST":
        r = requests.post(url, json=body, headers=headers, timeout=10)
    elif method == "PUT":
        r = requests.put(url, json=body, headers=headers, timeout=10)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers, timeout=10)

    if expect_status and r.status_code != expect_status:
        print(f"  [FAIL] {method} {path}: expected {expect_status}, got {r.status_code}")
        return None

    print(f"  [OK] {method} {path}: {r.status_code}")
    passed += 1
    try:
        return r.json()
    except:
        return r.text


print("\n=== MOVIE ZONE API Tests (Python/FastAPI) ===\n")

# 1. Get movies
data = test("GET", "/api/movies")
print(f"    -> {len(data['movies'])} movies loaded (page {data['pagination']['page']}/{data['pagination']['total_pages']})")

# 2. Get series
data = test("GET", "/api/series")
print(f"    -> {len(data['series'])} series loaded (page {data['pagination']['page']}/{data['pagination']['total_pages']})")

# 3. Login
data = test("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
token = data["token"]
print(f"    -> Token obtained")

# 4. Stats
data = test("GET", "/api/admin/stats", token=token)
print(f"    -> Movies: {data['stats']['movieCount']}, Series: {data['stats']['seriesCount']}, Episodes: {data['stats']['episodeCount']}")

# 5. Create movie
data = test("POST", "/api/movies", {"title": "Test Movie", "year": 2025, "genre": "Action", "download_url": "https://example.com/test"}, token=token)
movie_id = data["id"]
print(f"    -> Created: {data['title']}")

# 6. Update movie
data = test("PUT", f"/api/movies/{movie_id}", {"title": "Test Movie Updated", "genre": "Comedy"}, token=token)
print(f"    -> Updated: {data['title']} genre={data['genre']}")

# 7. Delete movie
data = test("DELETE", f"/api/movies/{movie_id}", token=token)
print(f"    -> {data['message']}")

# 8. Search
data = test("GET", "/api/movies?search=crimson")
print(f"    -> Search 'crimson': {data['pagination']['total']} results")

# 9. Genre filter
data = test("GET", "/api/movies?genre=Horror")
print(f"    -> Horror filter: {data['pagination']['total']} results")

# 10. Create series
data = test("POST", "/api/series", {
    "title": "Test Series", "year": 2026, "genre": "Drama",
    "seasons": [{
        "season_number": 1, "title": "Season 1",
        "episodes": [
            {"episode_number": 1, "title": "Pilot", "download_url": "https://example.com/s1e1", "watch_url": "https://example.com/s1e1/watch"},
            {"episode_number": 2, "title": "Chapter Two", "download_url": "https://example.com/s1e2"}
        ]
    }]
}, token=token)
series_id = data["id"]
print(f"    -> Created: {data['title']}, Seasons: {len(data['seasons'])}")

# 11. Get series detail
data = test("GET", f"/api/series/{series_id}")
print(f"    -> Seasons: {len(data['seasons'])}, Episodes in S1: {len(data['seasons'][0]['episodes'])}")

# 12. Delete series
data = test("DELETE", f"/api/series/{series_id}", token=token)
print(f"    -> {data['message']}")

# 13. Verify deletion
data = test("GET", "/api/series")
found = any(s["title"] == "Test Series" for s in data["series"])
print(f"    -> Deletion verified: {'FAILED' if found else 'OK'}")

# 14. Pagination
data = test("GET", "/api/movies?page=1&per_page=5")
print(f"    -> Page 1 of {data['pagination']['total_pages']}: {len(data['movies'])} movies")
data2 = test("GET", "/api/movies?page=2&per_page=5")
print(f"    -> Page 2 of {data2['pagination']['total_pages']}: {len(data2['movies'])} movies")

# 15. Public genres
data = test("GET", "/api/admin/genres/public")
print(f"    -> Genres: {data}")

print(f"\n=== {passed}/{total} tests passed ===")

server.should_exit = True
