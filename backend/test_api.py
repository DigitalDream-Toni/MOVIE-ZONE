import requests
import time

BASE = "http://localhost:8000"
passed = 0
total = 0

time.sleep(1)


def test(method, path, body=None, token=None, expect_status=None):
    global passed, total
    total += 1
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE}{path}"
    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, json=body, headers=headers)
    elif method == "PUT":
        r = requests.put(url, json=body, headers=headers)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers)

    if expect_status and r.status_code != expect_status:
        print(f"  [FAIL] {method} {path}: expected {expect_status}, got {r.status_code}")
        return None

    print(f"  [OK] {method} {path}: {r.status_code}")
    passed += 1
    try:
        return r.json()
    except:
        return r.text


print("\n=== MOVIE ZONE API Tests ===\n")

# 1. Get movies
data = test("GET", "/api/movies")
print(f"    -> {len(data)} movies loaded")

# 2. Get series
data = test("GET", "/api/series")
print(f"    -> {len(data)} series loaded")

# 3. Login
data = test("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
token = data["token"]
print(f"    -> Token obtained")

# 4. Stats
data = test("GET", "/api/admin/stats", token=token)
print(f"    -> Movies: {data['stats']['movieCount']}, Series: {data['stats']['seriesCount']}, Episodes: {data['stats']['episodeCount']}")

# 5. Create movie
data = test("POST", "/api/movies", {"title": "Python Test Movie", "year": 2025, "genre": "Action", "download_url": "https://example.com/test"}, token=token)
movie_id = data["id"]
print(f"    -> Created: {data['title']}")

# 6. Update movie
data = test("PUT", f"/api/movies/{movie_id}", {"title": "Python Test Movie Updated", "genre": "Comedy"}, token=token)
print(f"    -> Updated: {data['title']} genre={data['genre']}")

# 7. Delete movie
data = test("DELETE", f"/api/movies/{movie_id}", token=token)
print(f"    -> {data['message']}")

# 8. Search
data = test("GET", "/api/movies?search=crimson")
print(f"    -> Search 'crimson': {len(data)} results")

# 9. Genre filter
data = test("GET", "/api/movies?genre=Horror")
print(f"    -> Horror filter: {len(data)} results")

# 10. Create series
data = test("POST", "/api/series", {
    "title": "Python Test Series", "year": 2026, "genre": "Drama",
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
found = any(s["title"] == "Python Test Series" for s in data)
print(f"    -> Deletion verified: {'FAILED' if found else 'OK'}")

# 14. Public genres
data = test("GET", "/api/admin/genres/public")
print(f"    -> Genres: {data}")

print(f"\n=== {passed}/{total} tests passed ===\n")
