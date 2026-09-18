/*
 * ============================================
 * MOVIE ZONE - Main JavaScript (Frontend)
 * ============================================
 *
 * This file contains ALL the shared JavaScript code used across the
 * public-facing pages of the website. It handles:
 *
 * 1. Making API calls to the Python backend
 * 2. Navigation bar behavior
 * 3. Creating movie/series cards
 * 4. Hero banner carousel
 * 5. Horizontal scrolling rows
 * 6. Toast notifications
 * 7. Modal dialogs
 * 8. Utility functions
 *
 * HOW IT WORKS:
 * - The Python/FastAPI backend runs at the same address as this site
 * - We use the Fetch API (built into browsers) to call the backend
 * - The backend returns JSON data that we use to build the page
 * - No React, Vue, or any framework - just plain JavaScript!
 */

// ============================================
// STEP 1: API HELPER
// This object makes it easy to talk to the Python backend.
// Example: api.get('/movies') fetches all movies from the server.
// ============================================

// Auto-detect backend: if served from Live Server (port 5500),
// point API calls to the FastAPI backend on port 8000.
// If served from FastAPI itself, use relative paths.
const API_BASE = window.location.port === '8000' ? '/api' : 'http://localhost:8000/api';

// Origin of the backend server, used to resolve image URLs.
// The API returns root-relative image paths like /api/upload/images/poster/x.jpg.
// When the site is served from Live Server (e.g. port 5501), those must be
// prefixed with the backend origin or the browser 404s them.
const API_ORIGIN = window.location.port === '8000' ? '' : 'http://localhost:8000';

// Convert an image path from the API into a URL the browser can load.
// - Absolute URLs (http://...) and data: URIs pass through untouched
// - Root-relative paths (/api/upload/...) get the backend origin prepended
// - Empty/missing values fall back to a placeholder image
function mediaUrl(path, fallback = 'https://picsum.photos/seed/default/400/600') {
  if (!path) return fallback;
  if (/^(https?:)?\/\//i.test(path) || /^data:/i.test(path)) return path;
  if (/^\//.test(path)) return `${API_ORIGIN}${path}`;
  return path;
}

const api = {
  // GET request - used to fetch data (movies, series, etc.)
  async get(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();  // Convert response to JavaScript object
  },

  // POST request - used to create new data
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)  // Convert JavaScript object to JSON string
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API Error');
    }
    return response.json();
  }
};

// ============================================
// STEP 2: NAVIGATION
// Handles the top navigation bar, mobile menu, and search.
// ============================================

function initNavigation() {
  // Find elements on the page
  const nav = document.querySelector('.mz-nav');                    // Top nav bar
  const menuToggle = document.querySelector('.mz-menu-toggle');    // Hamburger button
  const mobileNav = document.querySelector('.mz-mobile-nav');       // Mobile menu
  const searchToggle = document.querySelector('.search-toggle');    // Search icon
  const navSearch = document.querySelector('.mz-nav-search');       // Search container
  const searchInput = navSearch?.querySelector('input');            // Search text box

  // When user scrolls down, fade out nav. When scrolling up, show it.
  let lastScrollY = 0;
  let ticking = false;

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const currentScrollY = window.scrollY;
        if (currentScrollY > lastScrollY && currentScrollY > 80) {
          // Scrolling DOWN past 80px — hide nav
          nav.classList.add('nav-hidden');
        } else {
          // Scrolling UP — show nav
          nav.classList.remove('nav-hidden');
        }
        // Always darken when scrolled
        nav.classList.toggle('scrolled', currentScrollY > 50);
        lastScrollY = currentScrollY;
        ticking = false;
      });
      ticking = true;
    }
  });

  // When hamburger button is clicked, open/close mobile menu
  menuToggle?.addEventListener('click', () => {
    menuToggle.classList.toggle('active');       // Animate hamburger to X
    mobileNav?.classList.toggle('active');       // Show/hide mobile menu
    // Prevent background scrolling when menu is open
    document.body.style.overflow = mobileNav?.classList.contains('active') ? 'hidden' : '';
  });

  // When a link in mobile menu is clicked, close the menu
  mobileNav?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menuToggle?.classList.remove('active');
      mobileNav?.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // Toggle search box open/close
  searchToggle?.addEventListener('click', () => {
    navSearch?.classList.toggle('active');
    if (navSearch?.classList.contains('active')) {
      searchInput?.focus();  // Put cursor in search box
    }
  });

  // When user presses Enter in search, go to search page
  searchInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && searchInput.value.trim()) {
      window.location.href = `search.html?q=${encodeURIComponent(searchInput.value.trim())}`;
    }
  });

  // Highlight the current page in the nav
  setActiveNavLink();
}

// Highlights which page we're currently on
function setActiveNavLink() {
  const path = window.location.pathname;
  document.querySelectorAll('.mz-nav-links a, .mz-mobile-nav a').forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href');
    if (href && path.includes(href.replace('.html', '')) && href !== 'index.html') {
      link.classList.add('active');
    } else if (path.endsWith('/') || path.endsWith('index.html') || path.endsWith('frontend/')) {
      if (href === 'index.html') link.classList.add('active');
    }
  });
}

