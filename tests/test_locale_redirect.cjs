// Check browser-side locale routing without any test dependency.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const template = fs.readFileSync(path.join(__dirname, '..', 'overrides', 'main.html'), 'utf8');
const match = template.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, 'Main template must include the early locale redirect');
const bootstrap = match[1];

function visit(pathname, options = {}) {
  let redirectedTo = null;
  const appliedColors = {};
  const session = options.session || {};
  const randomValues = options.randomValues || [options.random ?? 0.25];
  let randomIndex = 0;
  const source = {
    location: {
      pathname,
      search: options.search || '',
      hash: options.hash || '',
      replace(to) { redirectedTo = to; },
    },
    navigator: {
      language: options.browser || 'en-US',
      languages: options.browserLanguages || [options.browser || 'en-US'],
    },
    localStorage: {
      getItem(key) {
        if (key === 'company-notes:language') return options.savedLanguage || null;
        if (key === 'company-notes:paper') return options.legacyPaper || null;
        return null;
      },
    },
    sessionStorage: {
      getItem(key) { return session[key] || null; },
      setItem(key, value) { session[key] = String(value); },
    },
    Math: {
      random() { return randomValues[Math.min(randomIndex++, randomValues.length - 1)]; },
      floor: Math.floor,
    },
    document: { documentElement: { dataset: appliedColors } },
  };
  vm.runInNewContext(bootstrap, source, { timeout: 1500 });
  return { redirectedTo, paper: appliedColors.cnPaper || null, session };
}

const checks = [
  ['saved English on an article deep link', '/blog/grok-bot-backup/', { savedLanguage: 'en' }, '/en/blog/grok-bot-backup/'],
  ['browser English on an article deep link', '/blog/grok-bot-backup/', { browser: 'en-US' }, '/en/blog/grok-bot-backup/'],
  ['browser Simplified Chinese on an article', '/blog/grok-bot-backup/', { browser: 'zh-CN' }, '/zh-hans/blog/grok-bot-backup/'],
  ['browser zh-Hans on an article', '/blog/grok-bot-backup/', { browser: 'zh-Hans' }, '/zh-hans/blog/grok-bot-backup/'],
  ['browser zh-SG on a static content page', '/about/', { browser: 'zh-SG' }, '/zh-hans/about/'],
  ['browser zh-TW keeps Traditional Chinese', '/blog/grok-bot-backup/', { browser: 'zh-TW' }, null],
  ['saved Traditional wins over English browser', '/blog/grok-bot-backup/', { browser: 'en-US', savedLanguage: 'zh-hant' }, null],
  ['saved English wins over Traditional browser', '/', { browser: 'zh-TW', savedLanguage: 'en' }, '/en/'],
  ['explicit English URL wins over saved Traditional', '/en/blog/grok-bot-backup/', { savedLanguage: 'zh-hant' }, null],
  ['explicit Simplified URL wins over saved English', '/zh-hans/blog/grok-bot-backup/', { savedLanguage: 'en' }, null],
  ['blog index gets localized', '/blog/', { savedLanguage: 'en' }, '/en/blog/'],
  ['playbook page gets localized', '/playbooks/organization/', { savedLanguage: 'en' }, '/en/playbooks/organization/'],
  ['toolkit page gets localized', '/toolkit/', { savedLanguage: 'en' }, '/en/toolkit/'],
  ['unknown routes do not get guessed redirects', '/this-route-does-not-exist/', { savedLanguage: 'en' }, null],
  ['assets never redirect', '/assets/covers/field-notes.svg', { savedLanguage: 'en' }, null],
  ['sitemap never redirects', '/sitemap.xml', { savedLanguage: 'en' }, null],
  ['query and hash survive redirect', '/blog/grok-bot-backup/', { savedLanguage: 'en', search: '?utm_source=share', hash: '#export' }, '/en/blog/grok-bot-backup/?utm_source=share#export'],
];
for (const [label, pathname, options, expected] of checks) {
  const actual = visit(pathname, options).redirectedTo;
  assert.equal(actual, expected, label);
}
// A new session draws once: white 75%, each of five alternatives 5%.
assert.equal(visit('/', { randomValues: [0] }).paper, 'white');
assert.equal(visit('/', { randomValues: [0.749999] }).paper, 'white');
const alternatives = ['warm', 'cream', 'mist', 'sage', 'blush'];
for (let index = 0; index < alternatives.length; index++) {
  const result = visit('/', { randomValues: [0.75, (index + 0.5) / alternatives.length] });
  assert.equal(result.paper, alternatives[index]);
  assert.equal(result.session['company-notes:paper-session'], alternatives[index]);
}
const session = {};
assert.equal(visit('/', { session, randomValues: [0.8, 0.5] }).paper, 'mist');
assert.equal(visit('/en/blog/grok-bot-backup/', { session, randomValues: [0.01] }).paper, 'mist');
assert.equal(visit('/zh-hans/', { session, randomValues: [0.01] }).paper, 'mist');
assert.equal(visit('/', { legacyPaper: 'sage', randomValues: [0.1] }).paper, 'white');
const pickerSource = fs.readFileSync(path.join(__dirname, '..', 'shared/javascripts/site.js'), 'utf8');
assert.ok(pickerSource.includes("saveSessionPaper(value)"));
assert.ok(pickerSource.includes("document.documentElement.dataset.cnPaper"));
assert.ok(!pickerSource.includes("localStorage.setItem(PAPER_SESSION_KEY"));
console.log(`Locale redirects: ${checks.length} cases passed; weighted session paper selection passed.`);
