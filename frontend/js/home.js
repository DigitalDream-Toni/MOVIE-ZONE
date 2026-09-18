/*
 * MOVIE ZONE - Homepage behavior
 *
 * This module is only used on the homepage.
 * It coordinates the featured hero, the trending / new arrivals /
 * recently added rows, and the homepage search autocomplete with
 * recent searches stored in localStorage.
 */

const HOME = (() => {
  const STORAGE_RECENT = 'mz_home_recent_searches';
  const STORAGE_FAVS = 'mz_home_favorites';

  function getRecentSearches() {
    try {
      const raw = localStorage.getItem(STORAGE_RECENT);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function setRecentSearches(list) {
    try {
      localStorage.setItem(STORAGE_RECENT, JSON.stringify(list));
    } catch {
      // ignore storage errors
    }
  }

  function addRecentSearch(query) {
    if (!query) return;
    const normalized = query.trim();
    if (!normalized) return;
    let list = getRecentSearches().filter((s) => s.toLowerCase() !== normalized.toLowerCase());
    list.unshift(normalized);
    if (list.length > 8) list = list.slice(0, 8);
    setRecentSearches(list);
  }

  function getFavorites() {
    try {
      const raw = localStorage.getItem(STORAGE_FAVS);
      return new Set(raw ? JSON.parse(raw) : []);
    } catch {
      return new Set();
    }
  }

  function saveFavorites(set) {
    try {
      localStorage.setItem(STORAGE_FAVS, JSON.stringify(Array.from(set)));
    } catch {
      // ignore
    }
  }

  function recordView(contentType, id) {
    if (!id || !contentType) return;
    fetch(`${API_BASE}/home/content/${contentType}/${id}/view`, {
      method: 'POST',
    }).catch(() => {
      // view tracking is best-effort; never break the UI
    });
  }

  function isFavorite(id) {
    return getFavorites().has(id);
  }

  function toggleFavorite(id, cardEl) {
    const set = getFavorites();
    let message;
    if (set.has(id)) {
      set.delete(id);
      message = 'Removed from favorites';
    } else {
      set.add(id);
      message = 'Added to favorites';
    }
    saveFavorites(set);
    showToast(message, set.has(id) ? 'success' : 'success');
    renderCardFavoriteState(id, cardEl);
  }

  function renderCardFavoriteState(id, cardEl) {
    if (!cardEl) return;
    const btn = cardEl.querySelector('[data-fav]');
    if (!btn) return;
    const favorited = getFavorites().has(id);
    btn.dataset.fav = favorited ? 'true' : 'false';
    btn.title = favorited ? 'Remove from favorites' : 'Add to favorites';
    btn.innerHTML = favorited
      ? '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>';
    btn.classList.toggle('mz-card-fav-active', favorited);
  }

  function createCard(content) {
    const el = document.createElement('div');
    el.className = 'mz-card';

    const id = content.id || '';
    const type = content.type || (content.movie_type === 'movie' ? 'movie' : 'series');
    const poster = mediaUrl(content.poster);
    const title = content.title || 'Untitled';
    const year = content.year || '';
    const genre = content.genre || '';
    const isFeatured = !!content.is_featured;

    let actionsHtml = '';
    let clickAction = '';

    if (type === 'movie') {
      const watch = content.watch_url || null;
      const download = content.download_url || null;
      const detailUrl = `movie-details.html?id=${id}`;

      actionsHtml = `
        <button type="button" data-fav="false" title="Add to favorites" onclick="event.stopPropagation(); HOME.toggleFavorite('${escapeHtml(id)}', this.closest('.mz-card'))">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
        </button>
        ${watch ? `<button type="button" title="Watch" onclick="event.stopPropagation(); window.open('${escapeHtml(watch)}', '_blank')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        </button>` : ''}
        ${download ? `<button type="button" title="Download" onclick="event.stopPropagation(); window.open('${escapeHtml(download)}', '_blank')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        </button>` : ''}
      `;

      clickAction = `window.location.href='${detailUrl}'`;
    } else {
      const watch = content.watch_url || null;
      const download = content.download_url || null;
      const detailUrl = `series-details.html?id=${id}`;

      actionsHtml = `
        <button type="button" data-fav="false" title="Add to favorites" onclick="event.stopPropagation(); HOME.toggleFavorite('${escapeHtml(id)}', this.closest('.mz-card'))">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
        </button>
        <button type="button" title="View series" onclick="event.stopPropagation(); window.location.href='${detailUrl}'">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        </button>
      `;

      clickAction = `window.location.href='${detailUrl}'`;
    }

    el.innerHTML = `
      <div class="mz-card-poster">
        ${isFeatured ? '<span class="mz-card-badge">Featured</span>' : ''}
        <img src="${escapeHtml(poster)}" alt="${escapeHtml(title)}" loading="lazy" onerror="this.src='https://picsum.photos/seed/default/400/600'">
        <div class="mz-card-overlay">
          <div class="mz-card-actions">
            ${actionsHtml}
          </div>
        </div>
      </div>
      <div class="mz-card-info">
        <div class="mz-card-title">${escapeHtml(title)}</div>
        <div class="mz-card-meta">
          ${year ? `<span>${escapeHtml(String(year))}</span>` : ''}
          ${genre ? `<span class="mz-card-genre">${escapeHtml(genre)}</span>` : ''}
        </div>
      </div>
    `;

    el.addEventListener('click', () => {
      recordView(type, id);
      // eslint-disable-next-line no-new-func
      new Function(clickAction)();
    });

    return el;
  }

  async function refreshHomeData() {
    let featured = { items: [] };
    let newArrivals = { items: [] };
    let genreShelves = { shelves: [] };

    try {
      const results = await Promise.all([
        api.get('/home/featured?limit=10'),
        api.get('/home/new-arrivals?limit=12'),
        api.get('/home/random-genres?count=3'),
      ]);
      featured = results[0] || featured;
      newArrivals = results[1] || newArrivals;
      genreShelves = results[2] || genreShelves;
      hideOfflineBanner();
    } catch (err) {
      console.warn('Homepage data fetch failed, rendering with empty state:', err);
      showOfflineBanner();
    }

    try {
      initHeroCarousel(featured.items || []);
    } catch (err) {
      console.warn('Hero init failed:', err);
    }

    try {
      renderHomepageRow('scroll-trending', trendingItems(featured.items || [], newArrivals.items || []));
      renderGenreShelves(genreShelves.shelves || []);
    } catch (err) {
      console.warn('Homepage render failed:', err);
    }
  }

  function trendingItems(featured, newArrivals) {
    if (featured.length) return featured;
    return newArrivals.slice(0, 10);
  }

  function renderHomepageRow(scrollId, items) {
    const scroll = document.getElementById(scrollId);
    if (!scroll) return;
    scroll.innerHTML = '';
    items.forEach((it) => scroll.appendChild(createCard(it)));
    const rowEl = document.getElementById(scrollId)?.closest('.mz-row');
    if (rowEl) initRowScroll(rowEl);
  }

  // Fitting emoji per genre for shelf titles; 🎬 is the fallback.
  // Keys are matched case-insensitively; substrings let variants like
  // 'Sci-Fi Thriller' still resolve.
  const GENRE_EMOJI = {
    action: '💥',
    adventure: '🧭',
    anime: '🌀',
    comedy: '😂',
    crime: '🕵️',
    drama: '🎭',
    horror: '🔥',
    romance: '💕',
    'sci-fi': '🚀',
    scifi: '🚀',
    thriller: '🔪',
    mystery: '🔍',
    fantasy: '🐉',
    animation: '🎨',
    documentary: '🎥',
    family: '👨‍👩‍👧‍👦',
    nigerian: '🇳🇬',
    music: '🎵',
    sport: '🏆',
    war: '🎖️',
    western: '🤠',
  };

  function genreEmoji(genre) {
    const key = String(genre || '').toLowerCase();
    if (GENRE_EMOJI[key]) return GENRE_EMOJI[key];
    // Try substring match for compound genres like 'Sci-Fi Thriller'
    const hit = Object.keys(GENRE_EMOJI).find((k) => key.includes(k));
    return hit ? GENRE_EMOJI[hit] : '🎬';
  }

  // Build one shelf (title row + scrollable cards) inside #genre-shelves
  function renderGenreShelves(shelves) {
    const container = document.getElementById('genre-shelves');
    if (!container) return;
    container.innerHTML = '';

    shelves.forEach((shelf, i) => {
      if (!shelf.items || !shelf.items.length) return;

      const section = document.createElement('section');
      section.className = 'mz-section';
      section.innerHTML = `
        <div class="mz-section-inner">
          <div class="mz-row" id="row-genre-${i}">
            <div class="mz-section-header">
              <h2 class="mz-section-title">${genreEmoji(shelf.genre)} ${escapeHtml(shelf.genre)}</h2>
              <a href="genres.html?genre=${encodeURIComponent(shelf.genre)}" class="mz-section-link">
                View All
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 18l6-6-6-6"/></svg>
              </a>
            </div>
            <div class="mz-row-scroll" id="scroll-genre-${i}"></div>
            <button class="mz-row-btn mz-row-btn-left" aria-label="Scroll left">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <button class="mz-row-btn mz-row-btn-right" aria-label="Scroll right">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      `;
      container.appendChild(section);

      const scroll = section.querySelector('.mz-row-scroll');
      shelf.items.forEach((it) => scroll.appendChild(createCard(it)));
      initRowScroll(section.querySelector('.mz-row'));
    });
  }

  // ============================================
  // BACKEND OFFLINE BANNER
  // If the API is unreachable (Python server not
  // running), show a friendly banner with a retry
  // button instead of silent empty rows.
  // ============================================

  function showOfflineBanner() {
    let banner = document.getElementById('mz-offline-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'mz-offline-banner';
      banner.className = 'mz-offline-banner';
      banner.setAttribute('role', 'alert');
      banner.innerHTML = `
        <div class="mz-offline-banner-inner">
          <div class="mz-offline-banner-text">
            <strong>Can't reach the movie server.</strong>
            <span>New releases and recommendations aren't available right now.</span>
          </div>
          <button type="button" class="mz-offline-retry">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
            Try again
          </button>
        </div>
      `;
      banner.querySelector('.mz-offline-retry').addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        btn.disabled = true;
        btn.classList.add('retrying');
        try {
          await refreshHomeData();
        } finally {
          btn.disabled = false;
          btn.classList.remove('retrying');
        }
      });
      const hero = document.querySelector('.mz-hero');
      hero?.parentNode.insertBefore(banner, hero.nextSibling);
    }
    banner.classList.add('active');
    document.body.classList.add('mz-backend-offline');
  }

  function hideOfflineBanner() {
    document.getElementById('mz-offline-banner')?.classList.remove('active');
    document.body.classList.remove('mz-backend-offline');
  }

  async function loadHomepage() {
    try {
      await refreshHomeData();

      // Homepage search autocomplete
      const searchInput = document.querySelector('.mz-nav-search input');
      if (searchInput) {
        searchInput.addEventListener('input', onSearchInput);
        searchInput.addEventListener('focus', onSearchFocus);
        searchInput.addEventListener('blur', onSearchBlur);
        searchInput.addEventListener('keydown', onSearchKeydown);
        renderRecentSearches(searchInput);
      }
    } catch (err) {
      console.error('loadHomepage failed:', err);
    }
  }

  let searchSuggestionsEl = null;
  let searchSuggestionsTimeout = null;

  function onSearchInput(e) {
    const value = e.target.value.trim();
    clearTimeout(searchSuggestionsTimeout);

    if (value.length >= 2) {
      searchSuggestionsTimeout = setTimeout(() => fetchSuggestions(value), 180);
    } else {
      hideSuggestions();
    }
  }

  function onSearchFocus() {
    const recent = getRecentSearches();
    if (recent.length && !document.activeElement?.matches('.mz-nav-search input')) {
      renderRecentSearches(document.querySelector('.mz-nav-search input'));
    }
  }

  function onSearchBlur() {
    setTimeout(hideSuggestions, 180);
  }

  function onSearchKeydown(e) {
    if (e.key === 'Enter') {
      const value = e.target.value.trim();
      if (value) {
        addRecentSearch(value);
        window.location.href = `search.html?q=${encodeURIComponent(value)}`;
      }
    }
    if (e.key === 'Escape') {
      hideSuggestions();
      e.target.blur();
    }
  }

  async function fetchSuggestions(query) {
    try {
      const data = await api.get(`/home/search/suggestions?q=${encodeURIComponent(query)}&limit=8`);
      showSuggestions(data.suggestions || [], data.genres || [], query);
    } catch {
      hideSuggestions();
    }
  }

  function showSuggestions(suggestions, genres, query) {
    const input = document.querySelector('.mz-nav-search input');
    if (!input) return;

    let wrap = document.querySelector('.mz-search-suggestions');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.className = 'mz-search-suggestions';
      document.body.appendChild(wrap);
    }

    wrap.innerHTML = '';

    if (suggestions.length) {
      const section = document.createElement('div');
      section.className = 'mz-search-suggestions-section';
      section.innerHTML = `<div class="mz-search-suggestions-label">Results</div>`;
      suggestions.slice(0, 6).forEach((s) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'mz-search-suggestion';
        const typeLabel = s.type === 'series' ? 'Series' : 'Movie';
        item.innerHTML = `
          <span class="mz-search-suggestion-title">${escapeHtml(s.title || 'Untitled')}</span>
          <span class="mz-search-suggestion-meta">
            ${s.year ? escapeHtml(String(s.year)) : ''}
            ${s.genre ? `<span class="mz-search-suggestion-dot"></span>${escapeHtml(s.genre)}` : ''}
            <span class="mz-search-suggestion-dot"></span>${typeLabel}
          </span>
        `;
        item.addEventListener('click', () => {
          addRecentSearch(query);
          window.location.href = s.type === 'series'
            ? `series-details.html?id=${s.id}`
            : `movie-details.html?id=${s.id}`;
        });
        section.appendChild(item);
      });
      wrap.appendChild(section);
    }

    if (genres.length && query.length >= 2) {
      const section = document.createElement('div');
      section.className = 'mz-search-suggestions-section';
      section.innerHTML = `<div class="mz-search-suggestions-label">Genres</div>`;
      genres.slice(0, 5).forEach((g) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'mz-search-suggestion mz-search-suggestion-genre';
        item.textContent = g;
        item.addEventListener('click', () => {
          addRecentSearch(query);
          window.location.href = `genres.html?genre=${encodeURIComponent(g)}`;
        });
        section.appendChild(item);
      });
      wrap.appendChild(section);
    }

    positionSuggestions(input, wrap);
    wrap.classList.add('active');
    searchSuggestionsEl = wrap;
  }

  function positionSuggestions(input, wrap) {
    const rect = input.getBoundingClientRect();
    wrap.style.left = `${Math.min(rect.left, window.innerWidth - 320)}px`;
    wrap.style.top = `${rect.bottom + 6}px`;
    wrap.style.width = `${Math.min(rect.width, 320)}px`;
  }

  function hideSuggestions() {
    const wrap = document.querySelector('.mz-search-suggestions');
    if (wrap) wrap.classList.remove('active');
    searchSuggestionsEl = null;
  }

  function renderRecentSearches(input) {
    const recent = getRecentSearches();
    const wrap = document.querySelector('.mz-search-suggestions');
    if (!wrap) return;

    wrap.innerHTML = '';
    if (!recent.length) return;

    const section = document.createElement('div');
    section.className = 'mz-search-suggestions-section';
    section.innerHTML = `<div class="mz-search-suggestions-label">Recent</div>`;
    recent.forEach((term) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'mz-search-suggestion';
      item.textContent = term;
      item.addEventListener('click', () => {
        addRecentSearch(term);
        window.location.href = `search.html?q=${encodeURIComponent(term)}`;
      });
      section.appendChild(item);
    });
    wrap.appendChild(section);

    positionSuggestions(input, wrap);
    wrap.classList.add('active');
    searchSuggestionsEl = wrap;
  }

  return {
    toggleFavorite,
    loadHomepage,
    refreshHomeData,
  };
})();

window.HOME = HOME;
