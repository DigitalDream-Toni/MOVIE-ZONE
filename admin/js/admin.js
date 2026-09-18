/* ============================================
   MOVIE ZONE - Admin Dashboard JavaScript
   ============================================ */

// Auto-detect backend: if served from Live Server (port 5500),
// point API calls to the FastAPI backend on port 8000.
// If served from FastAPI itself, use relative paths.
const API_BASE = window.location.port === '8000' ? '/api' : 'http://localhost:8000/api';

// Origin of the backend server, used to resolve image URLs.
// The API returns root-relative image paths like /api/upload/images/poster/x.jpg.
// When pages are served from Live Server (port 5500), those must be
// prefixed with the backend origin or the browser 404s them.
const API_ORIGIN = window.location.port === '8000' ? '' : 'http://localhost:8000';

// Convert an image path from the API into a URL the browser can load.
function mediaUrl(path, fallback = 'https://picsum.photos/seed/default/90/130') {
  if (!path) return fallback;
  if (/^(https?:)?\/\//i.test(path) || /^data:/i.test(path)) return path;
  if (/^\//.test(path)) return `${API_ORIGIN}${path}`;
  return path;
}

// --- Auth ---
function getToken() {
  return localStorage.getItem('mz_admin_token');
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

function logout() {
  localStorage.removeItem('mz_admin_token');
  localStorage.removeItem('mz_admin_user');
  window.location.href = 'login.html';
}

// --- API Helper ---
async function adminFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers
  };

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (res.status === 401) {
    logout();
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(err.error || 'Request failed');
  }

  if (res.status === 204) return null;
  return res.json();
}

// --- Sidebar ---
function initSidebar() {
  const toggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  const overlay = document.querySelector('.sidebar-overlay');

  toggle?.addEventListener('click', () => {
    if (!sidebar || !overlay) return;
    const isOpen = sidebar.classList.toggle('open');
    overlay.classList.toggle('active', isOpen);
  });

  overlay?.addEventListener('click', () => {
    if (!sidebar || !overlay) return;
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });

  // Set active link
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav a').forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href');
    if (href && path.includes(href)) {
      link.classList.add('active');
    }
  });

  // Set admin user (value is a plain username string; tolerate stale/odd values)
  const userEl = document.getElementById('admin-username');
  if (userEl) {
    let stored = localStorage.getItem('mz_admin_user') || 'Admin';
    try {
      const parsed = JSON.parse(stored);
      if (parsed && typeof parsed === 'object' && parsed.username) stored = parsed.username;
    } catch { /* plain string - keep it */ }
    userEl.textContent = stored;
  }

  // Close sidebar on resize up to desktop
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (window.innerWidth > 1024) {
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
      }
    }, 80);
  });
}

