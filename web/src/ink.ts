// Hand-inked geometry: deterministic wobbly borders, pencil roughs and ink blots.
// Everything is seeded so a panel looks the same every time it is drawn.

export type Rng = () => number;

export function rng(seed: number): Rng {
  let a = seed >>> 0 || 0x9e3779b9;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

const r1 = (n: number) => Math.round(n * 10) / 10;
const between = (r: Rng, a: number, b: number) => a + (b - a) * r();

interface Pt {
  x: number;
  y: number;
}

/** One hand-ruled ink line from a to b: overshoots the corners a little and bows slightly. */
function inkLine(r: Rng, a: Pt, b: Pt, overshoot: number, bow: number, jitter: number): string {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const o1 = between(r, -0.4, 1) * overshoot;
  const o2 = between(r, -0.4, 1) * overshoot;
  const sx = a.x - ux * o1 + between(r, -jitter, jitter);
  const sy = a.y - uy * o1 + between(r, -jitter, jitter);
  const ex = b.x + ux * o2 + between(r, -jitter, jitter);
  const ey = b.y + uy * o2 + between(r, -jitter, jitter);
  const t = between(r, 0.35, 0.65);
  const bw = between(r, -bow, bow);
  const cx = a.x + dx * t - uy * bw;
  const cy = a.y + dy * t + ux * bw;
  return `M${r1(sx)} ${r1(sy)}Q${r1(cx)} ${r1(cy)} ${r1(ex)} ${r1(ey)}`;
}

export interface BorderPaths {
  /** heavy outer strokes, one per side */
  main: string;
  /** thinner partial strokes that thicken the line unevenly, like a loaded brush */
  weight: string;
}

/** Inked panel border for a w x h box (local coordinates, 0,0 top-left). */
export function inkBorder(w: number, h: number, seed: number, scale = 1): BorderPaths {
  const r = rng(seed);
  const corners: Pt[] = [
    { x: 0, y: 0 },
    { x: w, y: 0 },
    { x: w, y: h },
    { x: 0, y: h },
  ];
  const over = 3.5 * scale;
  const bow = 1.6 * scale;
  const jit = 0.9 * scale;
  let main = "";
  let weight = "";
  for (let i = 0; i < 4; i++) {
    const a = corners[i];
    const b = corners[(i + 1) % 4];
    main += inkLine(r, a, b, over, bow, jit);
    // a partial second pass, nudged inward, for brush weight variation
    const t0 = between(r, 0, 0.45);
    const t1 = between(r, t0 + 0.25, 1);
    const nx = -(b.y - a.y);
    const ny = b.x - a.x;
    const nl = Math.hypot(nx, ny) || 1;
    const inset = between(r, 1.2, 2.4) * scale;
    const pa = { x: a.x + (b.x - a.x) * t0 + (nx / nl) * inset, y: a.y + (b.y - a.y) * t0 + (ny / nl) * inset };
    const pb = { x: a.x + (b.x - a.x) * t1 + (nx / nl) * inset, y: a.y + (b.y - a.y) * t1 + (ny / nl) * inset };
    weight += inkLine(r, pa, pb, 0, bow * 0.6, jit * 0.5);
  }
  return { main, weight };
}

/** Light blue-pencil rough of a panel that has not been inked yet. */
export function pencilRough(w: number, h: number, seed: number): string {
  const r = rng(seed ^ 0x51ed);
  const corners: Pt[] = [
    { x: 0, y: 0 },
    { x: w, y: 0 },
    { x: w, y: h },
    { x: 0, y: h },
  ];
  let d = "";
  for (let pass = 0; pass < 2; pass++) {
    for (let i = 0; i < 4; i++) {
      d += inkLine(r, corners[i], corners[(i + 1) % 4], 9, 2.4, 2.2);
    }
  }
  return d;
}

/** A wobbly horizontal rule across a 0..w box at height y (for ink dividers). */
export function wobblyRule(w: number, y: number, seed: number, amp = 1.4): string {
  const r = rng(seed);
  const n = Math.max(4, Math.round(w / 80));
  let d = `M0 ${r1(y + between(r, -amp, amp))}`;
  for (let i = 1; i <= n; i++) {
    const x = (w * i) / n;
    const cx = x - w / n / 2;
    d += `Q${r1(cx)} ${r1(y + between(r, -amp, amp) * 1.6)} ${r1(x)} ${r1(y + between(r, -amp, amp))}`;
  }
  return d;
}

// ---------------------------------------------------------------------------
// Ink blots for canvas transitions.

export interface Blot {
  harmonics: { k: number; amp: number; phase: number; speed: number }[];
  tendrils: { angle: number; width: number; reach: number }[];
  drops: { angle: number; dist: number; size: number }[];
}

export function makeBlot(seed: number, splashy = 1): Blot {
  const r = rng(seed);
  const harmonics = [];
  for (let k = 2; k <= 11; k++) {
    harmonics.push({ k, amp: between(r, 0.015, 0.075) / Math.sqrt(k / 2), phase: r() * Math.PI * 2, speed: between(r, -1.2, 1.2) });
  }
  const tendrils = [];
  const nt = 5 + Math.floor(r() * 5);
  for (let i = 0; i < nt; i++) {
    tendrils.push({ angle: r() * Math.PI * 2, width: between(r, 0.035, 0.11), reach: between(r, 0.08, 0.32) * splashy });
  }
  const drops = [];
  const nd = Math.round((14 + r() * 14) * splashy);
  for (let i = 0; i < nd; i++) {
    drops.push({ angle: r() * Math.PI * 2, dist: between(r, 1.04, 1.5), size: between(r, 0.004, 0.022) });
  }
  return { harmonics, tendrils, drops };
}

function angDiff(a: number, b: number): number {
  let d = (a - b) % (Math.PI * 2);
  if (d > Math.PI) d -= Math.PI * 2;
  if (d < -Math.PI) d += Math.PI * 2;
  return d;
}

export function blotRadius(b: Blot, theta: number, time: number): number {
  let f = 1;
  for (const h of b.harmonics) f += h.amp * Math.sin(h.k * theta + h.phase + time * h.speed);
  for (const t of b.tendrils) {
    const d = angDiff(theta, t.angle) / t.width;
    f += t.reach * Math.exp(-d * d);
  }
  return Math.max(0.2, f);
}

/** Trace a closed, smooth blot outline into the current canvas path. */
export function traceBlot(ctx: CanvasRenderingContext2D, b: Blot, cx: number, cy: number, R: number, time = 0, steps = 120): void {
  const pts: Pt[] = [];
  for (let i = 0; i < steps; i++) {
    const th = (i / steps) * Math.PI * 2;
    const rr = R * blotRadius(b, th, time);
    pts.push({ x: cx + Math.cos(th) * rr, y: cy + Math.sin(th) * rr });
  }
  const mid = (p: Pt, q: Pt) => ({ x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 });
  const m0 = mid(pts[steps - 1], pts[0]);
  ctx.moveTo(m0.x, m0.y);
  for (let i = 0; i < steps; i++) {
    const p = pts[i];
    const m = mid(p, pts[(i + 1) % steps]);
    ctx.quadraticCurveTo(p.x, p.y, m.x, m.y);
  }
  ctx.closePath();
}

/** The same blot as an SVG path string (for static ink splats in the page chrome). */
export function blotPath(b: Blot, cx: number, cy: number, R: number, steps = 96, drops = true): string {
  const pts: Pt[] = [];
  for (let i = 0; i < steps; i++) {
    const th = (i / steps) * Math.PI * 2;
    const rr = R * blotRadius(b, th, 0);
    pts.push({ x: cx + Math.cos(th) * rr, y: cy + Math.sin(th) * rr });
  }
  const mid = (p: Pt, q: Pt) => ({ x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 });
  const m0 = mid(pts[steps - 1], pts[0]);
  let d = `M${r1(m0.x)} ${r1(m0.y)}`;
  for (let i = 0; i < steps; i++) {
    const m = mid(pts[i], pts[(i + 1) % steps]);
    d += `Q${r1(pts[i].x)} ${r1(pts[i].y)} ${r1(m.x)} ${r1(m.y)}`;
  }
  d += "Z";
  if (drops) {
    for (const dr of b.drops) {
      const s = dr.size * R * 2.2;
      const x = cx + Math.cos(dr.angle) * R * dr.dist * 1.08;
      const y = cy + Math.sin(dr.angle) * R * dr.dist * 1.08;
      d += `M${r1(x - s)} ${r1(y)}a${r1(s)} ${r1(s)} 0 1 0 ${r1(s * 2)} 0a${r1(s)} ${r1(s)} 0 1 0 ${r1(-s * 2)} 0Z`;
    }
  }
  return d;
}

export function traceDrops(ctx: CanvasRenderingContext2D, b: Blot, cx: number, cy: number, R: number, scale: number, grow: number): void {
  for (const d of b.drops) {
    const s = d.size * scale * Math.min(1, grow * 1.4);
    if (s <= 0.3) continue;
    const x = cx + Math.cos(d.angle) * R * d.dist;
    const y = cy + Math.sin(d.angle) * R * d.dist;
    ctx.moveTo(x + s, y);
    ctx.arc(x, y, s, 0, Math.PI * 2);
  }
}

export const easeInCubic = (t: number) => t * t * t;
export const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
export const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export const SVG_NS = "http://www.w3.org/2000/svg";

export function svgEl<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}
