# MOVIE ZONE

A premium movie streaming and discovery website.

## Tech Stack

| Part | Technology | Why |
|------|-----------|-----|
| **Backend** | Python + FastAPI | Fast, modern, easy to understand |
| **Database** | SQLite | No setup needed, stored in one file |
| **Frontend** | HTML + CSS + JavaScript | No frameworks, beginner-friendly |
| **Auth** | JWT + bcrypt | Secure admin login |
| **File uploads** | Multipart form upload | Images stored locally in `backend/uploads/` |

## Quick Start

### 1. Install Python (if not installed)
Download from: https://www.python.org/downloads/

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the server
```bash
cd backend
python main.py
```

### 4. Open in browser
- **Public site:** http://localhost:8000/frontend/
- **Admin panel:** http://localhost:8000/admin/login.html
- **Admin dashboard:** http://localhost:8000/admin/dashboard.html
- **API docs:** http://localhost:8000/docs

> **Note:** You can also use VS Code Live Server on port 5501 for the frontend, but API calls still go to port 8000.

### 5. Admin login
- Username: `admin`
- Password: `admin123`

## Project Structure

```
MOVIE ZONE/
|
|-- .gitignore                # Git ignore rules
|
|-- frontend/                 # Public website (HTML + CSS + JS)
|   |-- index.html           # Homepage with hero carousel
|   |-- movies.html          # Browse all movies
|   |-- series.html          # Browse all series
|   |-- genres.html          # Browse by genre
|   |-- search.html          # Search movies/series
|   |-- movie-details.html   # Single movie page
|   |-- series-details.html  # Single series page
|   |-- sw.js                # Service worker
|   |-- css/
|   |   |-- style.css        # Main styles
|   |   |-- responsive.css   # Mobile/tablet styles
|   |-- js/
|       |-- app.js           # Shared JavaScript code
|       |-- home.js          # Homepage-specific logic
|
|-- admin/                    # Admin dashboard
|   |-- login.html           # Admin login page
|   |-- dashboard.html       # Stats overview
|   |-- add-content.html     # Add movie or series
|   |-- edit-content.html    # Edit movie or series
|   |-- manage-movies.html   # Manage all movies
|   |-- manage-series.html   # Manage all series
|   |-- image-health.html    # Image integrity checker
|   |-- css/
|   |   |-- admin.css        # Admin styles
|   |-- js/
|       |-- admin.js         # Admin JavaScript
|
|-- backend/                  # Python backend (FastAPI)
    |-- main.py              # Main server file (START HERE)
    |-- requirements.txt     # Python packages to install
    |-- db/
    |   |-- __init__.py      # Database setup + sample data
    |   |-- moviezone.db     # SQLite database (auto-created)
    |-- models/
    |   |-- __init__.py      # Request body schemas
    |-- routes/
    |   |-- __init__.py
    |   |-- auth.py          # Login / authentication
    |   |-- movies.py        # Movie CRUD operations
    |   |-- series.py        # Series CRUD operations
    |   |-- home.py          # Homepage data (featured, genres, search)
    |   |-- admin.py         # Dashboard stats + image health
    |   |-- upload.py        # Image upload + serving
    |   |-- reviews.py       # User reviews
    |-- uploads/
        |-- poster/          # Uploaded poster images
        |-- backdrop/        # Uploaded backdrop images
```

## How the Backend API Works

The Python backend provides these API endpoints:

### Public (no login required)
```
GET  /api/movies                    Get all movies (with filters)
GET  /api/movies/{id}               Get one movie
GET  /api/series                    Get all series (with filters)
GET  /api/series/{id}               Get one series with seasons/episodes
GET  /api/home/featured             Featured content for hero carousel
GET  /api/home/new-arrivals         New arrivals
GET  /api/home/recently-added       Recently added content
GET  /api/home/random-genres        Random genre shelves for homepage
GET  /api/home/genres               All genres
GET  /api/home/search/suggestions   Search autocomplete
POST /api/home/content/{type}/{id}/view  Track content views
GET  /api/admin/genres/public       All genres (public)
POST /api/reviews                   Submit a review
GET  /api/reviews/movies/{id}       Get reviews for a movie
GET  /api/reviews/series/{id}       Get reviews for a series
GET  /api/upload/images/{cat}/{file} Serve uploaded images
```

### Admin (login required)
```
POST   /api/auth/login              Login and get JWT token
GET    /api/auth/verify             Verify token is valid
POST   /api/auth/change-password    Change admin password
GET    /api/admin/stats             Dashboard statistics
GET    /api/admin/image-health      Check for missing images on disk
GET    /api/admin/url-health        Check download URL health
GET    /api/admin/genres            All genres (admin)
POST   /api/movies                  Create a movie
PUT    /api/movies/{id}             Update a movie
DELETE /api/movies/{id}             Delete a movie
POST   /api/series                  Create a series
PUT    /api/series/{id}             Update a series
DELETE /api/series/{id}             Delete a series
POST   /api/upload/image            Upload an image (poster/backdrop)
```

## How the Frontend Works

Each HTML page loads `app.js` which provides:
1. **API calls** - `api.get('/movies')` fetches from the backend
2. **Card creation** - `createMovieCard(movie)` builds movie/series cards
3. **Navigation** - Menu, search, mobile menu
4. **Hero carousel** - Auto-rotating featured content banner

The homepage (`index.html` + `home.js`) additionally provides:
- Hero banner with featured content
- 🔥 Trending Now shelf
- Random genre shelves with fitting emoji icons
- Search suggestions

## Image Upload System

Images are uploaded via the admin dashboard and stored in `backend/uploads/`:
- **Poster images:** `backend/uploads/poster/`
- **Backdrop images:** `backend/uploads/backdrop/`

When uploading, the filename uses the movie/series title (e.g., `Moana.jpg`) instead of a random hash. If a file with that name already exists, a short random suffix is appended.

The **Image Health** page (`admin/image-health.html`) scans all movies and series to detect any that reference images missing from disk.

## Customization

### Change the accent color
Edit `frontend/css/style.css` and change the `--mz-red` variable:
```css
:root {
  --mz-red: #e50914;  /* Change this to any color */
}
```

### Add new genres
Edit `backend/db/__init__.py` and add new options to the movies list.

### Change sample data
Edit the `_seed_data()` function in `backend/db/__init__.py`.
Delete `backend/db/moviezone.db` and restart to regenerate.

## Git Setup

The project includes a `.gitignore` that excludes:
- Python bytecode (`__pycache__/`, `*.pyc`)
- Temp files (`server.log`, `token.txt`, `headers.txt`)
- IDE settings (`.vscode/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Secrets (`.env`)

The SQLite database (`moviezone.db`) is **not** ignored — it gets committed to GitHub as a backup.

## Testing

Run the API test suite:
```bash
cd backend
python full_test.py
```
This starts the server, runs tests, and verifies everything works.
