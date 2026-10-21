/* Company Notes: localized navigation, paper previews, and homepage reading carousel. */
(function () {
  'use strict';
  const PAPER_KEY = 'company-notes:paper';
  const LANGUAGE_KEY = 'company-notes:language';
  const DEFAULT_PAPER = 'warm'; // Once a default is chosen, change this and the token fallback.
  const papers = new Set(['warm', 'white', 'cream', 'mist', 'sage', 'blush']);

  function readPreference(key) { try { return window.localStorage.getItem(key); } catch (_) { return null; } }
  function writePreference(key, value) { try { window.localStorage.setItem(key, value); } catch (_) {} }

  function setupLanguageLinks() {
    const path = window.location.pathname.replace(/^\/(en|zh-hans)(?=\/)/, '') || '/';
    const destinations = { '/': path, '/en/': '/en' + path, '/zh-hans/': '/zh-hans' + path };
    document.querySelectorAll('a.md-select__link[href]').forEach(function (link) {
      const url = new URL(link.href, window.location.origin);
      if (url.origin !== window.location.origin) return;
      if (!Object.prototype.hasOwnProperty.call(destinations, url.pathname)) return;
      const locale = url.pathname === '/en/' ? 'en' : url.pathname === '/zh-hans/' ? 'zh-hans' : 'zh-hant';
      url.pathname = destinations[url.pathname];
      link.href = url.toString();
      link.addEventListener('click', function () { writePreference(LANGUAGE_KEY, locale); });
    });
  }

  function setupPaperPicker() {
    const picker = document.querySelector('[data-cn-paper-picker]');
    if (!picker) return;
    const buttons = [...picker.querySelectorAll('[data-cn-paper-option]')];
    const output = picker.querySelector('[data-cn-paper-choice]');
    const stored = readPreference(PAPER_KEY);
    let current = papers.has(stored) ? stored : DEFAULT_PAPER;
    function choose(value, save) {
      if (!papers.has(value)) return;
      current = value;
      document.documentElement.dataset.cnPaper = value;
      buttons.forEach(function (button) {
        const selected = button.dataset.cnPaperOption === value;
        button.setAttribute('aria-pressed', String(selected));
        if (selected && output) output.textContent = button.dataset.cnPaperName;
      });
      if (save) writePreference(PAPER_KEY, value);
    }
    buttons.forEach(function (button) {
      button.addEventListener('click', function () { choose(button.dataset.cnPaperOption, true); });
    });
    choose(current, false);
  }

  function setupCarousel() {
    const widget = document.querySelector('[data-cn-carousel]');
    if (!widget) return;
    const track = widget.querySelector('[data-cn-track]');
    const slides = [...widget.querySelectorAll('[data-cn-slide]')];
    const dots = [...widget.querySelectorAll('[data-cn-dot]')];
    const prev = widget.querySelector('[data-cn-prev]');
    const next = widget.querySelector('[data-cn-next]');
    const viewport = widget.querySelector('[data-cn-viewport]');
    if (!track || slides.length < 2 || !prev || !next || !viewport) return;
    let index = 0;
    let pointerX = null;
    let timer = null;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let paused = false;
    function show(to) {
      index = (to + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + (100 * index) + '%)';
      slides.forEach(function (slide, i) {
        slide.toggleAttribute('inert', i !== index);
        slide.setAttribute('aria-hidden', String(i !== index));
      });
      dots.forEach(function (dot, i) { dot.setAttribute('aria-pressed', String(i === index)); });
    }
    function stop() { if (timer !== null) { clearInterval(timer); timer = null; } }
    function start() {
      stop();
      if (paused || document.hidden || reduceMotion.matches) return;
      timer = window.setInterval(function () { show(index + 1); }, 6500);
    }
    function change(to) { show(to); start(); }
    prev.addEventListener('click', function () { change(index - 1); });
    next.addEventListener('click', function () { change(index + 1); });
    dots.forEach(function (dot, i) { dot.addEventListener('click', function () { change(i); }); });
    widget.addEventListener('mouseenter', function () { paused = true; stop(); });
    widget.addEventListener('mouseleave', function () { paused = false; start(); });
    widget.addEventListener('focusin', function () { paused = true; stop(); });
    widget.addEventListener('focusout', function (event) {
      if (!widget.contains(event.relatedTarget)) { paused = false; start(); }
    });
    viewport.addEventListener('touchstart', function (event) { pointerX = event.changedTouches[0].clientX; }, { passive: true });
    viewport.addEventListener('touchend', function (event) {
      if (pointerX === null) return;
      const distance = event.changedTouches[0].clientX - pointerX;
      pointerX = null;
      if (Math.abs(distance) > 45) change(index + (distance < 0 ? 1 : -1));
    }, { passive: true });
    widget.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault(); change(index + (event.key === 'ArrowRight' ? 1 : -1));
      }
    });
    document.addEventListener('visibilitychange', start);
    if (reduceMotion.addEventListener) reduceMotion.addEventListener('change', start);
    show(0);
    start();
  }

  function boot() {
    document.documentElement.classList.add('cn-ready');
    setupLanguageLinks();
    setupPaperPicker();
    setupCarousel();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
