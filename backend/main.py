"""
MOVIE ZONE - Main Python Server
================================

This is the MAIN file that starts the website server.
It uses FastAPI (a Python web framework) to handle web requests.

WHAT THIS FILE DOES:
1. Starts the Python web server
2. Connects all the route files (auth, movies, series, admin)
3. Serves the frontend HTML/CSS/JS files
4. Initializes the database with sample data

HOW TO RUN:
    cd backend
    pip install -r requirements.txt
    python main.py

Then open http://localhost:5500 in your browser.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# Import our route files (these handle different parts of the API)
from db import init_db                          # Database setup
from routes.auth import router as auth_router    # Login/authentication routes
from routes.movies import router as movies_router  # Movie CRUD routes
from routes.series import router as series_router  # Series CRUD routes
from routes.admin import router as admin_router    # Dashboard stats routes
from routes.reviews import router as reviews_router  # Reviews & ratings routes
from routes.upload import router as upload_router  # Image upload routes
from routes.home import router as home_router      # Homepage-only public routes

# ============================================
# STEP 1: Initialize the database
# This creates the tables and adds sample movies/series
# ============================================
init_db()

# ============================================
# STEP 2: Create the FastAPI application
# ============================================
app = FastAPI(
    title="MOVIE ZONE API",
    version="1.0.0",
    description="Backend API for MOVIE ZONE movie streaming website"
)

# Allow the frontend to make requests to the backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE
    allow_headers=["*"],        # Allow all headers
)

# ============================================
# STEP 3: Register the API route files
# Each file handles a different part of the API:
#   /api/auth/*     -> Authentication (login, verify token)
#   /api/movies/*   -> Movie management (CRUD)
#   /api/series/*   -> Series management (CRUD)
#   /api/admin/*    -> Dashboard stats, genres
# ============================================
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(series_router)
app.include_router(admin_router)
app.include_router(reviews_router)
app.include_router(upload_router)
app.include_router(home_router)

# ============================================
# STEP 4: Serve static files (HTML, CSS, JS)
# This allows the browser to access the frontend files
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/ folder
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend") # frontend/ folder
ADMIN_DIR = os.path.join(BASE_DIR, "..", "admin")       # admin/ folder

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


# ============================================
# STEP 5: Redirect routes (must be BEFORE static mount)
# ============================================

@app.get("/")
def root():
    """When someone visits the root URL, redirect to the homepage"""
    return RedirectResponse(url="/frontend/index.html")


@app.get("/admin")
@app.get("/admin/")
def admin_redirect():
    """When someone visits /admin, redirect to the login page"""
    return RedirectResponse(url="/admin/login.html")


@app.get("/admin/dashboard")
def admin_dashboard_redirect():
    """When someone visits /admin/dashboard, redirect to the dashboard"""
    return RedirectResponse(url="/admin/dashboard.html")


# Mount admin static files AFTER redirects so login.html etc. still work
app.mount("/admin", StaticFiles(directory=ADMIN_DIR), name="admin")


# ============================================
# STEP 6: Start the server
# ============================================
if __name__ == "__main__":
    import uvicorn
    print("\n  MOVIE ZONE Server starting...")
    print("  Public site: http://localhost:5500 (or the FastAPI origin: port 8000)")
    print("  Admin panel: http://localhost:5500/admin/")
    print("  API docs:    http://localhost:8000/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
