// Comic lettering: narration caption boxes and off-panel speech balloons.
import { hash, rng, svgEl, type Rng } from "./ink";
import type { Rect } from "./layout";

export type Side = "left" | "right";

export interface LineSpec {
  speaker: string;
  text: string;
  side: Side;
  showSpeaker: boolean;
}

export interface LetterSpec {
  caption?: string;
  lines: LineSpec[];
  /** panel size in px */
  w: number;
  h: number;
  seed: number;
}

const DEVICE = /\b(radio|phone|telephone|tv|television|speaker|intercom|tannoy|pa|loudspeaker|walkie|comms|computer|ai|answering machine|voicemail)\b/i;

export function isDevice(speaker: string): boolean {
  return DEVICE.test(speaker);
}

/** Lettering size for a panel of width w, nudged down when there is a lot to say. */
export function letterSize(w: number, h: number, chars: number): number {
  let px = Math.min(Math.max(w * 0.03, 13.5), 24);
  // short panels need smaller type or the art disappears behind words
  px = Math.min(px, Math.max(13.5, h * 0.075));
  if (chars > 90) px *= 0.94;
  if (chars > 150) px *= 0.92;
  return Math.max(12.5, Math.round(px * 10) / 10);
}

const overlaps = (a: Rect, b: Rect, pad = 6) => a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;

/**
 * Build the lettering layer for one panel. Returns elements positioned in panel space;
 * call after the container is attached (balloons are measured to fit their text).
 */
export function letterPanel(layer: HTMLElement, spec: LetterSpec, lt: number): HTMLElement[] {
  const out: HTMLElement[] = [];
  const r = rng(spec.seed);
  const margin = Math.max(8, Math.min(spec.w, spec.h) * 0.045);
  const placed: Rect[] = [];

  if (spec.caption) {
    const cap = document.createElement("div");
    cap.className = "caption";
    const rot = (r() - 0.5) * 2.4;
    cap.style.setProperty("--rot", `${rot.toFixed(2)}deg`);
    cap.style.left = `${Math.round(margin * 0.55)}px`;
    cap.style.top = `${Math.round(margin * 0.55)}px`;
    cap.style.maxWidth = `${Math.round(spec.w * (spec.w < 420 ? 0.74 : 0.56))}px`;
    const text = document.createElement("span");
    text.className = "caption-text";
    text.textContent = spec.caption;
    cap.append(text);
    layer.append(cap);
    placed.push({ x: cap.offsetLeft, y: cap.offsetTop, w: cap.offsetWidth, h: cap.offsetHeight });
    out.push(cap);
  }

  // reading order: each balloon starts lower than the one before it, whichever side it is on
  let minY = 0;
  for (const line of spec.lines) {
    const el = balloon(layer, line, spec, lt, margin, placed, r, minY);
    out.push(el);
    const last = placed[placed.length - 1];
    minY = last.y + last.h * 0.62;
  }
  return out;
}

