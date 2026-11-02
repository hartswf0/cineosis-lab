// Builds index.html for wg-lego-two-screens from renders/anchors.json. Static SVG, no page script.
const fs = require('fs'), path = require('path');
const OUT = process.argv[2];
const AN = JSON.parse(fs.readFileSync(path.join(OUT, 'renders/anchors.json'), 'utf8'));
const C = { ink:'#ece6da', dim:'#b3ab9e', faint:'#7a7368', rule:'#2e2a26', lime:'#c4f46a', orange:'#efa13a', amber:'#efb94a', red:'#e0483a', bg:'#0b0a09', panel:'#12100e', blue:'#7fb2ff' };
const f = n => +n.toFixed(1);

// ---------- hand landmark templates (21 points, MediaPipe order; wrist at 0,0; y up is negative) ----------
const T = {
  open: [[0,0],[-.25,-.1],[-.42,-.25],[-.55,-.4],[-.65,-.52],[-.2,-.55],[-.24,-.8],[-.26,-.95],[-.28,-1.08],[-.02,-.58],[-.02,-.86],[-.02,-1.03],[-.02,-1.17],[.15,-.54],[.19,-.79],[.21,-.95],[.23,-1.07],[.3,-.46],[.37,-.64],[.41,-.76],[.44,-.87]],
  pinch: [[0,0],[-.25,-.1],[-.4,-.25],[-.46,-.42],[-.46,-.58],[-.2,-.55],[-.33,-.72],[-.42,-.7],[-.45,-.6],[-.02,-.58],[-.08,-.84],[-.1,-.98],[-.12,-1.1],[.15,-.54],[.15,-.78],[.15,-.92],[.15,-1.03],[.3,-.46],[.34,-.63],[.36,-.74],[.37,-.84]],
  v: [[0,0],[-.22,-.12],[-.3,-.28],[-.18,-.4],[-.06,-.45],[-.18,-.55],[-.3,-.8],[-.36,-.96],[-.42,-1.1],[-.02,-.58],[.06,-.85],[.1,-1.0],[.14,-1.14],[.15,-.54],[.2,-.68],[.14,-.62],[.1,-.52],[.28,-.46],[.32,-.58],[.27,-.55],[.22,-.47]],
};
const BONES = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[17,18],[18,19],[19,20],[0,17]];
function anchorOf(kind, pts){
  if(kind === 'pinch') return [(pts[4][0]+pts[8][0])/2, (pts[4][1]+pts[8][1])/2];
  const ids = [0,5,9,13,17]; return [ids.reduce((s,i)=>s+pts[i][0],0)/5, ids.reduce((s,i)=>s+pts[i][1],0)/5];
}
// skeleton line drawing: kind, anchor (x,y) in svg units, scale px/unit, opts
function hand(kind, [ax, ay], s, o={}){
  const pts0 = T[kind], [cx, cy] = anchorOf(kind, pts0), rot = o.rot||0, mx = o.mirror ? -1 : 1;
  const P = pts0.map(([x,y]) => { let X = (x-cx)*mx, Y = y-cy; const c=Math.cos(rot), sn=Math.sin(rot); return [f(ax + s*(X*c - Y*sn)), f(ay + s*(X*sn + Y*c))]; });
  const col = o.color || C.ink, op = o.opacity ?? 1;
  let g = `<g opacity="${op}" stroke-linecap="round" stroke-linejoin="round">`;
  g += `<g stroke="${C.bg}" stroke-width="5" opacity=".7">` + BONES.map(([a,b]) => `<line x1="${P[a][0]}" y1="${P[a][1]}" x2="${P[b][0]}" y2="${P[b][1]}"/>`).join('') + '</g>';
  g += `<g stroke="${col}" stroke-width="2"${o.dash?' stroke-dasharray="4 3"':''}>` + BONES.map(([a,b]) => `<line x1="${P[a][0]}" y1="${P[a][1]}" x2="${P[b][0]}" y2="${P[b][1]}"/>`).join('') + '</g>';
  if(o.span){ g += `<line x1="${P[0][0]}" y1="${P[0][1]}" x2="${P[9][0]}" y2="${P[9][1]}" stroke="${C.orange}" stroke-width="4" opacity=".95"/>`; }
  g += P.map((p,i) => `<circle cx="${p[0]}" cy="${p[1]}" r="${[4,8].includes(i)&&kind==='pinch'?3.6:2.6}" fill="${[4,8].includes(i)&&kind==='pinch'?C.lime:C.bg}" stroke="${col}" stroke-width="1.3"/>`).join('');
  if(o.span){ g += pill(P[0][0], P[0][1] + 20, o.span, C.orange, 'middle', false, 13); }
  return g + '</g>';
}

// ---------- small drawing helpers ----------
function pill(x, y, text, color=C.lime, anchor='middle', solid=false, size=13.5){
  const w = text.length*size*0.62 + 14, h = size + 9;
  const x0 = anchor==='middle' ? x - w/2 : anchor==='end' ? x - w : x;
  return `<g><rect x="${f(x0)}" y="${f(y-h/2)}" width="${f(w)}" height="${h}" rx="${h/2}" fill="${solid?color:'rgba(11,10,9,.82)'}" stroke="${color}" stroke-width="1.2"/><text x="${f(x0+w/2)}" y="${f(y+size*0.36)}" text-anchor="middle" font-size="${size}" fill="${solid?'#111':color}" font-family="IBM Plex Mono,monospace">${text}</text></g>`;
}
function btn(x, y, text, color, solid){ return pill(x, y, text, color, 'middle', solid, 15); }
const mapPt = (b, p) => [f(b.x + p[0]*b.w), f(b.y + p[1]*b.h)];
const an = (img, k) => AN[img].anchors[k];
const hl = (img, k) => AN[img].hulls[k];
function outline(b, img, k, color=C.lime, dash=false, w=2){
  const pts = hl(img, k).map(p => mapPt(b, p).join(',')).join(' ');
  return `<polygon points="${pts}" fill="none" stroke="${color}" stroke-width="${w}"${dash?' stroke-dasharray="6 4"':''} stroke-linejoin="round"/>`;
}
function dropLine(b, from, to){
  const [x1,y1] = mapPt(b, from), [x2,y2] = mapPt(b, to);
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.lime}" stroke-width="2" stroke-dasharray="5 4"/><circle cx="${x2}" cy="${y2}" r="5" fill="none" stroke="${C.lime}" stroke-width="2"/><line x1="${x2-9}" y1="${y2}" x2="${x2+9}" y2="${y2}" stroke="${C.lime}" stroke-width="1.5"/>`;
}
function tick(x, y, color=C.lime, s=1){ return `<path d="M${x-5*s} ${y} l${3.5*s} ${3.5*s} l${7*s} -${8*s}" fill="none" stroke="${color}" stroke-width="${2.2*s}" stroke-linecap="round" stroke-linejoin="round"/>`; }
function cross(x, y, color=C.red, s=1){ return `<path d="M${x-4*s} ${y-4*s} l${8*s} ${8*s} M${x+4*s} ${y-4*s} l-${8*s} ${8*s}" stroke="${color}" stroke-width="${2*s}" stroke-linecap="round"/>`; }
// camera marker: circle with centre dot = the lens points out of the page, toward the viewer
function camMark(x, y, label, color, note){
  return `<g><circle cx="${x}" cy="${y}" r="6.5" fill="${C.bg}" stroke="${color}" stroke-width="1.6"/><circle cx="${x}" cy="${y}" r="2.2" fill="${color}"/><text x="${x+12}" y="${y+4.5}" font-size="12.5" fill="${color}" font-family="IBM Plex Mono,monospace" font-weight="500">${label}</text>${note?`<text x="${x+28}" y="${y+4.5}" font-size="11" fill="${C.dim}" font-family="IBM Plex Mono,monospace">${note}</text>`:''}</g>`;
}

