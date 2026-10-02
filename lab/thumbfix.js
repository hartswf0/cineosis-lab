/* A thumbnail the site does not carry is fetched from the archive's CDN, where every clip's picture lives beside its video.
   The index (aspect/thumbs.json: CDN folders, and each clip's folder by the first 8 characters of its id) loads on the first miss. */
(function () {
  const R2 = 'https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/', here = document.currentScript && document.currentScript.src.replace(/thumbfix\.js.*$/, '');
  let IX = null;
  const load = () => IX || (IX = fetch(here + 'aspect/thumbs.json').then(r => r.json()).catch(() => null));
  document.addEventListener('error', e => {
    const im = e.target; if (!im || im.tagName !== 'IMG' || im.dataset.cdn) return;
    const m = (im.getAttribute('src') || '').match(/([0-9a-f]{8})-[0-9a-f-]{27}\.jpg/); if (!m) return; im.dataset.cdn = 1;
    const id = (im.getAttribute('src').match(/([0-9a-f-]{36})\.jpg/) || [])[1];
    load().then(d => { if (!d) return; const k = d.map[m[1]]; if (k != null) im.src = R2 + d.pre[k] + '/thumbnails/' + ((d.stem || {})[m[1]] || id) + '.jpg'; });
  }, true);
})();
