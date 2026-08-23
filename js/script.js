(() => {
  'use strict';

  // Footer year
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Header scroll state
  const header = document.getElementById('siteHeader');
  const onScroll = () => {
    if (window.scrollY > 24) header.classList.add('scrolled');
    else header.classList.remove('scrolled');
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile nav toggle
  const navToggle = document.getElementById('navToggle');
  const mainNav = document.getElementById('mainNav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', () => {
      const open = mainNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(open));
    });
    mainNav.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        mainNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Price breakdown toggles
  document.querySelectorAll('.price-toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.toggle);
      if (!target) return;
      const open = target.classList.toggle('open');
      btn.textContent = open ? 'Hide pricing by vehicle' : 'See pricing by vehicle';
    });
  });

  // FAQ accordion
  document.querySelectorAll('.faq-item').forEach((item) => {
    const q = item.querySelector('.faq-q');
    const a = item.querySelector('.faq-a');
    q.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');

      // close others
      document.querySelectorAll('.faq-item.open').forEach((other) => {
        if (other !== item) {
          other.classList.remove('open');
          other.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
          other.querySelector('.faq-a').style.maxHeight = null;
        }
      });

      if (isOpen) {
        item.classList.remove('open');
        q.setAttribute('aria-expanded', 'false');
        a.style.maxHeight = null;
      } else {
        item.classList.add('open');
        q.setAttribute('aria-expanded', 'true');
        a.style.maxHeight = a.scrollHeight + 'px';
      }
    });
  });

  // Gallery lightbox
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxCap = document.getElementById('lightboxCap');
  const lightboxClose = document.getElementById('lightboxClose');

  document.querySelectorAll('.gallery-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      lightboxImg.src = item.getAttribute('href');
      lightboxImg.alt = item.querySelector('img').alt;
      lightboxCap.textContent = item.dataset.cap || '';
      lightbox.classList.add('open');
    });
  });

  const closeLightbox = () => lightbox.classList.remove('open');
  lightboxClose.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) closeLightbox();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });

  // Reveal on scroll
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('in'));
  }

  // Quote form — submit via fetch (Web3Forms) instead of mailto,
  // so it works with no email client, and we get inline success/error state.
  const quoteForm = document.getElementById('quoteForm');
  const quoteSubmit = document.getElementById('quoteSubmit');
  const quoteStatus = document.getElementById('quoteFormStatus');

  if (quoteForm && quoteStatus) {
    quoteForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const accessKey = quoteForm.querySelector('[name="access_key"]')?.value || '';
      if (!accessKey || accessKey === 'REPLACE_WITH_WEB3FORMS_ACCESS_KEY') {
        quoteStatus.className = 'form-status show error';
        quoteStatus.textContent =
          "Form isn't fully connected yet — call or text " +
          '+1 877 552 8664 and we’ll get you booked directly.';
        return;
      }

      quoteSubmit.disabled = true;
      quoteSubmit.textContent = 'Sending…';
      quoteStatus.className = 'form-status show sending';
      quoteStatus.textContent = 'Sending your request…';

      try {
        const res = await fetch(quoteForm.action, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: new FormData(quoteForm),
        });
        const result = await res.json().catch(() => ({}));

        if (res.ok && result.success !== false) {
          quoteStatus.className = 'form-status show success';
          quoteStatus.textContent =
            "Thanks — we've got your request and will follow up shortly.";
          quoteForm.reset();
        } else {
          throw new Error(result.message || 'Submission failed');
        }
      } catch (err) {
        quoteStatus.className = 'form-status show error';
        quoteStatus.textContent =
          'Something went wrong sending that. Call or text +1 877 552 8664 and we’ll get you sorted.';
      } finally {
        quoteSubmit.disabled = false;
        quoteSubmit.textContent = 'Submit';
      }
    });
  }
})();
