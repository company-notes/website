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
    const header = document.querySelector('.md-header__inner');
    if (!header || header.querySelector('[data-cn-paper-toolbar]')) return;
    const locale = window.location.pathname.startsWith('/en/') ? 'en' : window.location.pathname.startsWith('/zh-hans/') ? 'zh-hans' : 'zh-hant';
    const strings = {
      'zh-hant': { heading:'網站底色', tool:'變更網站底色', warm:'暖白', white:'紙白', cream:'奶油', mist:'霧藍', sage:'淺綠', blush:'霧粉' },
      'zh-hans': { heading:'网站底色', tool:'更改网站底色', warm:'暖白', white:'纸白', cream:'奶油', mist:'雾蓝', sage:'浅绿', blush:'雾粉' },
      'en': { heading:'Page background', tool:'Change page background', warm:'Warm', white:'Paper', cream:'Cream', mist:'Blue mist', sage:'Sage', blush:'Blush' }
    }[locale];
    const wrap = document.createElement('div');
    wrap.className = 'cn-paper-toolbar';
    wrap.dataset.cnPaperToolbar = '';
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'cn-paper-toggle';
    toggle.setAttribute('aria-label', strings.tool);
    toggle.title = strings.tool;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-haspopup', 'true');
    toggle.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5a8.5 8.5 0 1 0 8.5 8.5c0-1.5-1.2-2.2-2.3-2.2h-1.7c-1 0-1.6-.8-1.6-1.6 0-.8.6-1.5 1.4-2.1A8.5 8.5 0 0 0 12 3.5Z"/><circle cx="7.5" cy="11" r="1"/><circle cx="11" cy="7.5" r="1"/><circle cx="8.8" cy="16" r="1"/></svg>';
    const panel = document.createElement('div');
    panel.className = 'cn-paper-panel';
    panel.hidden = true;
    panel.setAttribute('role', 'group');
    panel.setAttribute('aria-label', strings.heading);
    const heading = document.createElement('p');
    heading.className = 'cn-paper-panel__heading';
    heading.textContent = strings.heading;
    panel.append(heading);
    const options = document.createElement('div');
    options.className = 'cn-paper-panel__options';
    const buttons = [];
    for (const color of papers) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'cn-paper-option';
      btn.dataset.cnPaperOption = color;
      btn.setAttribute('aria-pressed','false');
      const chip = document.createElement('span');
      chip.className = 'cn-paper-chip cn-paper-chip--' + color;
      chip.setAttribute('aria-hidden','true');
      btn.append(chip, document.createTextNode(strings[color]));
      options.append(btn);
      buttons.push(btn);
    }
    panel.append(options);
    wrap.append(toggle,panel);
    const language = Array.from(header.querySelectorAll('.md-header__option')).find(function (node) { return node.querySelector('.md-select'); });
    const anchor = language || header.querySelector('.md-header__option') || header.querySelector('.md-search');
    if (anchor) header.insertBefore(wrap, anchor);
    else header.append(wrap);
    function choose(value, save) {
      if (!papers.has(value)) return;
      document.documentElement.dataset.cnPaper = value;
      for (const btn of buttons) btn.setAttribute('aria-pressed', String(btn.dataset.cnPaperOption === value));
      if (save) writePreference(PAPER_KEY, value);
    }
    choose(papers.has(readPreference(PAPER_KEY)) ? readPreference(PAPER_KEY) : DEFAULT_PAPER, false);
    function open(value) {
      panel.hidden = !value;
      toggle.setAttribute('aria-expanded',String(value));
    }
    toggle.addEventListener('click',function () { open(panel.hidden); });
    for (const btn of buttons) btn.addEventListener('click',function () {
      choose(btn.dataset.cnPaperOption,true);
      open(false);
      toggle.focus();
    });
    document.addEventListener('pointerdown',function (event) { if (!wrap.contains(event.target)) open(false); });
    document.addEventListener('keydown',function (event) {
      if (event.key === 'Escape' && !panel.hidden) { open(false); toggle.focus(); }
    });
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