// --- Toast ---
function showToast(message, type = 'success') {
  const existing = document.querySelector('.admin-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `admin-toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// --- Modal ---
function showConfirmModal(title, message, onConfirm) {
  let overlay = document.querySelector('.admin-modal-overlay');
  if (overlay) overlay.remove();

  overlay = document.createElement('div');
  overlay.className = 'admin-modal-overlay';
  overlay.innerHTML = `
    <div class="admin-modal">
      <h3>${title}</h3>
      <p>${message}</p>
      <div class="modal-actions">
        <button class="btn btn-secondary btn-sm modal-cancel">Cancel</button>
        <button class="btn btn-danger btn-sm modal-confirm">Delete</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('active'));

  overlay.querySelector('.modal-cancel').addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 300);
  });

  overlay.querySelector('.modal-confirm').addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 300);
    onConfirm();
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('active');
      setTimeout(() => overlay.remove(), 300);
    }
  });
}

// --- Utility ---
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

// --- Image Upload ---
async function uploadFile(file, category, name) {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  if (name) formData.append('name', name);

  const res = await fetch(`${API_BASE}/upload/image`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Upload failed' }));
    throw new Error(err.detail || err.error || 'Upload failed');
  }

  return res.json();
}

function initUploadBoxes() {
  document.querySelectorAll('.upload-box').forEach(box => {
    const input = box.querySelector('.upload-input');
    const targetId = box.dataset.target;
    const urlInput = document.getElementById(targetId);
    const category = targetId.includes('poster') ? 'poster' : 'backdrop';
    const preview = box.querySelector('.upload-preview');

    // Click to open file picker
    box.addEventListener('click', (e) => {
      if (e.target === input) return;
      if (e.target.closest('.upload-replace-btn, .upload-clear-btn, .upload-progress')) return;
      input.click();
    });

    // Handle file selection
    input.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const isReplace = box.classList.contains('has-file');
      const prevPreviewHtml = preview.innerHTML;

      // Human-readable name to tag the saved file (e.g. "Moana", "Coyote vs Acme").
      // The form can supply it via data-field on the URL input; if not, fall back to the
      // title field on the same form.
      const fieldName = urlInput && urlInput.dataset.field;
      const formTitle = document.querySelector('#m-title, #s-title, #title, [name=title], [name=Name]');
      const titleName = formTitle && (formTitle.value || formTitle.textContent || '').trim();
      const nameToSend = (fieldName || titleName || '').replace(/[\/:*?"<>|]/g, '');
      const name = nameToSend || undefined;

      // Read the local file first, so the preview + spinner are on screen
      // before the upload starts (and can't race the result handling).
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (ev) => resolve(ev.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      }).catch(() => null);

      if (!dataUrl) {
        showToast('Could not read that file.', 'error');
        input.value = '';
        return;
      }

      preview.innerHTML = `<img src="${dataUrl}" alt="Preview">
        <div class="upload-progress">
          <span class="upload-spinner"></span>
          <span>Uploading ${escapeHtml(file.name)}…</span>
        </div>`;
      box.classList.add('has-file', 'uploading');
      box.classList.remove('upload-error');

      // Upload to server
      try {
        const result = await uploadFile(file, category, name);
        urlInput.value = result.url;
        if (result.name) urlInput.dataset.field = result.name;
        box.classList.remove('uploading');
        finalizeUploadPreview(box);
        showToast(isReplace ? 'Image replaced!' : 'Image uploaded!');
      } catch (err) {
        showToast(err.message || 'Upload failed', 'error');
        box.classList.add('upload-error');
        box.classList.remove('has-file', 'uploading');
        if (isReplace) {
          // Nothing changed server-side — restore the previous image + controls.
          preview.innerHTML = prevPreviewHtml;
          box.classList.add('has-file');
          refreshUploadControls(box);
        } else {
          preview.innerHTML = '';
        }
      } finally {
        box.classList.remove('uploading');
        input.value = '';
      }
    });

    // Drag and drop
    box.addEventListener('dragover', (e) => {
      e.preventDefault();
      box.classList.add('dragover');
    });
    box.addEventListener('dragleave', () => {
      box.classList.remove('dragover');
    });
    box.addEventListener('drop', (e) => {
      e.preventDefault();
      box.classList.remove('dragover');
      if (box.classList.contains('uploading')) return;
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        input.files = e.dataTransfer.files;
        input.dispatchEvent(new Event('change'));
      }
    });

    // If the form loads with an existing stored image (edit mode),
    // render it in the box with replace/clear controls attached.
    if (urlInput && urlInput.value) {
      showExistingImage(box, urlInput.value);
    }
  });
}

// Ensure a .has-file box shows the 'Replace image' + '×' controls.
function refreshUploadControls(box) {
  if (!box.classList.contains('has-file')) return;
  const preview = box.querySelector('.upload-preview');
  if (!preview || preview.querySelector('.upload-controls')) return;
  const wrap = document.createElement('div');
  wrap.className = 'upload-controls';
  wrap.innerHTML = `
    <button type="button" class="btn btn-sm btn-secondary upload-replace-btn">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0115-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 01-15 6.7L3 16"/></svg>
      Replace image
    </button>
    <button type="button" class="upload-clear-btn" title="Remove image" aria-label="Remove image">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  `;
  preview.appendChild(wrap);
  wireUploadControls(box);
}

// After an upload completes, upgrade the plain <img> preview to include controls.
function finalizeUploadPreview(box) {
  const preview = box.querySelector('.upload-preview');
  if (preview) preview.querySelector('.upload-progress')?.remove();
  refreshUploadControls(box);
}

// Show an existing stored image in a box (used by edit-content on load).
function showExistingImage(box, url) {
  const preview = box.querySelector('.upload-preview');
  if (!preview) return;
  preview.innerHTML = `<img src="${mediaUrl(url)}" alt="Current image">`;
  box.classList.add('has-file');
  refreshUploadControls(box);
}

// Re-check every upload box against its URL input — pages that populate
// fields asynchronously (edit-content) call this after data arrives.
window.syncUploadPreviews = function () {
  document.querySelectorAll('.upload-box').forEach(box => {
    const urlInput = document.getElementById(box.dataset.target);
    if (urlInput && urlInput.value && !box.querySelector('.upload-preview img')) {
      showExistingImage(box, urlInput.value);
    }
  });
};

function wireUploadControls(box) {
  const input = box.querySelector('.upload-input');
  const replaceBtn = box.querySelector('.upload-replace-btn');
  const clearBtn = box.querySelector('.upload-clear-btn');
  const urlInput = document.getElementById(box.dataset.target);
  const preview = box.querySelector('.upload-preview');
  if (replaceBtn) {
    replaceBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      input.click();
    });
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      urlInput.value = '';
      preview.innerHTML = '';
      box.classList.remove('has-file', 'uploading', 'upload-error');
      input.value = '';
    });
  }
}

// --- Init on every admin page ---
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initSidebar();
  initUploadBoxes();
});