// ============================================
// STEP 3: MOVIE CARD CREATION
// Each movie on the site is displayed as a "card" with a poster image.
// This function builds the HTML for one card.
// ============================================

function createMovieCard(movie) {
  // Create a div element to hold the card
  const card = document.createElement('div');
  card.className = 'mz-card';

  // When user clicks the card, go to movie details page
  card.onclick = () => {
    window.location.href = `movie-details.html?id=${movie.id}`;
  };

  // Build the card HTML using a template string (backticks)
  // ${movie.title} puts the movie's title into the HTML
  // The || means "or" - if poster is missing, use a default image
  card.innerHTML = `
    <div class="mz-card-poster">
      ${movie.is_featured ? '<span class="mz-card-badge">Featured</span>' : ''}
      <img src="${escapeHtml(mediaUrl(movie.poster))}"
           alt="${escapeHtml(movie.title)}"
           loading="lazy"
           onerror="this.src='https://picsum.photos/seed/default/400/600'">
      <div class="mz-card-overlay">
        <div class="mz-card-actions">
          ${movie.watch_url ? `<button title="Watch" onclick="event.stopPropagation(); window.open('${movie.watch_url}', '_blank')">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </button>` : ''}
          ${movie.download_url ? `<button title="Download" onclick="event.stopPropagation(); window.open('${movie.download_url}', '_blank')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
          </button>` : ''}
        </div>
      </div>
    </div>
    <div class="mz-card-info">
      <div class="mz-card-title">${escapeHtml(movie.title)}</div>
      <div class="mz-card-meta">
        <span>${movie.year || ''}</span>
        <span>${escapeHtml(movie.genre || '')}</span>
      </div>
    </div>
  `;
  return card;
}

// ============================================
// STEP 4: SERIES CARD CREATION
// Similar to movie cards but for TV series.
// ============================================

function createSeriesCard(series) {
  const card = document.createElement('div');
  card.className = 'mz-card';

  // Click to go to series details page
  card.onclick = () => {
    window.location.href = `series-details.html?id=${series.id}`;
  };

  // Count seasons and episodes
  const seasonCount = series.season_count || series.seasons?.length || 0;

  card.innerHTML = `
    <div class="mz-card-poster">
      <img src="${escapeHtml(mediaUrl(series.poster))}"
           alt="${escapeHtml(series.title)}"
           loading="lazy"
           onerror="this.src='https://picsum.photos/seed/default/400/600'">
      <div class="mz-card-overlay">
        <div class="mz-card-actions">
          <button title="View Series" onclick="event.stopPropagation(); window.location.href='series-details.html?id=${series.id}'">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </button>
        </div>
      </div>
    </div>
    <div class="mz-card-info">
      <div class="mz-card-title">${escapeHtml(series.title)}</div>
      <div class="mz-card-meta">
        <span>${series.year || ''}</span>
        <span>${seasonCount} Season${seasonCount !== 1 ? 's' : ''}</span>
      </div>
    </div>
  `;
  return card;
}

// ============================================
// STEP 5: HORIZONTAL SCROLL ROWS
// Movie rows scroll left/right. This sets up the arrow buttons.
// ============================================

function initRowScroll(rowEl) {
  if (!rowEl) return;

  // Find the scroll container and arrow buttons inside this row
  const scrollContainer = rowEl.querySelector('.mz-row-scroll');
  const leftBtn = rowEl.querySelector('.mz-row-btn-left');
  const rightBtn = rowEl.querySelector('.mz-row-btn-right');
  const scrollAmount = 400;  // How many pixels to scroll at a time

  // Left arrow - scroll left
  leftBtn?.addEventListener('click', () => {
    scrollContainer?.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  });

  // Right arrow - scroll right
  rightBtn?.addEventListener('click', () => {
    scrollContainer?.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  });
}

// ============================================
// STEP 6: HERO CAROUSEL
// The big banner at the top of the homepage.
// Shows featured movies and auto-switches every 7 seconds.
// ============================================

let currentHeroSlide = 0;
let heroInterval = null;

