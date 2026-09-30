/* Quickstart and help for every Markov Poet room: steps written as operations, the controls beside their icons,
   and the colour code of the Cineosis signs (the eight domains of the periodic table), with the rule for using each.
   MPGuide.first(room)  opens once per room (then only from the ? control)      MPGuide.open(room)
   MPGuide.legend()     html for the colour code, to place anywhere                  MPGuide.DOMS */
(function () {
  const DOMS = [
    ['perception', '#e9d9a8', 'Perception', 'So Lq Ga', 'Solid, liquid, gaseous: things in space. Choose it to fix where the line happens.'],
    ['affect', '#f0b9a4', 'Affect', 'Ic Dv As', 'Icon (a face, a close-up), dividual, any-space-whatever. Choose it when the line names a quality or a face.'],
    ['action', '#e7a37c', 'Action', 'Sy Mi Ve Im', 'Milieu, vector, symptom, imprint: bodies acting in a world. Choose it when the line has a verb of doing.'],
    ['reflection', '#b9cfa0', 'Thought: reflection', 'Pl Th Qu Ll', 'Figures, theatre, the everyday, the limits of action. Choose it for "like", "as", a staged or ordinary moment.'],
    ['mental', '#a9c9c9', 'Thought: mental', 'Rd Sd Mk Sb', 'Dreams, destinies, marks, symbols. Choose it for a turn of fate, a sign, "because".'],
    ['break', '#d9d3c7', 'Opsign · sonsign', 'Op Sn', 'Pure seeing and pure hearing: the action stops. Choose it for stillness, "nothing moved".'],
    ['time', '#b8b3d8', 'Time-image', 'Mf Sp Pf Ba', 'Mirrors, sheets of the past, powers of the false, bodies. Choose it for "remember", "once", "again".'],
    ['read', '#d9b8d2', 'Lectosign', 'Le', 'An image to be read. Use sparingly.'] ];
  const ICON = n => `<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><use href="#i-${n}"/></svg>`;
  const ROOMS = {
    poet: { title: 'The Poet', lede: 'An empty room. Words in, a film out.',
      steps: [['Type a line and press Return, or tap the mic and say it.', 'The mic takes one line: speak, then pause. The page finds your words itself (the first time it fetches its listener, about 45 MB).'],
              ['Watch the archive answer.', 'About twenty shots rise around your words, sized by their chance. One is taken; the film plays with your line.'],
              ['Add lines.', 'Each line joins the same film. Lines in one stanza share a world.'],
              ['Tap CHOOSE to replace a shot.', 'The drawer shows every shot the engine weighed for that moment. Tap one to keep it. ⌘Z undoes.'],
              ['Tap the red dot to record your voice.', 'Read the whole poem at your own pace, then STOP. The page finds where you read each line, and the film follows your timing.'],
              ['Tap SEND.', 'Share a link: it plays at once on a friend\'s phone, and they can remix it. Or send a small file with your own voice inside.']],
      ctl: [['mic', 'say one line'], ['rec', 'record your voice reading the poem'], ['play', 'play or pause · space'], ['wall', 'choose among the shots'], ['send', 'send or open a project'], ['more', 'calm, film sound, voice, undo, more']] },
    narrative: { title: 'Narrative', lede: 'A poem plays line by line. The wall shows every shot weighed for the line.',
      steps: [['Pick a poem at the top. Tap play.', 'The suite plays against the poet\'s recorded voice; other poems against a Piper voice.'],
              ['Read the wall.', 'Each tile is a shot the engine weighed; the number is its chance. Gold frame: the shot on screen.'],
              ['Tap a tile to try it. Tap ✓ to keep it.', 'The line waits while you try. Keeping recomposes the film. Esc goes back.'],
              ['Tap the grid icon for the gallery.', 'Only the moving pictures, the chosen shot large, the line over it.'],
              ['Tap SEND.', 'Share a link that plays at once, or a small file, or (in the lab) an MP4.']],
      ctl: [['voice', 'voice: recording, Piper, both'], ['mute', 'the films\' own sound'], ['calm', 'calm'], ['grid', 'gallery grid'], ['take', 'another take'], ['send', 'send']] },
    engine: { title: 'The Engine', lede: 'The workshop: paste any text, a transcript or a recording; read how the film was built.',
      steps: [['Paste words, pick a poem, or bring a recording.', 'A transcript with "Name: line" makes each speaker a strand.'],
              ['Tap Make the film.', 'Scenes come from stanzas; each scene gets one film from the archive as its world.'],
              ['Read What the film kept.', 'Kept: a relation in the words that the cut shows. Lost: one it does not. Thin: a line the archive cannot answer.'],
              ['Tap a shot to see its alternatives.', 'Choosing one is counted as a correction.'],
              ['Tap Send.', 'A link that plays at once, a small file, or (in the lab) an MP4.']],
      ctl: [] },
    hub: { title: 'The Markov Poet', lede: 'Three rooms that turn words into films from a public archive.', steps: [], ctl: [] } };
  const css = `.mpg{position:fixed;inset:0;z-index:100;background:#000c;display:flex;align-items:flex-end;justify-content:center;font:13px/1.5 'IBM Plex Mono',ui-monospace,monospace;color:#efe9dd}
  .mpg article{background:#0e0d0c;border:1px solid #2a2723;border-radius:14px 14px 0 0;width:min(640px,100%);max-height:88dvh;overflow:auto;padding:20px 20px calc(20px + env(safe-area-inset-bottom))}
  @media(min-width:760px){.mpg{align-items:center}.mpg article{border-radius:14px}}
  .mpg h2{font:400 26px/1.15 Fraunces,Georgia,serif;margin:0 0 4px}.mpg .lede{color:#9a938a;margin:0 0 16px}
  .mpg ol{list-style:none;margin:0 0 16px;padding:0;counter-reset:s}.mpg li{counter-increment:s;display:grid;grid-template-columns:28px 1fr;gap:2px 10px;padding:9px 0;border-top:1px solid #1f1d1a}
  .mpg li::before{content:counter(s);grid-row:span 2;width:22px;height:22px;border-radius:50%;border:1px solid #e8c070;color:#e8c070;display:grid;place-items:center;font-size:11px}
  .mpg li b{font:400 16px/1.3 Fraunces,Georgia,serif}.mpg li span{color:#9a938a;font-size:12px}
  .mpg h3{font:500 10px 'IBM Plex Mono',monospace;letter-spacing:.2em;color:#9a938a;margin:14px 0 8px}
  .mpg .ctl{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px 12px}.mpg .ctl div{display:flex;gap:8px;align-items:center;color:#cfc8bc}
  .mpg .ok{margin-top:18px;width:100%;min-height:48px;border:0;border-radius:10px;background:#e8c070;color:#1a1408;font:600 14px 'IBM Plex Mono',monospace;letter-spacing:.06em;cursor:pointer}
  .mpleg{display:grid;gap:8px}.mpleg>div{display:grid;grid-template-columns:auto 1fr;gap:0 10px;align-items:start}.mpleg>div>div b{display:block}
  .mpleg i{font-style:normal;min-width:72px;padding:3px 6px;border-radius:3px;color:#15120d;font-size:10.5px;text-align:center;margin-top:2px}
  .mpleg b{font-weight:500;color:#efe9dd}.mpleg span{color:#9a938a;font-size:12px}`;
  let styled = false;
  function legend() { return '<div class="mpleg">' + DOMS.map(d => `<div><i style="background:${d[1]}">${d[3]}</i><div><b>${d[2]}</b> <span>${d[4]}</span></div></div>`).join('') + '</div>'; }
  function open(room) {
    if (!styled) { const s = document.createElement('style'); s.textContent = css; document.head.append(s); styled = true; }
    const R = ROOMS[room] || ROOMS.hub, el = document.createElement('div'); el.className = 'mpg'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', R.title + ': how to use');
    el.innerHTML = `<article><h2>${R.title}</h2><p class="lede">${R.lede}</p>
      ${R.steps.length ? '<ol>' + R.steps.map(s => `<li><b>${s[0]}</b><span>${s[1]}</span></li>`).join('') + '</ol>' : ''}
      ${R.ctl.length ? '<h3>CONTROLS</h3><div class="ctl">' + R.ctl.map(c => `<div>${ICON(c[0])}<span>${c[1]}</span></div>`).join('') + '</div>' : ''}
      <h3>THE COLOUR OF A SHOT: ITS CINEOSIS SIGNS</h3>${legend()}
      <button class="ok">START</button></article>`;
    const close = () => { el.remove(); try { localStorage.setItem('mp.guide.' + room, '1'); } catch (e) { } };
    el.querySelector('.ok').onclick = close; el.onclick = e => { if (e.target === el) close(); };
    addEventListener('keydown', function k(e) { if (e.key === 'Escape') { close(); removeEventListener('keydown', k); } });
    document.body.append(el); el.querySelector('.ok').focus();
  }
  function first(room) { let seen = null; try { seen = localStorage.getItem('mp.guide.' + room); } catch (e) { } if (!seen) open(room); }
  window.MPGuide = { open, first, legend, DOMS, color: dom => (DOMS.find(d => d[0] === dom) || [0, '#ccc'])[1] };
})();
