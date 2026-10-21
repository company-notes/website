/* Keep readers on the same article when using Material's language picker.
 * Each locale is independently built with matching Markdown slugs and routes.
 */
(function () {
  document.documentElement.classList.add('cn-ready');

  function translateLinks() {
    var path = window.location.pathname.replace(/^\/(en|zh-hans)(?=\/)/, '');
    if (!path.startsWith('/')) path = '/' + path;
    var destinations = {
      '/': path,
      '/en/': '/en' + path,
      '/zh-hans/': '/zh-hans' + path
    };
    document.querySelectorAll('a.md-select__link[href]').forEach(function (link) {
      var url = new URL(link.href, window.location.origin);
      if (url.origin !== window.location.origin) return;
      if (Object.prototype.hasOwnProperty.call(destinations, url.pathname)) {
        link.href = destinations[url.pathname];
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', translateLinks, {once: true});
  } else {
    translateLinks();
  }
})();