function balloon(layer: HTMLElement, line: LineSpec, spec: LetterSpec, lt: number, margin: number, placed: Rect[], r: Rng, minY: number): HTMLElement {
  const device = isDevice(line.speaker);
  const el = document.createElement("div");
  el.className = `balloon${device ? " balloon--device" : ""}`;
  const text = document.createElement("div");
  text.className = "balloon-text";
  if (line.showSpeaker && line.speaker) {
    const who = document.createElement("span");
    who.className = "balloon-speaker";
    who.textContent = line.speaker;
    text.append(who);
  }
  const say = document.createElement("span");
  say.className = "balloon-say";
  say.textContent = line.text;
  text.append(say);
  // pick a pleasant text block shape (~2.3:1) before wrapping, capped by the panel
  const chars = line.text.length + (line.showSpeaker ? 4 : 0);
  // uppercase hand lettering runs ~0.6em per glyph; aim for a ~2.6:1 block
  const areaEm = chars * 0.6 * 1.12;
  const idealEm = Math.sqrt(areaEm * 2.6);
  const maxPx = spec.w * (spec.w < 420 ? 0.64 : spec.w < 640 ? 0.54 : 0.44);
  const widthPx = Math.min(maxPx, Math.max(6.5 * lt, idealEm * lt));
  text.style.width = `${Math.round(widthPx)}px`;
  el.append(text);
  layer.append(el);

  const tw = text.offsetWidth;
  const th = text.offsetHeight;
  const pad = lt * 0.5;
  const k = device ? 1.3 : 1.24;
  const a = (tw / 2) * k + pad;
  const b = (th / 2) * k + pad * 0.75;
  const bw = a * 2;
  const bh = b * 2;
  const tailRoom = Math.max(margin, lt * 1.6);

  let x = line.side === "right" ? spec.w - bw - tailRoom : tailRoom;
  x = Math.max(4, Math.min(spec.w - bw - 4, x));
  let y = Math.max(margin * 0.7, minY);
  for (let guard = 0; guard < 8; guard++) {
    const box = { x, y, w: bw, h: bh };
    const hit = placed.find((p) => overlaps(p, box));
    if (!hit) break;
    y = hit.y + hit.h + lt * 0.5;
  }
  if (y + bh > spec.h - 4) y = Math.max(4, spec.h - bh - 4);
  placed.push({ x, y, w: bw, h: bh });

  el.style.left = `${Math.round(x)}px`;
  el.style.top = `${Math.round(y)}px`;
  el.style.width = `${Math.round(bw)}px`;
  el.style.height = `${Math.round(bh)}px`;
  text.style.left = `${Math.round(a - tw / 2)}px`;
  text.style.top = `${Math.round(b - th / 2)}px`;

  // tail points off-panel, toward the edge the speaker stands behind
  const tipX = line.side === "right" ? spec.w + lt * 0.7 - x : -lt * 0.7 - x;
  const tipY = Math.min(spec.h - y - 6, b + b * (0.55 + r() * 0.35));
  el.style.transformOrigin = `${line.side === "right" ? "100%" : "0%"} 60%`;

  const svg = svgEl("svg", { class: "balloon-shape", width: Math.ceil(bw), height: Math.ceil(bh), "aria-hidden": "true" });
  const seed = spec.seed ^ hash(line.text);
  const shape = device ? electricShape(a, b, seed) : roundShape(a, b, seed);
  const tail = device ? electricTail(a, b, tipX, tipY, lt, seed) : smoothTail(a, b, tipX, tipY, lt, seed);
  const sw = Math.max(1.8, lt * 0.15);
  const ink = svgEl("g", { class: "balloon-ink", "stroke-width": (sw * 2).toFixed(2) });
  const tailAttrs: Record<string, string> = { d: tail.outline };
  if (!tail.fill) {
    tailAttrs.fill = "none";
    tailAttrs["stroke-width"] = (sw * 1.15).toFixed(2);
  }
  ink.append(svgEl("path", { d: shape }), svgEl("path", tailAttrs));
  const fill = svgEl("g", { class: "balloon-fill" });
  fill.append(svgEl("path", { d: shape }));
  if (tail.fill) fill.append(svgEl("path", { d: tail.fill }));
  svg.append(ink, fill);
  el.prepend(svg);
  return el;
}

// Superellipse hugging the text, with a slight hand wobble.
function superPoint(a: number, b: number, th: number, n = 2.6) {
  const c = Math.cos(th);
  const s = Math.sin(th);
  return {
    x: a + a * Math.sign(c) * Math.pow(Math.abs(c), 2 / n),
    y: b + b * Math.sign(s) * Math.pow(Math.abs(s), 2 / n),
  };
}

function roundShape(a: number, b: number, seed: number): string {
  const r = rng(seed);
  const steps = 40;
  const ph = r() * 6.28;
  const pts = [];
  for (let i = 0; i < steps; i++) {
    const th = (i / steps) * Math.PI * 2;
    const p = superPoint(a, b, th);
    const wob = 1 + Math.sin(th * 3 + ph) * 0.012 + (r() - 0.5) * 0.01;
    pts.push({ x: a + (p.x - a) * wob, y: b + (p.y - b) * wob });
  }
  return smoothClosed(pts);
}