// ---------- mascots ----------
function butter(x, y, s=1, mood='happy'){
  // isometric stick of butter, 1 unit = s px
  const t = (a,b) => `${f(x+a*s)} ${f(y+b*s)}`;
  const mouth = mood==='happy' ? `M${t(15,24)} Q${t(20,29)} ${t(25,24)}` : mood==='flat' ? `M${t(15,25)} L${t(25,25)}` : mood==='o' ? '' : `M${t(15,26)} Q${t(20,22)} ${t(25,26)}`;
  return `<g stroke="#3a2e14" stroke-width="${f(1.2*s)}" stroke-linejoin="round">
<path d="M${t(0,10)} L${t(12,0)} L${t(58,0)} L${t(46,10)} Z" fill="#fbeaa2"/>
<path d="M${t(46,10)} L${t(58,0)} L${t(58,22)} L${t(46,32)} Z" fill="#e3bf55"/>
<path d="M${t(0,10)} L${t(46,10)} L${t(46,32)} L${t(0,32)} Z" fill="#f5d670"/>
<path d="M${t(34,10)} L${t(46,0)} L${t(52,0)} L${t(40,10)} Z M${t(34,10)} L${t(40,10)} L${t(40,32)} L${t(34,32)} Z" fill="#f1ebdd"/>
<circle cx="${f(x+15*s)}" cy="${f(y+18*s)}" r="${f(1.8*s)}" fill="#2a2010" stroke="none"/><circle cx="${f(x+25*s)}" cy="${f(y+18*s)}" r="${f(1.8*s)}" fill="#2a2010" stroke="none"/>
${mood==='o' ? `<circle cx="${f(x+20*s)}" cy="${f(y+25*s)}" r="${f(2*s)}" fill="none" stroke="#2a2010" stroke-width="${f(1.3*s)}"/>` : `<path d="${mouth}" fill="none" stroke="#2a2010" stroke-width="${f(1.4*s)}" stroke-linecap="round"/>`}
<circle cx="${f(x+10.5*s)}" cy="${f(y+22.5*s)}" r="${f(2.2*s)}" fill="#f0a77a" stroke="none" opacity=".55"/><circle cx="${f(x+29.5*s)}" cy="${f(y+22.5*s)}" r="${f(2.2*s)}" fill="#f0a77a" stroke="none" opacity=".55"/>
</g>`;
}
// cartoon hand mascot: thick round strokes over the landmark template, with a face on the palm
function handMascot(kind, x, y, s, color=C.lime){
  const pts0 = T[kind], [cx, cy] = anchorOf('open', pts0);
  const P = pts0.map(([a,b]) => [f(x + (a-cx)*s), f(y + (b-cy)*s)]);
  const fingers = [[0,1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[17,18,19,20]];
  let g = `<g stroke-linecap="round" stroke-linejoin="round" fill="none">`;
  const palm = [P[0],P[1],P[5],P[9],P[13],P[17]].map(p=>p.join(',')).join(' ');
  g += `<polygon points="${palm}" fill="${color}" stroke="${color}" stroke-width="${f(s*0.36)}"/>`;
  g += fingers.map(fi => `<polyline points="${fi.map(i=>P[i].join(',')).join(' ')}" stroke="${color}" stroke-width="${f(s*0.17)}"/>`).join('');
  const mx = (P[0][0]+P[9][0])/2, my = (P[0][1]+P[9][1])/2 + s*0.04;
  g += `<circle cx="${f(mx-s*0.09)}" cy="${f(my-s*0.03)}" r="${f(s*0.03)}" fill="#111"/><circle cx="${f(mx+s*0.09)}" cy="${f(my-s*0.03)}" r="${f(s*0.03)}" fill="#111"/><path d="M${f(mx-s*0.07)} ${f(my+s*0.06)} Q${f(mx)} ${f(my+s*0.12)} ${f(mx+s*0.07)} ${f(my+s*0.06)}" stroke="#111" stroke-width="${f(s*0.025)}"/>`;
  return g + '</g>';
}
const svgBox = (vb, inner, cls='', label='') => `<svg class="${cls}" viewBox="${vb}" role="img"${label?` aria-label="${label}"`:''} xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
function chip(text, kind){
  const icon = kind==='ok' ? svgBox('0 0 64 36', butter(3,2,0.98,'happy'), 'ci') : kind==='pause' ? svgBox('0 0 64 36', butter(3,2,0.98,'flat'), 'ci') : kind==='warn' ? svgBox('0 0 64 36', butter(3,2,0.98,'o'), 'ci') : svgBox('0 0 40 40', handMascot('open', 20, 22, 26), 'ci h');
  return `<span class="chip ${kind}">${icon}<span>${text}</span></span>`;
}

// ---------- the two screens ----------
const LB = { x:26, y:32, w:428, h:267.5 };   // laptop screen box (16:10)
const TB = { x:30, y:30, w:400, h:300 };     // tablet screen box (4:3)
let clipN = 0;
function laptop(img, overlay, opts={}){
  const id = 'cl' + (clipN++);
  return svgBox('0 0 480 345', `
<defs><clipPath id="${id}"><rect x="${LB.x}" y="${LB.y}" width="${LB.w}" height="${LB.h}"/></clipPath></defs>
<rect x="10" y="10" width="460" height="303" rx="12" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.5"/>
<image href="renders/${img}.png" x="${LB.x}" y="${LB.y}" width="${LB.w}" height="${LB.h}" preserveAspectRatio="none"/>
<g clip-path="url(#${id})">${overlay}</g>
<rect x="${LB.x}" y="${LB.y}" width="${LB.w}" height="${LB.h}" fill="none" stroke="${C.rule}"/>
<path d="M2 313 L478 313 L466 334 L14 334 Z" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.5"/><path d="M200 319 L280 319" stroke="${C.faint}" stroke-width="1.5"/>
${camMark(240, 21, 'A', opts.aOff ? C.faint : C.lime, opts.aNote||'')}
${opts.aOff ? cross(240, 21, C.red, 1.6) : ''}
`, 'scr', 'Screen A, the laptop: perspective view');
}
function tablet(img, overlay, opts={}){
  const id = 'cl' + (clipN++);
  return svgBox('0 0 460 352', `
<defs><clipPath id="${id}"><rect x="${TB.x}" y="${TB.y}" width="${TB.w}" height="${TB.h}"/></clipPath></defs>
<rect x="8" y="8" width="444" height="336" rx="22" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.5"/>
<image href="renders/${img}.png" x="${TB.x}" y="${TB.y}" width="${TB.w}" height="${TB.h}" preserveAspectRatio="none"/>
<g clip-path="url(#${id})">${overlay}</g>
<rect x="${TB.x}" y="${TB.y}" width="${TB.w}" height="${TB.h}" fill="none" stroke="${C.rule}"/>
${camMark(150, 19, 'B', opts.bOff ? C.faint : C.orange, opts.bNote||'')}
${opts.bOff ? cross(150, 19, C.red, 1.6) : ''}
`, 'scr', 'Screen B, the flat tablet: plan view of the bed');
}
// side elevation: person on the left, tablet flat, laptop at the back, frustums A and B, hand at a height
function strip({ handY=52, handX=232, kind='open', aOn=true, bOn=true, handOff=false, note='' }={}){
  const aCol = aOn ? C.lime : C.faint, bCol = bOn ? C.orange : C.faint;
  const handShape = kind==='pinch'
    ? `<path d="M${handX-34} ${handY} q 18 -9 40 -3 l 6 6 q -4 4 -10 1" fill="none" stroke="${C.ink}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${handX+2}" cy="${handY+4}" r="3" fill="${C.lime}"/>`
    : `<path d="M${handX-34} ${handY} q 22 -7 50 0" fill="none" stroke="${C.ink}" stroke-width="6" stroke-linecap="round"/>`;
  return svgBox('0 0 480 128', `
<line x1="0" y1="112" x2="480" y2="112" stroke="${C.rule}" stroke-width="1.5"/>
<path d="M466 24 L150 2 L150 112 Z" fill="${aCol}" opacity="${aOn?.09:.04}" stroke="${aCol}" stroke-width="1" stroke-dasharray="${aOn?'0':'4 3'}"/>
<path d="M300 106 L186 0 L340 0 Z" fill="${bCol}" opacity="${bOn?.11:.04}" stroke="${bCol}" stroke-width="1" stroke-dasharray="${bOn?'0':'4 3'}"/>
<rect x="170" y="106" width="140" height="6" rx="2" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.2"/>
<rect x="352" y="106" width="110" height="6" rx="2" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.2"/>
<path d="M460 106 L472 16" stroke="${C.ink}" stroke-width="4" stroke-linecap="round"/>
<circle cx="466" cy="24" r="4" fill="${aCol}"/><text x="440" y="14" font-size="14" fill="${aCol}" font-family="IBM Plex Mono,monospace">A</text>
<circle cx="300" cy="106" r="4" fill="${bCol}"/><text x="306" y="100" font-size="14" fill="${bCol}" font-family="IBM Plex Mono,monospace">B</text>
<g opacity="${handOff?.45:1}">${handShape}</g>
${handOff?`<text x="${handX-34}" y="${handY-12}" font-size="13" fill="${C.amber}" font-family="IBM Plex Mono,monospace">out of view</text>`:''}
<text x="6" y="16" font-size="13" fill="${C.faint}" font-family="IBM Plex Mono,monospace">side view · person</text>
<text x="6" y="30" font-size="13" fill="${C.faint}" font-family="IBM Plex Mono,monospace">on this side</text>
${note?`<text x="6" y="100" font-size="13" fill="${C.dim}" font-family="IBM Plex Mono,monospace">${note}</text>`:''}
${!aOn?cross(466,40,C.red):''}${!bOn?cross(316,90,C.red):''}
`, 'strip', 'Side view of the two cameras and the hand');
}

// fused-version agreement meter, drawn in the laptop's screen corner
function agree(b, { a=true, bb=true, val='0.94', text } = {}){
  const x = b.x + b.w - 168, y = b.y + 10;
  const bar = (yy, on, col, lab, w) => `<text x="${x+10}" y="${yy+9}" font-size="11" fill="${on?col:C.faint}" font-family="IBM Plex Mono,monospace">${lab}</text><rect x="${x+24}" y="${yy}" width="100" height="10" fill="none" stroke="${C.rule}"/>${on?`<rect x="${x+24}" y="${yy}" width="${w}" height="10" fill="${col}"/>`:`<text x="${x+30}" y="${yy+9}" font-size="10" fill="${C.red}" font-family="IBM Plex Mono,monospace">no hand</text>`}`;
  return `<g><rect x="${x}" y="${y}" width="158" height="62" rx="4" fill="rgba(11,10,9,.85)" stroke="${C.rule}"/>
${bar(y+8, a, C.lime, 'A', 92)}${bar(y+24, bb, C.orange, 'B', 88)}
<text x="${x+10}" y="${y+53}" font-size="11" fill="${a&&bb?C.lime:C.amber}" font-family="IBM Plex Mono,monospace">${text || ('agree ' + val)}</text></g>`;
}
function status(b, text, color, right=false){ return pill(right ? b.x + b.w - 8 : b.x + 8, b.y + 17, text, color, right?'end':'start', false, 13); }

// ---------- overlays per state ----------
const S = { laptopScale: 88, bedScale: 96 };
function ov(state, ver, side){
  const isL = side==='A', img = state.img + (isL ? '-laptop' : '-bed'), b = isL ? LB : TB;
  const sc = isL ? S.laptopScale : S.bedScale;
  const P = k => mapPt(b, an(img, k));
  let o = '';
  const seeA = state.see ? state.see.includes('A') : true, seeB = state.see ? state.see.includes('B') : true;
  const sees = isL ? seeA : seeB;
  const handCol = isL ? C.ink : '#ffd9a8';
  switch(state.id){
    case 'calibrate': {
      const corners = [['c_bl','1'],['c_br','2'],['c_fr','3'],['c_fl','4']];
      corners.forEach(([k,n], i) => {
        const [x,y] = P(k), done = i < 3;
        o += `<circle cx="${x}" cy="${y}" r="${isL?11:13}" fill="none" stroke="${done?C.lime:C.orange}" stroke-width="2"${done?'':' stroke-dasharray="4 3"'}/><circle cx="${x}" cy="${y}" r="2.5" fill="${done?C.lime:C.orange}"/>`;
        const inX = k.endsWith('l') ? 1 : -1, inY = k.includes('_b') ? 1 : -1;
        const lx = x + inX*(isL?22:24), ly = y + inY*(isL?24:28), anc = inX > 0 ? 'start' : 'end';
        const w = 86, x0 = anc==='start' ? lx : lx - w;
        o += `<g font-size="13" font-family="IBM Plex Mono,monospace"><rect x="${x0-4}" y="${ly-14}" width="${w+8}" height="20" rx="4" fill="rgba(11,10,9,.85)"/><text x="${x0}" y="${ly}" fill="${C.ink}">${n}</text><text x="${x0+18}" y="${ly}" fill="${C.lime}">A</text>${tick(x0+38, ly-5, C.lime, .9)}<text x="${x0+52}" y="${ly}" fill="${C.orange}">B</text>${done?tick(x0+72, ly-5, C.orange, .9):`<circle cx="${x0+72}" cy="${ly-5}" r="5" fill="none" stroke="${C.orange}" stroke-dasharray="2 2"/>`}</g>`;
      });
      o += hand('pinch', P('c_fl'), sc*0.8, { color:handCol, rot: isL ? -0.92 : -1.71 });
      if(isL){ o += status(b, 'Calibrate · corner 4 of 4', C.orange); o += pill(b.x + b.w/2, b.y + b.h - 18, 'A has corner 4 · waiting for B', C.orange, 'middle', false, 13); }
      else { o += pill(b.x + b.w/2, b.y + b.h/2 - 14, 'Pinch corner 4 and hold', C.orange, 'middle', false, 14); o += btn(b.x + b.w/2, b.y + b.h/2 + 18, 'Redo', C.dim); }
      break;
    }
    case 'target': {
      o += outline(b, img, 'yellow', C.lime, false, 2.5);
      const [x,y] = P('yellow_top');
      o += hand('open', [x, y - (isL?58:30)], sc, { color:handCol, span: (!isL && ver===1) ? 'span 48 px · high' : '' });
      if(!isL) o += `<circle cx="${P('yellow_top')[0]}" cy="${P('yellow_top')[1]}" r="20" fill="none" stroke="${C.lime}" stroke-width="2" stroke-dasharray="5 4"/>`;
      o += isL ? pill(P('yellow_top')[0], P('yellow_bot')[1] + 26, 'Lift', C.lime, 'middle', true, 15) : pill(P('yellow_top')[0] + 74, P('yellow_top')[1] - 4, 'Lift', C.lime, 'middle', true, 15);
      o += status(b, isL ? (ver===1 ? 'A · plan position' : 'A · left/right + height') : (ver===1 ? 'B · height from hand size' : 'B · left/right + forward/back'), isL?C.lime:C.orange);
      if(isL && ver===2) o += agree(b, {});
      break;
    }
    case 'lift': case 'lostA': case 'lostB': {
      o += outline(b, img, 'land', C.lime, true, 1.8);
      o += dropLine(b, an(img,'yellow_bot'), an(img,'red_land'));
      const [x,y] = P('yellow_top');
      if(sees) o += hand('pinch', [x + (isL?2:0), y - (isL?6:4)], sc, { color:handCol, mirror:isL, span: (!isL && ver===1) ? 'span 71 px → Height · 2' : '' });
      else o += `<text x="${x-70}" y="${y+4}" text-anchor="end" font-size="13" fill="${C.red}" font-family="IBM Plex Mono,monospace">camera ${side} · no hand</text>`;
      if(!isL) o += pill(b.x + 66, b.y + b.h - 22, 'Height · 2', C.lime, 'middle', true, 15);
      if(isL) o += pill(b.x + 52, b.y + b.h - 18, 'Height · 2', C.lime, 'middle', false, 13.5);
      o += btn(b.x + b.w - (isL?50:60), b.y + b.h - (isL?18:22), 'Cancel', C.dim);
      if(state.id==='lift') o += status(b, isL ? (ver===1?'A · over the red 2x4':'A · x 0 mm · height 2') : (ver===1?'B · pinch from below = lift':'B · x 1 mm · over the red 2x4'), isL?C.lime:C.orange);
      if(state.id==='lostA') o += status(b, isL ? 'A lost the hand' : 'B only · plan moves, height held', isL?C.red:C.amber);
      if(state.id==='lostB') o += status(b, isL ? 'A only · height moves, depth held' : 'B lost the hand', isL?C.amber:C.red);
      if(isL && ver===2) o += agree(b, state.id==='lostA' ? { a:false, text:'reduced · B only' } : state.id==='lostB' ? { bb:false, text:'reduced · A only' } : { val:'0.96' });
      break;
    }
    case 'snap': {
      o += outline(b, img, 'yellow', C.lime, false, 2.5);
      const [x,y] = P('yellow_top');
      o += hand('open', [x + (isL?-96:96), y - (isL?20:-30)], sc, { color:handCol, opacity:.55, mirror:isL });
      o += pill(x, isL ? y - 22 : P('yellow_bot')[1] + 44, 'Snapped · level 2', C.lime, 'middle', false, 13.5);
      o += btn(b.x + b.w - (isL?44:52), b.y + b.h - (isL?18:22), 'Undo', C.lime, true);
      o += status(b, isL ? 'Placed · one undo step' : '8 studs locked', C.lime);
      if(isL && ver===2) o += agree(b, { val:'0.97' });
      break;
    }
    case 'paused': {
      const [x,y] = P('yellow_top');
      o += outline(b, img, 'yellow', C.amber, true, 2);
      o += pill(x, y - (isL?22:34), 'Tracking paused', C.amber, 'middle', false, 14);
      o += btn(b.x + b.w/2 - 52, b.y + b.h - (isL?18:24), 'Place', C.lime, true);
      o += btn(b.x + b.w/2 + 52, b.y + b.h - (isL?18:24), 'Cancel', C.dim);
      o += status(b, isL ? 'A · no hand' : 'B · no hand', C.red);
      if(isL && ver===2) o += agree(b, { a:false, bb:false, text:'paused · no camera' });
      break;
    }
    case 'duplicate': {
      o += outline(b, img, 'copy', C.lime, false, 2.5);
      o += outline(b, img, 'copyLand', C.lime, true, 1.5);
      o += dropLine(b, an(img,'copy_bot'), an(img,'copy_land'));
      const [x,y] = P('copy_top');
      if(isL) o += `<text x="${x}" y="${y-56}" text-anchor="middle" font-size="12" fill="${C.dim}" font-family="IBM Plex Mono,monospace">A sees a hand, no V</text>`;
      else o += hand('v', [x, y - 6], sc, { color:handCol });
      o += pill(x + (isL?70:96), y + (isL?8:10), 'Copy', C.lime, 'middle', true, 14);
      o += status(b, isL ? 'Duplicated · held' : 'B · V from below = duplicate', isL?C.lime:C.orange);
      o += btn(b.x + b.w - (isL?50:60), b.y + b.h - (isL?18:22), 'Cancel', C.dim);
      break;
    }
    case 'rotate': {
      o += outline(b, img, 'yellow', C.lime, false, 2.5);
      const [x,y] = P('yellow_top');
      if(isL) o += hand('v', [x + 96, y + 30], sc, { color:handCol });
      else o += `<text x="${x}" y="${y-74}" text-anchor="middle" font-size="12" fill="${C.dim}" font-family="IBM Plex Mono,monospace">B sees a hand, no V</text>`;
      o += `<path d="M${x-34} ${y-(isL?30:52)} a 40 22 0 0 1 68 0" fill="none" stroke="${C.lime}" stroke-width="2"/><path d="M${x+34} ${y-(isL?30:52)} l -9 -3 m 9 3 l 1 -9" stroke="${C.lime}" stroke-width="2" fill="none" stroke-linecap="round"/>`;
      o += pill(x - (isL?0:0), y - (isL?52:72), 'Rotate 90°', C.lime, 'middle', false, 13.5);
      o += status(b, isL ? 'A · two fingers up = rotate' : 'Rotated · held', isL?C.lime:C.orange);
      break;
    }
  }
  return o;
}

// ---------- state cards ----------
function card(ver, st){
  const optsA = { aOff: st.see && !st.see.includes('A') }, optsB = { bOff: st.see && !st.see.includes('B') };
  return `<article class="state" id="v${ver}-${st.id}">
<header><span class="sn">${st.n}</span><h4>${st.title}</h4>${st.chips||''}</header>
<div class="screens"><figure>${laptop(st.img+'-laptop', ov(st, ver, 'A'), optsA)}<figcaption>Screen A · laptop · perspective</figcaption></figure>
<figure>${tablet(st.img+'-bed', ov(st, ver, 'B'), optsB)}<figcaption>Screen B · flat tablet · plan (the bed)</figcaption></figure></div>
<div class="below">${strip(st.strip||{})}<dl><dt class="a">Camera A reads</dt><dd>${st.readA}</dd><dt class="b">Camera B reads</dt><dd>${st.readB}</dd>${st.does?`<dt>Result</dt><dd>${st.does}</dd>`:''}</dl></div>
</article>`;
}

const V1 = [
  { id:'target', n:'1', img:'target', title:'Target', chips: chip('A + B tracking','ok'),
    readA:'An open hand over the left half of the view. Its palm position gives left/right and forward/back. A treats the hand as flat and reads no height.',
    readB:'The wrist to middle-knuckle span is 48 px, which is small, so the hand is high: about 6 bricks above the bed. Nothing is held, so the height only sets how big the cursor ring is.',
    does:'The yellow 2x4 under the hand is outlined on both screens, with "Lift".', strip:{ handY:38, handX:210 } },
  { id:'lift', n:'2', img:'lift', title:'Lift', chips: chip('Holding','ok'),
    readA:'Plan position moves the held brick over the red 2x4.',
    readB:'A pinch seen from below picks up the brick. The span grows to 71 px as the hand comes down, which maps to Height · 2: the brick will land as the second layer.',
    does:'The yellow 2x4 hangs above the red 2x4. A dashed drop line runs to where it will land. Cancel puts it back where it was.', strip:{ handY:58, kind:'pinch' } },
  { id:'snap', n:'3', img:'snap', title:'Snap', chips: chip('Placed','ok'),
    readA:'Plan position matches the red 2x4 to the stud, so the brick lines up.',
    readB:'The hand opens. The last height reading is level 2, so the brick snaps onto the red 2x4.',
    does:'The brick sits on the studs. This is one undo step, and Undo is offered.', strip:{ handY:64 } },
  { id:'paused', n:'4', img:'paused', title:'Paused', chips: chip('Tracking paused','pause'),
    readA:'Nothing. The hand left the laptop view.',
    readB:'Nothing. In this version each camera gives different axes, so if either camera loses the hand the hold pauses.',
    does:'The brick is ghosted where it was. Place puts it at the ghost position; Cancel returns it to where it was picked up. An open hand that comes back does not place it.', see:'', strip:{ handX:96, handY:44, aOn:false, bOn:false, handOff:true } },
  { id:'duplicate', n:'5', img:'duplicate', title:'Gesture · two fingers from below', chips: chip('Copy','ok'),
    readA:'A sees a hand but does not read the V. A only reads plan position in this version.',
    readB:'Two fingers (V) seen from below, under the hand, held 0.3 s: duplicate. The copy appears beside the original, already held.',
    does:'A second yellow 2x4 hangs behind the stack with its own drop line.', strip:{ handY:46 } },
  { id:'rotate', n:'6', img:'rotate', title:'Gesture · two fingers up to A', chips: chip('Rotate','ok'),
    readA:'Two fingers up, facing the laptop, held 0.3 s: rotate the held brick 90 degrees.',
    readB:'The same hand seen from below shows a fist with two fingers pointing away. B does not act on it while A reads it.',
    does:'The held brick turns from 4x2 to 2x4. The old orientation stays as a faint outline until the hand moves.', strip:{ handY:46 } },
];
const V2 = [
  { id:'calibrate', n:'0', img:'calibrate', title:'Calibrate', chips: chip('Corner 4 of 4','warn'),
    readA:'Where the pinch is in A\'s image (x, y in pixels) at each corner. Corner 4: recorded.',
    readB:'Where the pinch is in B\'s image at each corner. Corner 4: still waiting for a steady pinch.',
    does:'When all eight readings are in (4 corners × 2 cameras), the page fits one mapping per camera from image position to bed position, and the shared left/right axis lines the two up.', strip:{ handY:92, handX:192, kind:'pinch' } },
  { id:'target', n:'1', img:'target', title:'Target', chips: chip('A + B agree','ok'),
    readA:'Left/right and height. The hand is about 6 bricks above the bed.',
    readB:'Left/right and forward/back. Left/right from B is within 2 mm of A, so the meter reads "agree".',
    does:'The yellow 2x4 is outlined with "Lift".', strip:{ handY:38, handX:210 } },
  { id:'lift', n:'2', img:'lift', title:'Lift', chips: chip('Holding','ok'),
    readA:'Height falls as the hand comes down: Height · 2.',
    readB:'Forward/back puts the brick over the red 2x4. The pinch from below lifts.',
    does:'Drop line to the landing footprint. Cancel is offered.', strip:{ handY:58, kind:'pinch' } },
  { id:'snap', n:'3', img:'snap', title:'Snap', chips: chip('Placed','ok'),
    readA:'Height reaches the top of the red 2x4.', readB:'The hand opens over the red 2x4.',
    does:'Snapped on the studs as one undo step. Undo is offered.', strip:{ handY:64 } },
  { id:'lostA', n:'4a', img:'lift', title:'Camera A loses the hand', chips: chip('Reduced · B only','warn'),
    readA:'Nothing.', readB:'Left/right and forward/back continue.',
    does:'The brick still moves in plan. Its height is held at the last value from A, and the meter reads "reduced".', see:'B', strip:{ handY:58, kind:'pinch', aOn:false } },
  { id:'lostB', n:'4b', img:'lift', title:'Camera B loses the hand', chips: chip('Reduced · A only','warn'),
    readA:'Left/right and height continue.', readB:'Nothing.',
    does:'The brick still moves left/right and up/down. Forward/back is held at the last value from B.', see:'A', strip:{ handY:58, kind:'pinch', bOn:false } },
  { id:'paused', n:'5', img:'paused', title:'Both cameras lose the hand', chips: chip('Tracking paused','pause'),
    readA:'Nothing.', readB:'Nothing.',
    does:'The action pauses. The brick is ghosted with "Tracking paused", Place and Cancel.', see:'', strip:{ handX:96, handY:44, aOn:false, bOn:false, handOff:true } },
];

// ---------- comparison: the lift state in both versions ----------
function compareCol(ver){
  const st = (ver===1?V1:V2).find(s => s.id==='lift');
  return `<div class="ccol"><h3>${ver===1?'1 · Floor reads depth':'2 · Calibrated camera pair (fused)'}</h3>${laptop('lift-laptop', ov(st, ver, 'A'))}${tablet('lift-bed', ov(st, ver, 'B'))}</div>`;
}

// ---------- calibration flow (line drawings) ----------
function calStep(i){
  const done = i, corners = [[40,30],[200,30],[200,130],[40,130]];
  let g = `<rect x="20" y="12" width="200" height="136" rx="6" fill="${C.panel}" stroke="${C.ink}" stroke-width="1.2"/><rect x="30" y="20" width="180" height="120" fill="none" stroke="${C.rule}"/>`;
  g += `<circle cx="120" cy="10" r="4" fill="${C.orange}"/>`;
  corners.forEach(([x,y],k) => {
    const st = k < done ? 'done' : k===done ? 'now' : 'todo';
    const col = st==='done' ? C.lime : st==='now' ? C.orange : C.faint;
    g += `<circle cx="${x}" cy="${y}" r="9" fill="none" stroke="${col}" stroke-width="1.8"${st==='todo'?' stroke-dasharray="3 3"':''}/><text x="${x}" y="${y+4}" text-anchor="middle" font-size="10" fill="${col}" font-family="IBM Plex Mono,monospace">${k+1}</text>`;
    if(st==='done') g += tick(x + (x<100?18:-30), y, C.lime, .7) + tick(x + (x<100?30:-18), y, C.orange, .7);
  });
  if(done < 4){ const [x,y] = corners[done]; g += hand('pinch', [x + (x<100?6:-6), y + 2], 52, { color:'#ffd9a8' }); }
  else g += `<text x="120" y="84" text-anchor="middle" font-size="13" fill="${C.lime}" font-family="IBM Plex Mono,monospace">fit · 1.8 mm</text>`;
  return svgBox('0 0 240 156', g, 'cal');
}

// ---------- gesture table rows ----------
const GT = [
  ['open','Open, flat palm','Plan position: where the hand sits over the view (version 1). Left/right and height (version 2).','Plan cursor: the hand seen from below gives a ring on the bed. The span gives height in version 1.'],
  ['pinch','Pinch (thumb tip to index tip)','Holds what is already lifted. Used at the corners in calibration.','Lift: a pinch seen from below picks up the brick under the ring.'],
  ['v','Two fingers','Two fingers up, facing the laptop: rotate the held brick 90 degrees.','V seen from below, under the hand: duplicate the brick.'],
  ['open','Hand leaves the view','Version 1: the hold pauses. Version 2: reduced reading from B.','Version 1: the hold pauses. Version 2: reduced reading from A.'],
];

// ---------- onboarding ----------
const OB = [
  ['done','Lay the tablet flat','Put the tablet screen-up between you and the laptop, long side facing you. Its front camera is on the edge nearest the laptop.','The check turns green when B sees the ceiling for 1 s with no hand.','happy'],
  ['done','Show both cameras your hand','Hold an open hand about 20 cm above the tablet. A sees it from the front, B from below.','Green when both A and B report a hand in the same frame.','happy'],
  ['done','Pinch the four corners','Version 2 only. Pinch on each marked corner of the bed and hold until both ticks appear.','Green when all four corners have an A tick and a B tick, and the fit error is under 4 mm.','happy'],
  ['now','Lift the yellow brick','Point at the yellow 2x4 with an open hand. When it is outlined, pinch.','Green when a brick is held for 1 s.','o'],
  ['todo','Snap it on the red brick','Carry it over the red 2x4, bring your hand down until the bed shows Height · 2, then open your hand.','Green when the brick is placed. Undo is shown next to it.','flat'],
];
function obStep([s, title, body, check, mood], i){
  const box = s==='done' ? `<svg class="ck" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="6" fill="${C.lime}" stroke="${C.lime}"/>${tick(14,15,'#111',1.2)}</svg>`
    : s==='now' ? `<svg class="ck" viewBox="0 0 28 28"><rect x="1.5" y="1.5" width="25" height="25" rx="6" fill="none" stroke="${C.orange}" stroke-width="2"/><circle cx="14" cy="14" r="4" fill="${C.orange}"/></svg>`
    : `<svg class="ck" viewBox="0 0 28 28"><rect x="1.5" y="1.5" width="25" height="25" rx="6" fill="none" stroke="${C.faint}" stroke-width="2" stroke-dasharray="4 3"/></svg>`;
  const mascot = i===1||i===3 ? svgBox('0 0 80 70', handMascot(i===3?'pinch':'open', 40, 40, 44, s==='done'?C.lime:C.orange), 'ma') : svgBox('0 0 80 70', butter(10, 18, 1.05, mood), 'ma');
  return `<li class="ob ${s}">${box}<div><h4>${i+1}. ${title}</h4><p>${body}</p><p class="note">${check}</p></div>${mascot}</li>`;
}

// ---------- system overlay labels ----------
function systemFig(){
  const A = AN.system.anchors, W = 1600, H = 1000;
  const p = k => [A[k][0]*W, A[k][1]*H];
  const lab = (k, text, col, dx, dy) => { const [x,y] = p(k); return `<line x1="${x}" y1="${y}" x2="${x+dx}" y2="${y+dy}" stroke="${col}" stroke-width="2"/>${pill(x+dx, y+dy, text, col, dx<0?'end':'start', false, 26)}`; };
  return svgBox(`0 0 ${W} ${H}`, `<image href="renders/system.png" x="0" y="0" width="${W}" height="${H}"/>
${lab('camA','A · laptop webcam, faces you',C.lime,-60,-150)}
${lab('camB','B · tablet front camera, faces up',C.orange,140,40)}
${lab('hand','one hand, 21 landmarks',C.ink,-120,-160)}
${lab('tablet','Screen B · the bed (plan)',C.dim,-80,70)}
${lab('laptop','Screen A · perspective',C.dim,60,90)}`, 'sys', 'Rendered system view: laptop, flat tablet, two camera frustums, and a hand');
}
// side-elevation comparison of the two versions' axes
function axesFig(ver){
  const g = `<line x1="0" y1="150" x2="420" y2="150" stroke="${C.rule}" stroke-width="1.5"/>
<path d="M392 40 L120 10 L120 150 Z" fill="${C.lime}" opacity=".08" stroke="${C.lime}" stroke-width="1"/>
<path d="M250 144 L150 20 L320 20 Z" fill="${C.orange}" opacity=".1" stroke="${C.orange}" stroke-width="1"/>
<rect x="140" y="144" width="130" height="6" rx="2" fill="${C.panel}" stroke="${C.ink}"/>
<rect x="300" y="144" width="100" height="6" rx="2" fill="${C.panel}" stroke="${C.ink}"/><path d="M398 144 L408 34" stroke="${C.ink}" stroke-width="4" stroke-linecap="round"/>
<circle cx="392" cy="40" r="4" fill="${C.lime}"/><circle cx="250" cy="144" r="4" fill="${C.orange}"/>
<path d="M170 82 q 22 -7 50 0" fill="none" stroke="${C.ink}" stroke-width="6" stroke-linecap="round"/>
${ver===1 ? `
<text x="120" y="190" font-size="12" fill="${C.lime}" font-family="IBM Plex Mono,monospace">A → left/right, forward/back</text>
<text x="120" y="208" font-size="12" fill="${C.orange}" font-family="IBM Plex Mono,monospace">B → height, from hand size</text>
<path d="M232 136 L232 96" stroke="${C.orange}" stroke-width="2"/><path d="M226 102 L232 94 L238 102" fill="none" stroke="${C.orange}" stroke-width="2"/>
<text x="10" y="100" font-size="11" fill="${C.dim}" font-family="IBM Plex Mono,monospace">span 0→9</text><text x="10" y="114" font-size="11" fill="${C.dim}" font-family="IBM Plex Mono,monospace">bigger = lower</text>`
: `
<text x="120" y="190" font-size="12" fill="${C.lime}" font-family="IBM Plex Mono,monospace">A → left/right, height</text>
<text x="120" y="208" font-size="12" fill="${C.orange}" font-family="IBM Plex Mono,monospace">B → left/right, forward/back</text>
<text x="10" y="100" font-size="11" fill="${C.dim}" font-family="IBM Plex Mono,monospace">shared axis:</text><text x="10" y="114" font-size="11" fill="${C.dim}" font-family="IBM Plex Mono,monospace">left/right</text>`}`;
  return svgBox('0 0 420 220', g, 'axes', `Side view of version ${ver}`);
}

// ---------- page ----------
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LEGO Two Screens</title>
<meta name="description" content="Wireframes and three.js renders for a LEGO building system with two screens and two hand-tracking cameras: a laptop that shows the set in perspective and a flat tablet that shows it in plan.">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0a09;--panel:#12100e;--ink:#ece6da;--dim:#b3ab9e;--faint:#7a7368;--rule:#2e2a26;--red:#e0483a;--lime:#c4f46a;--amber:#efb94a;--orange:#efa13a}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 "IBM Plex Mono",ui-monospace,Menlo,monospace;overflow-x:hidden}
main{max-width:1180px;margin:0 auto;padding:28px 16px 80px}
a{color:var(--lime)}
h1{font:700 clamp(28px,5vw,44px)/1.1 Fraunces,Georgia,serif;margin:6px 0 10px}
h2{font:400 24px/1.25 Fraunces,Georgia,serif;margin:48px 0 10px;border-top:1px solid var(--rule);padding-top:22px}
h3{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);margin:22px 0 8px;font-weight:500}
h4{font:400 18px/1.3 Fraunces,Georgia,serif;margin:0}
p{max-width:72ch;margin:8px 0}
.lead{font:300 19px/1.45 Fraunces,Georgia,serif;color:#d8d2c6;max-width:64ch}
.kick{font-size:11px;letter-spacing:.16em;color:var(--dim);text-transform:uppercase}
.note{color:var(--faint);font-size:12.5px}
nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0}
nav.toc a{border:1px solid var(--rule);border-radius:4px;padding:8px 12px;text-decoration:none;color:var(--ink);font-size:12.5px;min-height:40px;display:inline-flex;align-items:center}
svg{display:block;width:100%;height:auto;max-width:100%}
figure{margin:0;min-width:0}
figcaption{font-size:12px;color:var(--dim);margin-top:5px}
.wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px;min-width:600px}
th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid var(--rule)}
th{font-weight:500;color:var(--dim);font-size:11px;letter-spacing:.1em;text-transform:uppercase}
td.ic{width:72px}td.ic svg{width:60px}
th.a{color:var(--lime)}th.b{color:var(--orange)}
.hero{display:grid;grid-template-columns:1.6fr 1fr;gap:16px;align-items:start;margin:14px 0}
.mascots{display:flex;gap:12px;align-items:center;border:1px solid var(--rule);border-radius:6px;padding:12px;background:var(--panel)}
.mascots svg{width:96px;flex:none}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--rule);border-radius:999px;padding:2px 10px 2px 4px;font-size:12px;white-space:nowrap}
.chip svg.ci{width:30px;flex:none}.chip svg.ci.h{width:22px}
.chip.ok{border-color:var(--lime);color:var(--lime)}.chip.pause{border-color:var(--amber);color:var(--amber);border-style:dashed}.chip.warn{border-color:var(--orange);color:var(--orange)}
.state{border:1px solid var(--rule);border-radius:8px;padding:14px;margin:16px 0;background:#0e0d0b}
.state header{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.sn{font-size:12px;color:var(--bg);background:var(--ink);border-radius:3px;padding:0 6px;font-weight:500}
.screens{display:grid;grid-template-columns:1.05fr 1fr;gap:14px;align-items:end}
.below{display:grid;grid-template-columns:1fr 1.25fr;gap:16px;margin-top:12px;align-items:start}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px}
dt{color:var(--dim);font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding-top:2px;white-space:nowrap}
dt.a{color:var(--lime)}dt.b{color:var(--orange)}
dd{margin:0}
.versions{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.vcard{border:1px solid var(--rule);border-radius:8px;padding:14px;background:var(--panel);min-width:0}
.vcard ul{padding-left:18px;margin:8px 0}.vcard li{margin:3px 0}
.ccol{display:grid;gap:10px;min-width:0}
.calflow{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.calflow figure{border:1px solid var(--rule);border-radius:6px;padding:8px}
ol.onb{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px;max-width:none}
.ob{display:grid;grid-template-columns:32px 1fr 84px;gap:12px;align-items:start;border:1px solid var(--rule);border-radius:8px;padding:12px;margin:0}
.ob .ck{width:28px}.ob .ma{width:80px}
.ob.done{border-color:#3d4a26}.ob.now{border-color:var(--orange)}.ob.todo{opacity:.8}
.ob p{margin:4px 0}
.br{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.br figure img{width:100%;display:block;border-radius:4px;border:1px solid var(--rule)}
.beauty{margin-top:12px}
.beauty img{width:100%;display:block;border-radius:6px}
ul{padding-left:20px;max-width:80ch}li{margin:4px 0}
code{background:var(--panel);padding:1px 5px;border-radius:3px;font-size:12.5px;word-break:break-word}
@media (max-width:860px){.hero,.versions,.below,.br{grid-template-columns:1fr}.calflow{grid-template-columns:repeat(2,1fr)}}
@media (max-width:640px){.screens{grid-template-columns:1fr}.ob{grid-template-columns:28px 1fr 52px;gap:10px;padding:10px}.ob .ma{width:52px}main{padding:22px 16px 60px}}
</style>
</head>
<body>
<main>
<div class="kick">WAR GAMES · LEGO bed · two screens, two cameras · wireframes · 2 November 2026</div>
<h1>Two screens and two cameras watch one hand build in LEGO</h1>
<p class="lead">A laptop shows a LEGO set in perspective. A tablet lies flat in front of it and shows the same set from above, as the bed you build on. The laptop's webcam sees your hand from the front. The tablet's front camera sees it from below. You build by hand: point at a brick, pinch to lift it, carry it, and open your hand to snap it onto the studs.</p>
<p>This page draws the screens for each step, in two versions that differ in what each camera is trusted to measure. The images inside the screens are three.js renders. The hand skeletons, outlines, drop lines and buttons are drawn on top as SVG.</p>
<nav class="toc"><a href="#setup">Setup</a><a href="#gestures">Gesture spaces</a><a href="#versions">Two versions</a><a href="#v1">Version 1 states</a><a href="#calibration">Calibration</a><a href="#v2">Version 2 states</a><a href="#onboarding">First build</a><a href="#render">Build / Render</a><a href="#method">How it was made</a></nav>

<h2 id="setup">Setup</h2>
<div class="hero">
<figure>${systemFig()}<figcaption>Rendered with three.js. The laptop screen and the tablet show the Lift state. Lime frustum: camera A. Orange frustum: camera B. The hand is drawn as its 21 landmarks.</figcaption></figure>
<div>
<p><b>Screen A</b> is the laptop. Its webcam, camera A, faces you. The laptop shows the set in perspective, as if a camera were looking at it from your side of the table.</p>
<p><b>Screen B</b> is a phone or tablet lying flat between you and the laptop. Its front camera, camera B, faces up at the underside of your hand. The tablet shows the set in plan, top-down. Far on the tablet is toward the laptop.</p>
<p>Both cameras run the same 21-point hand landmark model. Each camera has its own gestures, so one hand shape can mean one thing to A and another to B.</p>
<div class="mascots">${svgBox('0 0 96 70', butter(14,16,1.2,'happy'))}${svgBox('0 0 96 96', handMascot('open', 48, 56, 62))}<p class="note" style="margin:0">Butter and Hand show up on status chips and in the first-build steps. Butter's face shows the tracking state: smiling when tracking, flat when paused, round mouth when something needs attention.</p></div>
<p style="margin-top:12px">${chip('Tracking','ok')} ${chip('Paused','pause')} ${chip('Reduced','warn')}</p>
</div>
</div>

<h2 id="gestures">Gesture spaces: one hand shape, two meanings</h2>
<p>A reads gestures made toward the laptop. B reads gestures made over the tablet, seen from below. When both cameras see a gesture at once, the camera named in the table acts and the other ignores it.</p>
<div class="wrap"><table>
<tr><th></th><th>Hand shape</th><th class="a">Camera A · faces you</th><th class="b">Camera B · faces up</th></tr>
${GT.map(([k,name,a,b],i) => `<tr><td class="ic">${svgBox('0 0 80 90', i===3 ? handMascot(k, 40, 50, 50, C.faint) : handMascot(k, 40, 52, 50))}</td><td>${name}</td><td>${a}</td><td>${b}</td></tr>`).join('')}
</table></div>
<h3>The four gestures as drawn on the screens</h3>
<div class="versions">
<figure>${tablet('target-bed', ov(V1[0], 2, 'B'))}<figcaption>Flat palm seen from the top: hover. The plan cursor ring sits on the yellow 2x4.</figcaption></figure>
<figure>${tablet('lift-bed', ov(V2[2], 2, 'B'))}<figcaption>Pinch seen from below: lift. The bed shows Height · 2.</figcaption></figure>
<figure>${tablet('duplicate-bed', ov(V1[4], 1, 'B'))}<figcaption>V seen by B, under the hand: duplicate. The copy is held.</figcaption></figure>
<figure>${laptop('rotate-laptop', ov(V1[5], 1, 'A'))}<figcaption>Two fingers up seen by A: rotate 90 degrees. The old orientation stays as a faint outline.</figcaption></figure>
</div>

<h2 id="versions">Two versions side by side</h2>
<div class="versions">
<div class="vcard"><h3>1 · Floor reads depth</h3>${axesFig(1)}
<ul><li>The flat screen is the bed.</li><li>B estimates height from the apparent size of the hand: the distance from the wrist (landmark 0) to the middle knuckle (landmark 9). A bigger span means a lower hand. The span is rounded to plates and shown in bricks.</li><li>A assumes a flat hand and reads only plan position: left/right and forward/back, from where the hand sits over the laptop's view.</li><li>No calibration step. The span-to-height table is set for an adult hand.</li><li>Each camera supplies different axes, so losing either camera pauses a hold.</li></ul></div>
<div class="vcard"><h3>2 · Calibrated camera pair (fused)</h3>${axesFig(2)}
<ul><li>A gives left/right and height. B gives left/right and forward/back. Left/right is measured by both, and that shared axis ties the two cameras together.</li><li>Calibration: pinch at the four marked corners of the bed. Both cameras record where they saw each pinch.</li><li>An agreement meter compares the two left/right readings. Within 5 mm reads "agree"; over 15 mm reads "check calibration".</li><li>One camera lost: the other keeps a reduced reading. Both lost: the action pauses.</li></ul></div>
</div>
<h3>The same moment, Lift, in each version</h3>
<div class="versions">${compareCol(1)}${compareCol(2)}</div>
<div class="wrap"><table>
<tr><th>Axis</th><th>1 · Floor reads depth</th><th>2 · Fused</th></tr>
<tr><td>Left/right</td><td>A</td><td>A and B, compared</td></tr>
<tr><td>Forward/back</td><td>A (where the hand sits over the view)</td><td>B</td></tr>
<tr><td>Height</td><td>B, from hand span</td><td>A</td></tr>
<tr><td>Setup</td><td>None</td><td>Four-corner pinch</td></tr>
<tr><td>A loses the hand</td><td>Pause</td><td>B only: plan moves, height held</td></tr>
<tr><td>B loses the hand</td><td>Pause</td><td>A only: left/right and height move, forward/back held</td></tr>
<tr><td>Known weakness</td><td>Tilting the hand changes the span, which reads as a change in height.</td><td>Needs calibration again if the tablet or laptop moves.</td></tr>
</table></div>

<h2 id="v1">Version 1 · Floor reads depth</h2>
<p>Each state is a pair: the laptop on the left, the bed on the right. Under each pair is a side view of the two cameras and the hand. A greyed frustum with a cross means that camera has lost the hand.</p>
${V1.map(s => card(1, s)).join('\n')}

<h2 id="calibration">Calibration flow (version 2)</h2>
<p>The bed shows four corner targets. Pinch on corner 1 and hold still. When A has recorded the pinch, a lime A tick appears; when B has, an orange B tick appears. Then move to the next corner. With eight readings in, the page fits one mapping per camera and reports the fit error. Redo clears all four corners.</p>
<div class="calflow">${[0,1,2,3,4].map(i => `<figure>${calStep(i)}<figcaption>${i<4?`Corner ${i+1}: pinch and hold`:'Done: both cameras mapped'}</figcaption></figure>`).join('')}</div>

<h2 id="v2">Version 2 · Calibrated camera pair (fused)</h2>
<p>The agreement meter sits in the top-right of the laptop screen. Its two bars are how sure each camera is that it sees a hand; the line under them compares the left/right reading from each camera.</p>
${V2.map(s => card(2, s)).join('\n')}

<h2 id="onboarding">First build: five steps</h2>
<p>Each step has a check that turns green when the step is done. This is a description of the screen, not a working page: here the first three steps are shown done, step 4 is in progress, and step 5 is waiting.</p>
<ol class="onb">${OB.map(obStep).join('')}</ol>

<h2 id="render">Build / Render</h2>
<p>The two working views of the finished scene, next to a clean render of the same scene on a light background.</p>
<div class="br">
<figure><img src="renders/snap-laptop.png" alt="Laptop view of the finished scene"><figcaption>Build · Screen A, perspective</figcaption></figure>
<figure><img src="renders/snap-bed.png" alt="Bed view of the finished scene"><figcaption>Build · Screen B, plan</figcaption></figure>
</div>
<figure class="beauty"><img src="renders/beauty.png" alt="Render of the finished LEGO scene on a light background"><figcaption>Render · the yellow 2x4 on the red 2x4, with the rest of the set and the minifigure.</figcaption></figure>

<h2 id="method">How it was made, and limits</h2>
<ul>
<li>The renders are three.js (r160) images made in headless Chromium through Playwright, using SwiftShader for WebGL. The script is in <a href="source/render.html">source/render.html</a> and <a href="source/run.js">source/run.js</a>; the page itself is generated by <a href="source/build.js">source/build.js</a>.</li>
<li>The LEGO is built from primitives at LEGO proportions: stud pitch 8 mm, brick height 9.6 mm, plate 3.2 mm, stud 4.8 mm across and 1.7 mm tall. Bricks are rounded boxes with cylinder studs and a 0.1 mm gap on each side. The baseplate is 16 x 16 studs.</li>
<li>Lighting: a hemisphere light, one directional light with soft shadows, and a weak fill light.</li>
<li>The hand skeletons are drawn, not tracked. They are hand-placed 21-point templates in the MediaPipe landmark order. Their positions come from points projected out of each render (<a href="renders/anchors.json">anchors.json</a>), so outlines, drop lines and the hand line up with the bricks.</li>
<li>The readings in the text (spans in pixels, millimetres, agreement values) are example values for the wireframe, not measurements.</li>
<li>The page has no live 3D view and loads no scripts. It does not connect to WAG Hand Butter.</li>
</ul>
</main>
</body>
</html>
`;
fs.writeFileSync(path.join(OUT, 'index.html'), html);
console.log('wrote', path.join(OUT, 'index.html'), html.length, 'bytes');
