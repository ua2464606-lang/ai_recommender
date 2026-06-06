/**
 * NeuralFind - shared browser utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q');
  if (q && typeof window.quickSearch === 'function') {
    setTimeout(() => window.quickSearch(q), 300);
  }
});

if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, {threshold: 0.1});

  document.querySelectorAll('.stat-card, .how-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    io.observe(el);
  });
}

function animateScoreBars() {
  document.querySelectorAll('.score-bar-fill').forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => {
        bar.style.width = width;
      }, 100);
    });
  });
}

document.addEventListener('resultsRendered', animateScoreBars);

function autoToast(msg, delay = 2500) {
  const toast = document.getElementById('mainToast');
  const body = document.getElementById('toastBody');
  if (!toast || !body) return;

  body.textContent = msg;
  const instance = new bootstrap.Toast(toast, {delay});
  instance.show();
}

document.addEventListener('keydown', (e) => {
  const activeTag = document.activeElement ? document.activeElement.tagName : '';
  if (e.key === '/' && activeTag !== 'INPUT' && activeTag !== 'TEXTAREA') {
    const input = document.getElementById('searchInput');
    if (input) {
      e.preventDefault();
      input.focus();
    }
  }

  if (e.key === 'Escape') {
    const input = document.getElementById('searchInput');
    if (input) input.blur();
  }
});
