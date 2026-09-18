# MOVIE ZONE

A premium movie streaming and discovery website.

## Tech Stack

| Part | Technology | Why |
|------|-----------|-----|
| **Backend** | Python + FastAPI | Fast, modern, easy to understand |
| **Database** | SQLite | No setup needed, stored in one file |
| **Frontend** | HTML + CSS + JavaScript | No frameworks, beginner-friendly |
| **Auth** | JWT + bcrypt | Secure admin login |

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
python main.py
```

### 4. Open in browser
- **Public site:** http://localhost:5500/ (via Live Server) or http://localhost:8000/frontend/ (backend directly)
- **Admin panel:** http://localhost:5500/admin/ (or http://localhost:8000/admin/)
- **API docs:** http://localhost:8000/docs

### 5. Admin login
- Username: `admin`
- Password: `admin123`

## Project Structure

```
MOVIE ZONE/
|
|-- frontend/                    # Public website (HTML + CSS + JS)
|   |-- index.html              # Homepage with hero banner
|   |-- movies.html             # Browse all movies
|   |-- series.html             # Browse all series
|   |-- genres.html             # Browse by genre
|   |-- search.html             # Search movies/series
|   |-- movie-details.html      # Single movie page
|   |-- series-details.html     # Single series page
|   |-- css/
|   |   |-- style.css           # Main styles
|   |   |-- responsive.css      # Mobile/tablet styles
|   |-- js/
|       |-- app.js              # Shared JavaScript code
|
|-- admin/                       # Admin dashboard
|   |-- login.html              # Admin login page
|   |-- dashboard.html          # Stats overview
|   |-- add-content.html        # Add movie or series
|   |-- edit-content.html       # Edit movie or series
|   |-- manage-movies.html      # Manage all movies
|   |-- manage-series.html      # Manage all series
|   |-- css/
|   |   |-- admin.css           # Admin styles
|   |-- js/
|       |-- admin.js            # Admin JavaScript
|
|-- backend/              # Python backend (FastAPI)
    |-- main.py                 # Main server file (START HERE)
    |-- requirements.txt        # Python packages to install
    |-- db/
    |   |-- __init__.py         # Database setup + sample data
    |   |-- moviezone.db        # SQLite database (auto-created)
    |-- models/
    |   |-- __init__.py         # Request body schemas
    |-- routes/
        |-- __init__.py
        |-- auth.py             # Login/authentication
        |-- movies.py           # Movie CRUD operations
        |-- series.py           # Series CRUD operations
        |-- admin.py            # Dashboard stats
```

## How the Backend API Works

The Python backend provides these API endpoints:

### Public (no login required)
```
GET  /api/movies              Get all movies
GET  /api/movies/{id}         Get one movie
GET  /api/series              Get all series
GET  /api/series/{id}         Get one series with seasons/episodes
GET  /api/admin/genres/public Get all genres
```

### Admin (login required)
```
POST /api/auth/login          Login and get token
GET  /api/admin/stats         Dashboard statistics
POST /api/movies              Create a movie
PUT  /api/movies/{id}         Update a movie
DELETE /api/movies/{id}       Delete a movie
POST /api/series              Create a series
PUT  /api/series/{id}         Update a series
DELETE /api/series/{id}       Delete a series
```

## How the Frontend Works

Each HTML page loads `app.js` which provides:
1. **API calls** - `api.get('/movies')` fetches from the backend
2. **Card creation** - `createMovieCard(movie)` builds a movie card
3. **Navigation** - Handles menu, search, mobile menu
4. **Hero carousel** - Auto-rotating featured content banner

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

## Testing

Run the API test suite:
```bash
cd backend
python full_test.py
```
This starts the server, runs 14 tests, and verifies everything works.
