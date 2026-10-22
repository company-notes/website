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
        if (key === 'company-notes:paper') return options.paper || null;
        return null;
      },
    },
    document: { documentElement: { dataset: appliedColors } },
  };
  vm.runInNewContext(bootstrap, source, { timeout: 1500 });
  return { redirectedTo, paper: appliedColors.cnPaper || null };
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
assert.equal(visit('/blog/grok-bot-backup/', { savedLanguage: 'en', paper: 'sage' }).paper, 'sage');
console.log(`Locale redirects: ${checks.length} cases passed; paper preference preserved.`);