function initHeroCarousel(slides) {
  if (!slides || slides.length === 0) return;

  const container = document.getElementById('hero-slides');
  if (!container) return;

  // Build HTML for each slide
  container.innerHTML = slides.map((slide, i) => `
    <div class="mz-hero-slide ${i === 0 ? 'active' : ''}">
      <div class="mz-hero-backdrop" style="background-image: url('${mediaUrl(slide.backdrop || slide.poster)}')"></div>
      <div class="mz-hero-content">
        <span class="mz-hero-badge">${slide.type === 'series' ? 'Series' : 'Featured'}</span>
        <h1 class="mz-hero-title">${escapeHtml(slide.title)}</h1>
        <div class="mz-hero-meta">
          <span class="year">${slide.year}</span>
          <span class="dot"></span>
          <span class="genre">${escapeHtml(slide.genre)}</span>
          ${slide.type === 'series' ? `<span class="dot"></span><span>${slide.season_count || 0} Season${(slide.season_count || 0) !== 1 ? 's' : ''}</span>` : ''}
        </div>
        <p class="mz-hero-desc">${escapeHtml(slide.description || '')}</p>
        <div class="mz-hero-actions">
          <a href="${slide.type === 'series' ? 'series-details.html' : 'movie-details.html'}?id=${slide.id}" class="mz-btn mz-btn-primary">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M8 5v14l11-7z"/></svg>
            View Details
          </a>
          ${slide.download_url ? `<a href="${slide.download_url}" target="_blank" class="mz-btn mz-btn-secondary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            Download
          </a>` : ''}
        </div>
      </div>
    </div>
  `).join('');

  // Auto-advance to next slide every 7 seconds
  heroInterval = setInterval(() => {
    const slides = container.querySelectorAll('.mz-hero-slide');
    slides[currentHeroSlide].classList.remove('active');  // Hide current slide
    currentHeroSlide = (currentHeroSlide + 1) % slides.length;  // Go to next
    slides[currentHeroSlide].classList.add('active');  // Show next slide
  }, 7000);
}

// ============================================
// STEP 7: TOAST NOTIFICATIONS
// Small popup messages that appear at the bottom of the screen.
// ============================================

function showToast(message, type = 'success') {
  // Remove any existing toast
  const existing = document.querySelector('.mz-toast');
  if (existing) existing.remove();

  // Create new toast
  const toast = document.createElement('div');
  toast.className = `mz-toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => toast.classList.add('show'));

  // Remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================
// STEP 8: MODAL DIALOG
// A popup box that appears in the center of the screen.
// Used for "Are you sure?" confirmations.
// ============================================

function showModal(title, body, onConfirm, onCancel) {
  // Remove any existing modal
  let overlay = document.querySelector('.mz-modal-overlay');
  if (overlay) overlay.remove();

  // Create modal HTML
  overlay = document.createElement('div');
  overlay.className = 'mz-modal-overlay';
  overlay.innerHTML = `
    <div class="mz-modal">
      <h3 class="mz-modal-title">${title}</h3>
      <p class="mz-modal-body">${body}</p>
      <div class="mz-modal-actions">
        <button class="mz-btn mz-btn-outline mz-btn-sm modal-cancel">Cancel</button>
        <button class="mz-btn mz-btn-primary mz-btn-sm modal-confirm">Delete</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('active'));

  // Cancel button
  overlay.querySelector('.modal-cancel').addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 300);
    onCancel?.();
  });

  // Confirm button
  overlay.querySelector('.modal-confirm').addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 300);
    onConfirm?.();
  });

  // Click outside to cancel
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('active');
      setTimeout(() => overlay.remove(), 300);
      onCancel?.();
    }
  });
}

// ============================================
// STEP 9: UTILITY FUNCTIONS
// Small helper functions used throughout the app.
// ============================================

// Prevents HTML injection attacks by escaping special characters
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Gets a value from the URL query string
// Example: search.html?q=horror  ->  getQueryParam('q') returns 'horror'
function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

// Converts a date string to a readable format
// Example: "2024-01-15T10:30:00" -> "Jan 15, 2024"
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ============================================
// SHARED FOOTER
// Every public page has <footer id="mz-footer-root"></footer>
// and this fills it in - one source of truth instead of
// seven copies of the same markup drifting apart.
// ============================================

function renderFooter() {
  const root = document.getElementById('mz-footer-root');
  if (!root) return;
  const year = new Date().getFullYear();
  root.className = 'mz-footer';
  root.innerHTML = `
    <div class="mz-footer-inner">
      <div class="mz-footer-brand">
        <div class="footer-logo">MOVIE ZONE</div>
        <p>Your premium destination for movies and series. Discover, explore, and enjoy entertainment without boundaries.</p>
      </div>
      <div class="mz-footer-links">
        <div class="mz-footer-col">
          <h4>Browse</h4>
          <a href="index.html">Home</a>
          <a href="movies.html">Movies</a>
          <a href="series.html">Series</a>
          <a href="genres.html">Genres</a>
          <a href="search.html">Search</a>
        </div>
        <div class="mz-footer-col">
          <h4>Popular Genres</h4>
          <a href="genres.html?genre=Action">Action</a>
          <a href="genres.html?genre=Drama">Drama</a>
          <a href="genres.html?genre=Comedy">Comedy</a>
          <a href="genres.html?genre=Sci-Fi">Sci-Fi</a>
        </div>
      </div>
    </div>
    <div class="mz-footer-bottom">
      &copy; ${year} MOVIE ZONE. All rights reserved.
    </div>
  `;
}

// ============================================
// STEP 10: INITIALIZE
// This runs when the page finishes loading.
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();  // Set up the nav bar
  renderFooter();    // Fill in the shared footer
});
