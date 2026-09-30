/* Reading words in the browser: the text half of OpenAI's CLIP ViT-B/32 (transformers.js, Xenova/clip-vit-base-patch32).
   Every device takes the 8-bit model (62 MB, fetched once, then cached) and a 512x512 correction (markov/reader-fix.bin, fitted
   by markov/fit_reader.py) that carries its output onto the exact model that read the shots. Measured on 400 phrases, by the exact
   reader's own score of the shot chosen: exact 41.3 · 8-bit 38.9 · 8-bit corrected ~39.5 · random 30. The exact model is 121 MB:
   twice the wait for that last step. The lab server (/api/embed) still reads exactly.
   window.ClipText.encode(texts, onStatus) -> Promise<number[][]>     .warm(onStatus)     .state -> 'idle' | 'loading' | 'ready' | 'failed'
   onStatus({stage: 'loading' | 'ready' | 'failed', text, frac, eta})  eta: seconds left, from the download speed so far */
(function () {
  let ready = null; const subs = new Set(); const api = { state: 'idle', frac: 0, eta: null };
  const tell = s => { Object.assign(api, { frac: s.frac == null ? api.frac : s.frac, eta: s.eta }); if (s.stage === 'ready') api.state = 'ready'; else if (s.stage === 'failed') api.state = 'failed'; else api.state = 'loading'; subs.forEach(f => { try { f(s); } catch (e) { } }); };
  function load(onStatus) {
    if (onStatus) subs.add(onStatus);
    if (!ready) ready = (async () => {
      const t0 = performance.now(); tell({ stage: 'loading', text: 'fetching the reader', frac: 0 });
      const fix = fetch(new URL('markov/reader-fix.bin', document.baseURI)).then(r => r.ok ? r.arrayBuffer() : null).then(b => b && new Float32Array(b)).catch(() => null);
      const T = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1');
      T.env.allowLocalModels = false;
      const id = 'Xenova/clip-vit-base-patch32', seen = {};
      const prog = p => { if (p.status === 'progress' && p.total) { seen[p.file] = [p.loaded, p.total]; const a = Object.values(seen).reduce((s, x) => [s[0] + x[0], s[1] + x[1]], [0, 0]);
          const el = (performance.now() - t0) / 1000, rate = a[0] / Math.max(.2, el), eta = a[0] > 2e5 ? Math.max(0, (a[1] - a[0]) / rate) : null;
          tell({ stage: 'loading', text: 'fetching the reader', frac: a[0] / a[1], eta }); } };
      const [tok, model, W] = await Promise.all([T.AutoTokenizer.from_pretrained(id), T.CLIPTextModelWithProjection.from_pretrained(id, { dtype: 'q8', progress_callback: prog }), fix]);
      tell({ stage: 'ready', text: 'ready', frac: 1, eta: 0 });
      return async texts => {
        const inp = tok(texts, { padding: true, truncation: true }), { text_embeds } = await model(inp), d = text_embeds.dims[1], x = text_embeds.data;
        return texts.map((_, i) => { let v = x.slice(i * d, (i + 1) * d), n = Math.hypot(...v) || 1;
          if (W) { const q = Array.from(v, y => y / n), o = new Float64Array(d); for (let a = 0; a < d; a++) { const qa = q[a], row = a * d; for (let b = 0; b < d; b++) o[b] += qa * W[row + b]; } v = o; n = Math.hypot(...v) || 1; }
          return Array.from(v, y => y / n); });
      };
    })().catch(e => { ready = null; tell({ stage: 'failed', text: 'the reader could not load: ' + (e.message || e) }); throw e; });
    return ready;
  }
  api.encode = async (texts, onStatus) => (await load(onStatus))(texts); api.warm = onStatus => load(onStatus).catch(() => { }); api.off = f => subs.delete(f);
  window.ClipText = api;
})();