function electricShape(a: number, b: number, seed: number): string {
  const r = rng(seed);
  const perim = Math.PI * (a + b);
  const spikes = Math.max(14, Math.round(perim / 16));
  let d = "";
  for (let i = 0; i < spikes * 2; i++) {
    const th = (i / (spikes * 2)) * Math.PI * 2;
    const p = superPoint(a, b, th, 2.4);
    const f = i % 2 === 0 ? 1 + 0.04 + r() * 0.03 : 0.9 + r() * 0.02;
    const x = a + (p.x - a) * f;
    const y = b + (p.y - b) * f;
    d += `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  return d + "Z";
}

function smoothClosed(pts: { x: number; y: number }[]): string {
  const n = pts.length;
  const mid = (i: number) => ({ x: (pts[i].x + pts[(i + 1) % n].x) / 2, y: (pts[i].y + pts[(i + 1) % n].y) / 2 });
  const m0 = mid(n - 1);
  let d = `M${m0.x.toFixed(1)} ${m0.y.toFixed(1)}`;
  for (let i = 0; i < n; i++) {
    const m = mid(i);
    d += `Q${pts[i].x.toFixed(1)} ${pts[i].y.toFixed(1)} ${m.x.toFixed(1)} ${m.y.toFixed(1)}`;
  }
  return d + "Z";
}

function boundaryToward(a: number, b: number, tx: number, ty: number) {
  // find the superellipse point whose direction from centre matches the tip direction
  const target = Math.atan2(ty - b, tx - a);
  let best = 0;
  let bestD = Infinity;
  for (let i = 0; i < 180; i++) {
    const th = (i / 180) * Math.PI * 2;
    const p = superPoint(a, b, th);
    const d = Math.abs(Math.atan2(Math.sin(Math.atan2(p.y - b, p.x - a) - target), Math.cos(Math.atan2(p.y - b, p.x - a) - target)));
    if (d < bestD) {
      bestD = d;
      best = th;
    }
  }
  return best;
}

function smoothTail(a: number, b: number, tx: number, ty: number, lt: number, seed: number): { outline: string; fill: string } {
  const r = rng(seed ^ 0x7a11);
  const th = boundaryToward(a, b, tx, ty);
  const spread = Math.min(0.42, (lt * 1.1) / Math.max(a, b));
  const p1 = superPoint(a, b, th - spread);
  const p2 = superPoint(a, b, th + spread);
  // pull the base slightly inside so the seam is buried under the balloon fill
  const inset = (p: { x: number; y: number }) => ({ x: a + (p.x - a) * 0.9, y: b + (p.y - b) * 0.9 });
  const q1 = inset(p1);
  const q2 = inset(p2);
  const bend = (r() - 0.5) * lt * 1.2;
  const mx = (q1.x + q2.x) / 2;
  const my = (q1.y + q2.y) / 2;
  const dx = tx - mx;
  const dy = ty - my;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const c1x = q1.x + dx * 0.55 + nx * bend;
  const c1y = q1.y + dy * 0.55 + ny * bend;
  const c2x = q2.x + dx * 0.45 + nx * bend;
  const c2y = q2.y + dy * 0.45 + ny * bend;
  const f = (n: number) => n.toFixed(1);
  const d = `M${f(q1.x)} ${f(q1.y)}Q${f(c1x)} ${f(c1y)} ${f(tx)} ${f(ty)}Q${f(c2x)} ${f(c2y)} ${f(q2.x)} ${f(q2.y)}Z`;
  return { outline: d, fill: d };
}

function electricTail(a: number, b: number, tx: number, ty: number, lt: number, seed: number): { outline: string; fill: string } {
  const r = rng(seed ^ 0x3e1e);
  const th = boundaryToward(a, b, tx, ty);
  const p = superPoint(a, b, th, 2.4);
  const sx = a + (p.x - a) * 0.96;
  const sy = b + (p.y - b) * 0.96;
  const dx = tx - sx;
  const dy = ty - sy;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const zig = lt * 0.55;
  const pts = [
    { x: sx, y: sy },
    { x: sx + dx * 0.33 + nx * zig * (0.8 + r() * 0.4), y: sy + dy * 0.33 + ny * zig },
    { x: sx + dx * 0.55 - nx * zig, y: sy + dy * 0.55 - ny * zig * (0.8 + r() * 0.4) },
    { x: sx + dx * 0.78 + nx * zig * 0.7, y: sy + dy * 0.78 + ny * zig * 0.7 },
    { x: tx, y: ty },
  ];
  const d = pts.map((q, i) => `${i ? "L" : "M"}${q.x.toFixed(1)} ${q.y.toFixed(1)}`).join("");
  // lightning tail is a single stroke, no fill
  return { outline: d, fill: "" };
}
