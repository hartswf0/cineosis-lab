/* Reading words in the browser: the text half of OpenAI's CLIP ViT-B/32 (transformers.js, Xenova/clip-vit-base-patch32, half precision: 8-bit drifts to cosine .86-.96, fp16 matches the server at 1.0000),
   the same model that read the shots (shannon/embed_openai.py). No server needed; the model (~125 MB) is fetched once and cached by the browser.
   window.ClipText.encode(texts, onStatus) -> Promise<number[][]> (unit vectors, 512-d) */
(function () {
  let ready = null;
  function load(onStatus) {
    if (!ready) ready = (async () => {
      onStatus && onStatus({ stage: 'loading', text: 'fetching the reader' });
      const T = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1');
      T.env.allowLocalModels = false;
      const id = 'Xenova/clip-vit-base-patch32';
      const tok = await T.AutoTokenizer.from_pretrained(id);
      const seen = {};
      const prog = p => { if (p.status === 'progress' && p.total) { seen[p.file] = [p.loaded, p.total]; const a = Object.values(seen).reduce((s, x) => [s[0] + x[0], s[1] + x[1]], [0, 0]);
          onStatus && onStatus({ stage: 'loading', text: 'learning to read', frac: a[0] / a[1] }); } };
      let model;
      // phones keep little memory for a page: they take the lighter reader (8-bit, ~65 MB) so the listener fits beside it
      const small = /iP(hone|ad|od)|Android/.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Mac/.test(navigator.platform)) || (navigator.deviceMemory && navigator.deviceMemory <= 4);
      try { model = await T.CLIPTextModelWithProjection.from_pretrained(id, { dtype: small ? 'q8' : 'fp16', progress_callback: prog }); }
      catch (e) { // a phone that cannot hold the exact reader gets the lighter one (8-bit): slightly different choices, but it runs
        for (const k in seen) delete seen[k]; model = await T.CLIPTextModelWithProjection.from_pretrained(id, { dtype: 'q8', progress_callback: prog }); }
      onStatus && onStatus({ stage: 'ready', text: 'reading' });
      return async texts => {
        const inp = tok(texts, { padding: true, truncation: true });
        const { text_embeds } = await model(inp);
        const d = text_embeds.dims[1], x = text_embeds.data;
        return texts.map((_, i) => { const v = Array.from(x.slice(i * d, (i + 1) * d)); const n = Math.hypot(...v) || 1; return v.map(y => y / n); });
      };
    })().catch(e => { ready = null; throw e; });
    return ready;
  }
  window.ClipText = { encode: async (texts, onStatus) => (await load(onStatus))(texts), warm: onStatus => load(onStatus) };
})();
