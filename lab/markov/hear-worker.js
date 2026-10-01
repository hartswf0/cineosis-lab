// The Markov Poet's own ears, off the main thread: Whisper (tiny, English, with word timestamps) through transformers.js.
// in:  {id, pcm: Float32Array at 16 kHz}     out: {id, text, words: [{w, t0, t1}]} | {id, error} ; progress: {status, frac}
import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1';
env.allowLocalModels = false;
let pipe = null;
async function load() {
  if (!pipe) { const seen = {};
    pipe = pipeline('automatic-speech-recognition', 'onnx-community/whisper-tiny.en_timestamped', { dtype: { encoder_model: 'fp32', decoder_model_merged: 'q8' },
      progress_callback: p => { if (p.status === 'progress' && p.total) { seen[p.file] = [p.loaded, p.total]; const a = Object.values(seen).reduce((s, x) => [s[0] + x[0], s[1] + x[1]], [0, 0]); postMessage({ status: 'loading', frac: a[0] / a[1] }); } } });
    pipe.then(() => postMessage({ status: 'ready' })).catch(() => { }); }
  return pipe;
}
// fetch the listener's files into the browser's cache without starting it (phones: no memory used until the mic is tapped)
async function prefetch() {
  const base = 'https://huggingface.co/onnx-community/whisper-tiny.en_timestamped/resolve/main/', files = ['onnx/encoder_model.onnx', 'onnx/decoder_model_merged_quantized.onnx'];
  try { const c = await caches.open('transformers-cache'); for (const f of files) { if (!(await c.match(base + f))) { const r = await fetch(base + f); if (r.ok) await c.put(base + f, r); } } postMessage({ status: 'cached' }); } catch (e) { }
}
onmessage = async e => {
  const { id, pcm, warm } = e.data; if (e.data.prefetch) return prefetch();
  try { const p = await load(); if (warm) return;
    const out = await p(pcm, { return_timestamps: 'word', chunk_length_s: 29, stride_length_s: 4 });
    postMessage({ id, text: (out.text || '').trim(), words: (out.chunks || []).map(c => ({ w: c.text.trim(), t0: c.timestamp[0], t1: c.timestamp[1] == null ? c.timestamp[0] + .3 : c.timestamp[1] })) });
  } catch (err) { pipe = null; postMessage({ id, error: String(err && err.message || err) }); }
};
