// linetype-text.js
// Draws [phrase]{.linetype-text data-linetype="dashed"} in a ggplot linetype,
// in the surrounding text's own font, on its own baseline.
//
// Attributes:
//   data-linetype: solid|dashed|dotted|dotdash|longdash|twodash
//   data-lty: a ggplot/R hex pattern such as "44" (overrides data-linetype)
//   data-ghost: opacity of the faint underlying text (default per linetype)
//   data-stroke-width: stroke width in em (default --ltx-stroke-width-em)
//   data-dash-scale: multiplies every dash and gap (default --ltx-dash-scale)
//   data-color: stroke and text color (default: the surrounding color)
//
// How: the phrase is drawn on a canvas in the computed font, the glyph pixels
// are thinned to a one-pixel skeleton (Zhang-Suen), and the skeleton is traced
// into polylines. Those are stroked in SVG with the linetype's dash pattern,
// over the real text at low opacity. The SVG is placed by a zero-height probe
// whose top is the browser's own alphabetic baseline, so the stroke and the
// text share one baseline whatever the font's metrics.
//
// Dash patterns are ggplot's: each hex digit is a length in line widths,
// alternating on and off, so dashes scale with the stroke width. Caps are
// butt, ggplot's default.

(function() {
  'use strict';

  const NAMED = {
    solid: null,
    dashed: '44',
    dotted: '13',
    dotdash: '1343',
    longdash: '73',
    twodash: '2262'
  };

  // Canvas pixels per CSS pixel. Higher gives smoother skeletons.
  const SCALE = 3;

  function thin(a, w, h) { // Zhang-Suen binary image thinning
    let changed = true, passes = 0;
    const nb = (i) => [i - w, i - w + 1, i + 1, i + w + 1, i + w, i + w - 1, i - 1, i - w - 1];
    while (changed && passes++ < 100) {
      changed = false;
      for (let stage = 0; stage < 2; stage++) {
        const del = [];
        for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
          const i = y * w + x;
          if (!a[i]) continue;
          const p = nb(i).map(v => a[v] || 0);
          const count = p.reduce((q, v) => q + v, 0);
          if (count < 2 || count > 6) continue;
          let transitions = 0;
          for (let j = 0; j < 8; j++) if (!p[j] && p[(j + 1) % 8]) transitions++;
          if (transitions !== 1) continue;
          if (stage === 0) { if (p[0] * p[2] * p[4] || p[2] * p[4] * p[6]) continue; }
          else if (p[0] * p[2] * p[6] || p[0] * p[4] * p[6]) continue;
          del.push(i);
        }
        if (del.length) { changed = true; for (const i of del) a[i] = 0; }
      }
    }
    return a;
  }

  // Trace the 8-connected skeleton as polylines, consuming each edge once.
  function trace(a, w, h) {
    // m-adjacency: a diagonal neighbour already reached through a shared side
    // neighbour is not adjacent. Otherwise every staircase corner reads as a
    // three-way junction and a plain curve shatters into pieces.
    const set = j => j >= 0 && j < a.length && a[j];
    const adjacent = i => {
      const x = i % w, out = [];
      for (const d of [-w, 1, w, -1]) {
        const j = i + d;
        if (set(j) && Math.abs(j % w - x) <= 1) out.push(j);
      }
      for (const [dx, dy] of [[1, -1], [1, 1], [-1, 1], [-1, -1]]) {
        if (x + dx < 0 || x + dx >= w) continue;
        const j = i + dy * w + dx;
        if (set(j) && !set(i + dx) && !set(i + dy * w)) out.push(j);
      }
      return out;
    };
    const pix = [];
    for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) if (a[y * w + x]) pix.push(y * w + x);
    const visited = new Set(), edge = (i, j) => i < j ? i + ',' + j : j + ',' + i;
    const paths = [];
    function follow(start, next) {
      const nodes = [start, next];
      visited.add(edge(start, next));
      let prev = start, at = next;
      for (let steps = 0; steps < 25000; steps++) {
        const choices = adjacent(at).filter(n => n !== prev && !visited.has(edge(at, n)));
        if (choices.length !== 1) break;
        const to = choices[0];
        visited.add(edge(at, to)); nodes.push(to); prev = at; at = to;
      }
      return nodes;
    }
    for (const i of pix) {
      const n = adjacent(i);
      if (n.length !== 2) for (const j of n) if (!visited.has(edge(i, j))) paths.push(follow(i, j));
    }
    for (const i of pix) for (const j of adjacent(i)) if (!visited.has(edge(i, j))) paths.push(follow(i, j));
    return paths.filter(p => p.length > 1).map(p => p.map(i => [i % w, Math.floor(i / w)]));
  }

  // Join the skeleton's pieces into long strokes, the way a pen draws them.
  // Tracing stops at every junction, so a letter arrives as many short
  // pieces, and a dash pattern restarts at the start of each piece: the
  // rhythm would reset at random inside every letter. Here pieces meeting at
  // a junction are paired off straightest-first and chained, so the pattern
  // runs evenly along each whole stroke. Short spurs that thinning leaves at
  // junctions are pruned first; they would show as stray dots.
  function strokes(pieces, spur) {
    const len = p => { let l = 0; for (let k = 1; k < p.length; k++) l += Math.hypot(p[k][0] - p[k - 1][0], p[k][1] - p[k - 1][1]); return l; };
    // Endpoints within a pixel or two are one junction.
    const nodeOf = (() => {
      const nodes = [];
      return (pt) => {
        for (let n = 0; n < nodes.length; n++) {
          if (Math.abs(nodes[n][0] - pt[0]) <= 2 && Math.abs(nodes[n][1] - pt[1]) <= 2) return n;
        }
        nodes.push(pt);
        return nodes.length - 1;
      };
    })();
    let live = pieces.map(p => ({ pts: p, ends: [nodeOf(p[0]), nodeOf(p[p.length - 1])], len: len(p) }));
    const degrees = () => {
      const d = new Map();
      for (const pc of live) for (const n of pc.ends) d.set(n, (d.get(n) || 0) + 1);
      return d;
    };
    for (let round = 0; round < 2; round++) {
      const d = degrees();
      live = live.filter(pc => !(pc.len < spur && pc.ends[0] !== pc.ends[1] &&
        ((d.get(pc.ends[0]) === 1 && d.get(pc.ends[1]) >= 3) || (d.get(pc.ends[1]) === 1 && d.get(pc.ends[0]) >= 3))));
    }
    // Outward direction of a piece at one of its ends, a few pixels in.
    const dir = (pc, end) => {
      const p = pc.pts, k = Math.min(p.length - 1, 6);
      const [a, b] = end === 0 ? [p[0], p[k]] : [p[p.length - 1], p[p.length - 1 - k]];
      const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return [(b[0] - a[0]) / l, (b[1] - a[1]) / l];
    };
    // At each junction pair the incident ends straightest-first.
    const link = new Map(); // "piece:end" -> [piece, end]
    const atNode = new Map();
    live.forEach((pc, i) => pc.ends.forEach((n, e) => {
      if (!atNode.has(n)) atNode.set(n, []);
      atNode.get(n).push([i, e]);
    }));
    for (const ends of atNode.values()) {
      const pairs = [];
      for (let x = 0; x < ends.length; x++) for (let y = x + 1; y < ends.length; y++) {
        if (ends[x][0] === ends[y][0]) continue;
        const u = dir(live[ends[x][0]], ends[x][1]), v = dir(live[ends[y][0]], ends[y][1]);
        pairs.push([-(u[0] * v[0] + u[1] * v[1]), x, y]);
      }
      pairs.sort((a, b) => b[0] - a[0]);
      const used = new Set();
      for (const [, x, y] of pairs) {
        if (used.has(x) || used.has(y)) continue;
        used.add(x); used.add(y);
        link.set(ends[x].join(':'), ends[y]);
        link.set(ends[y].join(':'), ends[x]);
      }
    }
    // Chain linked pieces into strokes, starting from free ends, then loops.
    const done = new Set(), out = [];
    const walk = (i, entryEnd) => {
      const stroke = [];
      while (i !== undefined && !done.has(i)) {
        done.add(i);
        const p = entryEnd === 0 ? live[i].pts : live[i].pts.slice().reverse();
        stroke.push(...(stroke.length ? p.slice(1) : p));
        const next = link.get(i + ':' + (1 - entryEnd));
        if (!next) break;
        [i, entryEnd] = next;
      }
      return stroke;
    };
    live.forEach((pc, i) => [0, 1].forEach(e => {
      if (!done.has(i) && !link.has(i + ':' + e)) out.push(walk(i, e));
    }));
    live.forEach((pc, i) => { if (!done.has(i)) out.push(walk(i, 0)); });
    return out.filter(s => s.length > 1);
  }

  // 8-connected components of the glyph pixels: label per pixel (0 = none)
  // and each component's bounding box.
  function components(a, w, h) {
    const label = new Int32Array(a.length), boxes = [null];
    const stack = [];
    for (let start = 0; start < a.length; start++) {
      if (!a[start] || label[start]) continue;
      const id = boxes.length, box = [w, h, 0, 0];
      label[start] = id; stack.push(start);
      while (stack.length) {
        const i = stack.pop(), x = i % w, y = (i - x) / w;
        if (x < box[0]) box[0] = x; if (y < box[1]) box[1] = y;
        if (x > box[2]) box[2] = x; if (y > box[3]) box[3] = y;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = x + dx, ny = y + dy;
          if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
          const j = ny * w + nx;
          if (a[j] && !label[j]) { label[j] = id; stack.push(j); }
        }
      }
      boxes.push(box);
    }
    return { label, boxes };
  }

  // Ramer-Douglas-Peucker. A pixel staircase is longer than the stroke it
  // approximates, which would stretch the dash spacing along diagonals.
  function simplify(points, eps) {
    if (points.length < 3) return points;
    const [ax, ay] = points[0], [bx, by] = points[points.length - 1];
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy);
    let worst = 0, at = 0;
    for (let k = 1; k < points.length - 1; k++) {
      // A closed stroke starts where it ends: measure from that point.
      const d = len < 1e-9
        ? Math.hypot(points[k][0] - ax, points[k][1] - ay)
        : Math.abs(dy * points[k][0] - dx * points[k][1] + bx * ay - by * ax) / len;
      if (d > worst) { worst = d; at = k; }
    }
    if (worst <= eps) return [points[0], points[points.length - 1]];
    return simplify(points.slice(0, at + 1), eps).slice(0, -1).concat(simplify(points.slice(at), eps));
  }

  function cssNumber(el, name, fallback) {
    const v = parseFloat(getComputedStyle(el).getPropertyValue(name));
    return Number.isFinite(v) ? v : fallback;
  }

  function resolve(span) {
    const named = (span.dataset.linetype || 'dashed').trim();
    const lty = span.dataset.lty ? span.dataset.lty.trim() : NAMED[named];
    const kind = span.dataset.lty ? 'custom' : (named in NAMED ? named : 'custom');
    return { lty, kind };
  }

  function render(span) {
    // Not laid out (a hidden slide, a collapsed callout): nothing to measure.
    // It stays plain text until shown.
    if (!span.getClientRects().length) return;
    const value = span.dataset.ltxText || span.textContent;
    span.dataset.ltxText = value;
    if (span.dataset.color) span.style.color = span.dataset.color;
    span.innerHTML = '';
    const ghost = document.createElement('span');
    ghost.className = 'ltx-ghost';
    ghost.textContent = value;
    const probe = document.createElement('span');
    probe.className = 'ltx-probe';
    probe.setAttribute('aria-hidden', 'true');
    span.append(ghost, probe);

    const { lty, kind } = resolve(span);
    // Solid is just the text: no ghost, no overlay.
    if (!lty) { span.classList.remove('ltx-rendered'); return; }
    const ghostAlpha = span.dataset.ghost !== undefined
      ? parseFloat(span.dataset.ghost)
      : cssNumber(span, '--ltx-ghost-' + kind, 0.2);
    span.style.setProperty('--ltx-ghost', String(ghostAlpha));
    span.classList.add('ltx-rendered');

    const cs = getComputedStyle(span);
    const fs = parseFloat(cs.fontSize), pad = 3;
    const strokeEm = span.dataset.strokeWidth !== undefined
      ? parseFloat(span.dataset.strokeWidth)
      : cssNumber(span, '--ltx-stroke-width-em', 0.075);
    const dashScale = span.dataset.dashScale !== undefined
      ? parseFloat(span.dataset.dashScale)
      : cssNumber(span, '--ltx-dash-scale', 0.7);
    const lw = fs * strokeEm * SCALE; // stroke width, canvas pixels

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const font = `${cs.fontStyle} ${cs.fontWeight} ${fs * SCALE}px ${cs.fontFamily}`;
    ctx.font = font;
    if (cs.letterSpacing && cs.letterSpacing !== 'normal') ctx.letterSpacing = parseFloat(cs.letterSpacing) * SCALE + 'px';
    const m = ctx.measureText(value);
    const ascent = Math.ceil(Math.max(m.actualBoundingBoxAscent || fs * SCALE, fs * SCALE * 0.85));
    const descent = Math.ceil(Math.max(m.actualBoundingBoxDescent || fs * SCALE * 0.25, fs * SCALE * 0.3));
    const width = Math.ceil(m.width + pad * 2 * SCALE), height = ascent + descent + pad * 2 * SCALE;
    canvas.width = width; canvas.height = height;
    ctx.font = font;
    if (cs.letterSpacing && cs.letterSpacing !== 'normal') ctx.letterSpacing = parseFloat(cs.letterSpacing) * SCALE + 'px';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#000';
    const baseline = ascent + pad * SCALE;
    ctx.fillText(value, pad * SCALE, baseline);
    const rgba = ctx.getImageData(0, 0, width, height).data;
    const binary = new Uint8Array(width * height);
    for (let i = 0; i < binary.length; i++) binary[i] = rgba[i * 4 + 3] > 110 ? 1 : 0;
    const { label, boxes } = components(binary, width, height);
    thin(binary, width, height);
    const polylines = strokes(trace(binary, width, height), 1.5 * lw).map(p => simplify(p, 0.25 * SCALE));
    // Thinning erases a small blob (an i's dot) outright, or leaves a stub
    // shorter than the stroke is wide, which butt caps would not show. Such a
    // component is drawn as a dot at its centre, one line width long.
    const kept = new Int32Array(boxes.length);
    for (let i = 0; i < binary.length; i++) if (binary[i]) kept[label[i]]++;
    for (let id = 1; id < boxes.length; id++) {
      if (kept[id] * 1.0 >= lw) continue;
      const [x0, y0, x1, y1] = boxes[id];
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      polylines.push([[cx - lw / 2, cy], [cx + lw / 2, cy]]);
    }
    const d = polylines
      .map(p => p.map(([x, y], k) => (k ? 'L' : 'M') + x + ' ' + y).join(' '))
      .join(' ');

    // The probe's top is the real alphabetic baseline of the ghost text.
    // Rects are in viewport pixels, which a scaled slide shrinks or grows;
    // divide by that scale to get the span's own CSS pixels.
    const spanRect = span.getBoundingClientRect();
    const scale = spanRect.height / span.offsetHeight || 1;
    const baselineCss = (probe.getBoundingClientRect().top - spanRect.top) / scale;

    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.style.width = (width / SCALE) + 'px';
    svg.style.height = (height / SCALE) + 'px';
    svg.style.left = -pad + 'px';
    svg.style.top = (baselineCss - baseline / SCALE) + 'px';
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', d);
    path.setAttribute('stroke-width', String(lw));
    path.setAttribute('stroke-linecap', 'butt');
    if (lty) {
      path.setAttribute('stroke-dasharray',
        lty.split('').map(ch => parseInt(ch, 16) * lw * dashScale).join(' '));
    }
    // The faint letters are drawn in the same SVG, from the same baseline
    // coordinate as the skeleton, so the two cannot drift apart. The DOM text
    // underneath stays for selection, search and screen readers, unseen.
    const text = document.createElementNS(NS, 'text');
    text.setAttribute('x', String(pad * SCALE));
    text.setAttribute('y', String(baseline));
    text.setAttribute('class', 'ltx-ghost-glyphs');
    text.style.font = font;
    if (cs.letterSpacing && cs.letterSpacing !== 'normal') text.style.letterSpacing = parseFloat(cs.letterSpacing) * SCALE + 'px';
    text.style.whiteSpace = 'pre';
    text.textContent = value;
    svg.append(text, path);
    span.appendChild(svg);
  }

  function renderAll() {
    document.querySelectorAll('.linetype-text').forEach(span => {
      try { render(span); } catch (e) {
        // Leave the phrase as plain text rather than break the sentence.
        span.classList.remove('ltx-rendered');
        console.warn('linetype-text: could not render', span.dataset.ltxText, e);
      }
    });
  }

  let frame = 0;
  function start() {
    if (!document.querySelector('.linetype-text')) return;
    document.fonts.ready.then(renderAll);
    const later = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(renderAll);
    };
    window.addEventListener('resize', later);
    // In a reveal deck, phrases on slides not yet shown cannot be measured.
    if (window.Reveal && window.Reveal.on) {
      window.Reveal.on('ready', later);
      window.Reveal.on('slidechanged', later);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
