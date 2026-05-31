/* ═══════════════════════════════════════
   ReconHub – Vanilla JavaScript
   ═══════════════════════════════════════ */

(function () {
  'use strict';

  // ── CSRF Helper ──────────────────────────
  function getCSRF() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const cookie = document.cookie.split('; ').find(r => r.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  // ── Toast System ──────────────────────────
  function showToast(message, level) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    const icon = icons[level] || icons.info;
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + level;
    toast.innerHTML = '<i class="fas ' + icon + '"></i><span>' + escapeHtml(message) + '</span><button class="toast-close">&times;</button>';
    container.appendChild(toast);
    toast.querySelector('.toast-close').addEventListener('click', function () { removeToast(toast); });
    setTimeout(function () { removeToast(toast); }, 5000);
  }

  function removeToast(toast) {
    if (toast.classList.contains('removing')) return;
    toast.classList.add('removing');
    setTimeout(function () { toast.remove(); }, 300);
  }

  function escapeHtml(text) {
    var d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  // ── Django Messages → Toasts ──────────────
  function convertDjangoMessages() {
    var container = document.getElementById('django-messages');
    if (!container) return;
    var items = container.querySelectorAll('.toast-data');
    items.forEach(function (el) {
      var level = el.getAttribute('data-level');
      var msg = el.getAttribute('data-message');
      showToast(msg, level);
    });
    container.remove();
  }

  // ── Copy to Clipboard ─────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-copy');
    if (!btn) return;
    var text = btn.getAttribute('data-copy');
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast('Copied to clipboard!', 'success');
      }).catch(function () {
        fallbackCopy(text);
      });
    } else {
      fallbackCopy(text);
    }
  });

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast('Copied to clipboard!', 'success');
    } catch (err) {
      showToast('Failed to copy', 'error');
    }
    document.body.removeChild(ta);
  }

  // ── Favorite Toggle ───────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.favorite-toggle');
    if (!btn) return;
    var targetId = btn.getAttribute('data-target-id');
    if (!targetId) return;
    fetch('/api/targets/' + targetId + '/favorite/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRF(), 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var icon = btn.querySelector('i');
        if (data.favorite) {
          btn.classList.add('active');
          icon.className = 'fas fa-star';
        } else {
          btn.classList.remove('active');
          icon.className = 'far fa-star';
        }
      })
      .catch(function () { showToast('Failed to toggle favorite', 'error'); });
  });

  // ── Save Dork ─────────────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-save-dork');
    if (!btn) return;
    var query = btn.getAttribute('data-query');
    var category = btn.getAttribute('data-category');
    var source = btn.getAttribute('data-source') || 'google';
    if (!query) return;
    fetch('/api/dorking/save/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRF(), 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ query: query, category: category, source: source }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.saved) { showToast('Dork saved!', 'success'); }
        else { showToast('Failed to save dork', 'error'); }
      })
      .catch(function () { showToast('Failed to save dork', 'error'); });
  });

  // ── Open All Links ────────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[id^="btn-open-all-"]');
    if (!btn) return;
    var engine = btn.getAttribute('data-engine');
    var warnLimit = parseInt(btn.getAttribute('data-warn-limit') || '0', 10);
    var links;
    if (engine === 'google') {
      links = document.querySelectorAll('.dork-actions a[href*="google.com"]');
    } else if (engine === 'bing') {
      links = document.querySelectorAll('.dork-actions a[href*="bing.com"]');
    } else if (engine === 'duckduckgo') {
      links = document.querySelectorAll('.dork-actions a[href*="duckduckgo.com"]');
    } else {
      links = document.querySelectorAll('.engine-card');
    }
    var count = links.length;
    if (warnLimit > 0 && count > warnLimit) {
      if (!confirm('This will open ' + count + ' tabs. Continue?')) return;
    }
    links.forEach(function (link) {
      var href = link.getAttribute('href') || link.getAttribute('data-url');
      if (href) { window.open(href, '_blank'); }
    });
  });

  // ── Open All Engines ──────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('#btn-open-all-engines');
    if (!btn) return;
    var cards = document.querySelectorAll('.engine-card');
    if (cards.length > 12) {
      if (!confirm('This will open ' + cards.length + ' tabs. Continue?')) return;
    }
    cards.forEach(function (card) {
      var href = card.getAttribute('href');
      if (href) window.open(href, '_blank');
    });
  });

  // ── Sidebar Toggle ────────────────────────
  var sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function () {
      document.getElementById('sidebar').classList.toggle('open');
    });
  }

  // ── Keyboard Shortcuts ────────────────────
  var searchInput = document.getElementById('global-search-input');
  document.addEventListener('keydown', function (e) {
    // / to focus search
    if (e.key === '/' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && !e.target.isContentEditable) {
      e.preventDefault();
      if (searchInput) searchInput.focus();
    }
    // ? to show shortcuts
    if (e.key === '?' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      showToast('Shortcuts: / Search, g+d Dashboard, g+t Targets, g+s Subdomains, g+w Wayback, g+r Reports', 'info');
    }
    // g then key navigation
    if (e.key === 'g' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      document._gPressed = true;
      setTimeout(function () { document._gPressed = false; }, 800);
      return;
    }
    if (document._gPressed) {
      document._gPressed = false;
      var map = { d: '/api/dashboard/', t: '/api/targets/', s: '/api/recon/subdomains/', w: '/api/recon/wayback/', r: '/api/reporting/' };
      var url = map[e.key];
      if (url) { window.location.href = url; }
    }
  });

  // ── Wayback Client Filter ─────────────────
  window.filterWayback = function (val) {
    var tbody = document.getElementById('wayback-tbody');
    if (!tbody) return;
    var rows = tbody.querySelectorAll('.wayback-row');
    var q = val.toLowerCase();
    rows.forEach(function (row) {
      var text = row.textContent.toLowerCase();
      row.style.display = text.indexOf(q) > -1 ? '' : 'none';
    });
  };

  // ── Loader Bar ────────────────────────────
  var loaderBar = document.getElementById('loader-bar');
  document.addEventListener('DOMContentLoaded', function () {
    // Show loader on form submissions
    document.addEventListener('submit', function (e) {
      if (e.target.closest('form') && !e.target.closest('.inline-form')) {
        if (loaderBar) loaderBar.classList.add('active');
      }
    });
    // Hide loader when page loads
    if (loaderBar) loaderBar.classList.remove('active');
  });
  window.addEventListener('beforeunload', function () {
    if (loaderBar) loaderBar.classList.add('active');
  });

  // ── Init ──────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    convertDjangoMessages();
    // Focus search on / shortcut hint click
  });

})();
