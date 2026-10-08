/**
 * Google Developer Groups (GDG) On Campus ENSAF
 * Unified Google Light / Dark Theme Controller
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'gdg_theme';

  function getSystemPreference() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  function getSavedTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {
      // localStorage may be unavailable in private browsing mode
    }
    return getSystemPreference();
  }

  function applyTheme(theme, save = false) {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);

    if (save) {
      try {
        localStorage.setItem(STORAGE_KEY, theme);
      } catch (e) {}
    }

    // Update meta theme-color for mobile browser headers
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.setAttribute('content', theme === 'dark' ? '#131314' : '#bfe4fa');
    }

    updateToggleButtons(theme);

    // Notify components & shaders
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || getSavedTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next, true);
    return next;
  }

  function getSunIcon() {
    return `<svg class="theme-icon sun-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>`;
  }

  function getMoonIcon() {
    return `<svg class="theme-icon moon-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>`;
  }

  function updateToggleButtons(theme) {
    const buttons = document.querySelectorAll('[data-theme-toggle], .theme-toggle-btn');
    buttons.forEach(btn => {
      const isDark = theme === 'dark';
      btn.setAttribute('aria-label', isDark ? 'Switch to Google Light Theme' : 'Switch to Google Dark Theme');
      btn.setAttribute('title', isDark ? 'Switch to Google Light Theme' : 'Switch to Google Dark Theme');
      btn.innerHTML = isDark ? getSunIcon() : getMoonIcon();
      btn.classList.toggle('is-dark', isDark);
    });
  }

  // 1. Immediately apply initial theme before body renders to avoid flashing
  const initialTheme = getSavedTheme();
  applyTheme(initialTheme, false);

  // 2. Wire up UI once DOM is ready
  function initToggleUI() {
    updateToggleButtons(document.documentElement.getAttribute('data-theme') || initialTheme);

    document.addEventListener('click', function(e) {
      const toggleBtn = e.target.closest('[data-theme-toggle], .theme-toggle-btn');
      if (toggleBtn) {
        e.preventDefault();
        toggleTheme();
      }
    });

    // Listen for storage changes across browser tabs
    window.addEventListener('storage', function(e) {
      if (e.key === STORAGE_KEY && (e.newValue === 'dark' || e.newValue === 'light')) {
        applyTheme(e.newValue, false);
      }
    });

    // Listen for OS system theme changes if no explicit user preference was stored
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        try {
          if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light', false);
          }
        } catch (err) {}
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToggleUI);
  } else {
    initToggleUI();
  }

  // Expose public API
  window.gdgTheme = {
    get: function() {
      return document.documentElement.getAttribute('data-theme') || 'light';
    },
    set: function(theme) {
      applyTheme(theme, true);
    },
    toggle: toggleTheme
  };
})();
