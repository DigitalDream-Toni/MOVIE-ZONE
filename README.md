# MOVIE ZONE

A premium movie streaming and discovery website.

## Tech Stack

| Part | Technology | Why |
|------|-----------|-----|
| **Backend** | Python + FastAPI | Fast, modern, easy to understand |
| **Database** | SQLite | No setup needed, stored in one file |
| **Frontend** | HTML + CSS + JavaScript | No frameworks, beginner-friendly |
| **Auth** | JWT + bcrypt | Secure admin login |
| **File uploads** | Multipart + Cloudinary | Images persist on Render (local disk in dev) |

## Quick Start

### 1. Install Python (if not installed)
Download from: https://www.python.org/downloads/

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cd backend
cp .env.example .env   # Edit if needed
```

The default `.env` works out of the box. Change `JWT_SECRET` for production.

### 4. Start the server
```bash
cd backend
python main.py
```

### 5. Open in browser
- **Public site:** http://localhost:8000/frontend/
- **Admin panel:** http://localhost:8000/admin/login.html
- **Admin dashboard:** http://localhost:8000/admin/dashboard.html
- **API docs:** http://localhost:8000/docs

> **Note:** You can also use VS Code Live Server on port 5501 for the frontend, but API calls still go to port 8000.

### 6. Admin login
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
|   |-- main.py              # Main server file (START HERE)
|   |-- .env                 # Environment variables (JWT secret, port)
|   |-- requirements.txt     # Python packages to install
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

Images are uploaded via the admin dashboard and stored by `backend/storage.py`:

- **Production (Render):** stored in **Cloudinary** and the database keeps the full `https://res.cloudinary.com/...` URL. This is required on Render because the server's disk is wiped on every deploy — anything saved locally would vanish and leave broken posters behind.
- **Local development:** stored on disk in `backend/uploads/` (`poster/` and `backdrop/` subfolders), and the database keeps a root-relative path like `/api/upload/images/poster/Moana.jpg`.

The backend picks automatically: **Cloudinary is used when the `CLOUDINARY_URL` environment variable is set**, otherwise local disk. No code changes needed to switch.

When uploading, the filename uses the movie/series title (e.g., `Moana.jpg`) instead of a random hash. If a file with that name already exists, a short random suffix is appended.

The **Image Health** page (`admin/image-health.html`) scans all movies and series to detect any that reference images missing from disk. Cloudinary-hosted images are always considered healthy (they're served by Cloudinary's CDN).

## Deploying to Render

The backend is deployed on Render at `https://movie-zone-qgda.onrender.com` and the frontend on Vercel.

### Required: persistent image storage (Cloudinary)

Render's free tier has an **ephemeral disk** — every deploy wipes uploaded files. To keep posters/backdrops:

1. Create a free account at [cloudinary.com](https://cloudinary.com) and copy the **CLOUDINARY_URL** from the dashboard (looks like `cloudinary://<api_key>:<api_secret>@<cloud_name>`).
2. In the Render dashboard, open your service → **Environment** → add:
   ```
   CLOUDINARY_URL = cloudinary://<api_key>:<api_secret>@<cloud_name>
   ```
3. Redeploy. New uploads go to Cloudinary and survive redeploys.

Also make sure `JWT_SECRET` is set as a Render environment variable (change it from the default).

> **Already have images in `backend/uploads/` from before?** They're gone after the next deploy. Re-upload them from the admin dashboard once `CLOUDINARY_URL` is configured — they'll be stored in Cloudinary permanently.

### Deploy steps

1. Push this repo to GitHub.
2. On Render, create a **Web Service** from the repo:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add the environment variables above (`CLOUDINARY_URL`, `JWT_SECRET`).
4. Point the frontend at the Render URL — `API_URL` in `frontend/js/app.js` and `admin/js/admin.js` (and `admin/login.html`) must match your Render URL.

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
- Root-level `.env` files

The SQLite database (`moviezone.db`) and `backend/.env` are **not** ignored — they get committed to GitHub so the app works out of the box after cloning.

## Testing

Run the API test suite:
```bash
cd backend
python full_test.py
```
This starts the server, runs tests, and verifies everything works.
