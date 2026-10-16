// Comic page composition: which beats share a page, and where each panel sits.
import { shotType, type Beat } from "./data";

export type PanelKind = "big" | "small";

export function panelKind(beat: Beat): PanelKind {
  const t = shotType(beat);
  return t === "establishing" || t === "wide" ? "big" : "small";
}

/**
 * Group consecutive beats into pages of 1-4 panels.
 * - a scene change or an establishing shot starts a new page
 * - an establishing shot followed by another big shot stays alone (splash page)
 * - big shots (establishing/wide) only stack at the top of a page, at most two
 * - medium/close/POV/low/high/OTS share a row below, at most three
 */
export function planPages(beats: Beat[]): number[][] {
  const pages: number[][] = [];
  let cur: number[] = [];
  const flush = () => {
    if (cur.length) pages.push(cur);
    cur = [];
  };
  beats.forEach((beat, i) => {
    if (!cur.length) {
      cur.push(i);
      return;
    }
    const first = beats[cur[0]];
    const big = panelKind(beat) === "big";
    const bigs = cur.filter((j) => panelKind(beats[j]) === "big").length;
    const smalls = cur.length - bigs;
    const opener = cur.length === 1 && shotType(first) === "establishing";
    let breakPage =
      beat.scene_id !== first.scene_id ||
      shotType(beat) === "establishing" ||
      cur.length >= 4 ||
      bigs >= 2;
    if (!breakPage && big) breakPage = opener || smalls > 0;
    if (!breakPage && !big) breakPage = smalls >= 3;
    if (breakPage) flush();
    cur.push(i);
  });
  flush();
  return pages;
}

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface Tier {
  items: number[];
  minA: number;
  maxA: number;
  ideal: number;
  fill: number;
}

/**
 * Lay out one page inside a W x H stage. Panels are cropped (object-fit: cover) within
 * tolerances so a page fills the stage without distorting the art too much.
 * `aspects` are the native image aspect ratios of the panels.
 */
export function layoutPage(kinds: PanelKind[], aspects: number[], W: number, H: number, gutter: number, narrow: boolean): { rects: Rect[]; width: number; height: number } {
  const n = kinds.length;
  const tiers: Tier[] = [];
  if (n === 1) {
    const a = aspects[0];
    tiers.push({ items: [0], minA: a / 1.12, maxA: a * 1.14, ideal: a, fill: a / 1.08 });
  } else if (narrow) {
    kinds.forEach((_, i) => tiers.push({ items: [i], minA: 1.45, maxA: 2.45, ideal: aspects[i], fill: aspects[i] }));
  } else {
    let row: number[] = [];
    const flushRow = () => {
      if (!row.length) return;
      const k = row.length;
      const ideal = avg(row.map((i) => aspects[i]));
      if (k === 1) tiers.push({ items: row, minA: 1.6, maxA: 2.45, ideal, fill: ideal });
      else if (k === 2) tiers.push({ items: row, minA: 1.3, maxA: 2.0, ideal, fill: 1.5 });
      else tiers.push({ items: row, minA: 1.15, maxA: 1.95, ideal, fill: 1.4 });
      row = [];
    };
    kinds.forEach((kind, i) => {
      if (kind === "big") {
        flushRow();
        tiers.push({ items: [i], minA: 1.7, maxA: 2.45, ideal: aspects[i], fill: aspects[i] });
      } else {
        row.push(i);
        if (row.length === 3) flushRow();
      }
    });
    flushRow();
  }

  const T = tiers.length;
  const gaps = (T - 1) * gutter;
  // Each tier's panel width is (pw - (k-1)g)/k. The smallest total height (max crop)
  // is linear in pw, so solve for the widest page that still fits.
  let slope = 0;
  let offset = 0;
  for (const t of tiers) {
    const k = t.items.length;
    slope += 1 / (k * t.maxA);
    offset += ((k - 1) * gutter) / (k * t.maxA);
  }
  const pwFit = (H - gaps + offset) / slope;
  const pw = Math.max(80, Math.min(W, pwFit));
  const widths = tiers.map((t) => (pw - (t.items.length - 1) * gutter) / t.items.length);
  const ideal = tiers.map((t, i) => widths[i] / t.ideal);
  const lo = tiers.map((t, i) => widths[i] / t.maxA);
  const hi = tiers.map((t, i) => widths[i] / t.minA);
  let heights = ideal.slice();
  const total = sum(heights) + gaps;
  if (total > H) {
    const need = total - H;
    const slack = heights.map((h, i) => Math.max(0, h - lo[i]));
    const s = sum(slack) || 1;
    heights = heights.map((h, i) => h - slack[i] * Math.min(1, need / s));
  } else if (total < H) {
    const room = H - total;
    const grow = tiers.map((t, i) => Math.max(0, Math.min(hi[i], widths[i] / t.fill) - heights[i]));
    const g = sum(grow);
    if (g > 0) heights = heights.map((h, i) => h + grow[i] * Math.min(1, room / g));
  }
  const height = sum(heights) + gaps;
  const rects: Rect[] = new Array(n);
  let y = 0;
  tiers.forEach((t, ti) => {
    let x = 0;
    for (const item of t.items) {
      rects[item] = { x, y, w: widths[ti], h: heights[ti] };
      x += widths[ti] + gutter;
    }
    y += heights[ti] + gutter;
  });
  return { rects, width: pw, height };
}

const sum = (a: number[]) => a.reduce((s, v) => s + v, 0);
const avg = (a: number[]) => sum(a) / (a.length || 1);
