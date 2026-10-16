// Ink transitions: a page-sized ink blot that floods in and drains away,
// and a per-panel reveal where the art blooms out of a spreading ink stain.
import { easeInCubic, easeInOut, easeOutCubic, makeBlot, traceBlot, traceDrops, type Blot } from "./ink";

const INK = "#15110e";

function frame(): Promise<number> {
  return new Promise((res) => requestAnimationFrame(res));
}

async function animate(duration: number, step: (t: number, now: number) => void): Promise<void> {
  const start = performance.now();
  for (;;) {
    const now = await frame();
    const t = Math.min(1, (now - start) / duration);
    step(t, now);
    if (t >= 1) return;
  }
}

function makeCanvas(w: number, h: number, maxDpr = 1.5) {
  const dpr = Math.min(window.devicePixelRatio || 1, maxDpr);
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.round(w * dpr));
  c.height = Math.max(1, Math.round(h * dpr));
  c.style.width = `${w}px`;
  c.style.height = `${h}px`;
  const ctx = c.getContext("2d")!;
  ctx.scale(dpr, dpr);
  return { c, ctx };
}

export interface WipeOptions {
  host: HTMLElement;
  direction: 1 | -1;
  seed: number;
  /** called while the stage is fully inked; swap the page here */
  onCovered: () => Promise<void> | void;
  /** expose the canvas while running (for screenshots / tests) */
  onFrame?: (phase: "cover" | "drain", t: number) => void;
  reduced?: boolean;
}

/** Ink-wipe between pages. Resolves once the new page is fully visible. */
export async function inkWipe(opts: WipeOptions): Promise<void> {
  const { host, direction } = opts;
  const rect = host.getBoundingClientRect();
  const W = rect.width;
  const H = rect.height;
  if (opts.reduced || W < 2 || H < 2) {
    host.classList.add("is-fading");
    await new Promise((r) => setTimeout(r, 160));
    await opts.onCovered();
    host.classList.remove("is-fading");
    return;
  }
  const { c, ctx } = makeCanvas(W, H);
  c.className = "ink-wipe";
  host.append(c);

  // Flood: a main blot from the leading edge plus two satellites that merge into it.
  const fromX = direction > 0 ? W * 1.02 : -W * 0.02;
  const ox = fromX;
  const oy = H * 0.62;
  const far = Math.hypot(Math.max(ox, W - ox), Math.max(oy, H - oy));
  const blots: { b: Blot; x: number; y: number; delay: number; scale: number }[] = [
    { b: makeBlot(opts.seed, 1), x: ox, y: oy, delay: 0, scale: 1.45 },
    { b: makeBlot(opts.seed + 1, 0.8), x: ox - direction * W * 0.28, y: H * 0.18, delay: 0.16, scale: 0.62 },
    { b: makeBlot(opts.seed + 2, 0.7), x: ox - direction * W * 0.5, y: H * 0.92, delay: 0.3, scale: 0.5 },
  ];
  const cover = 520;
  await animate(cover, (t, now) => {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = INK;
    ctx.beginPath();
    for (const bl of blots) {
      const lt = Math.max(0, (t - bl.delay) / (1 - bl.delay));
      if (lt <= 0) continue;
      const R = far * bl.scale * easeInCubic(Math.min(1, lt * 1.02)) + 1;
      traceBlot(ctx, bl.b, bl.x, bl.y, R, now / 900);
      traceDrops(ctx, bl.b, bl.x, bl.y, R, Math.min(W, H), lt);
    }
    ctx.fill("nonzero");
    if (t >= 1) ctx.fillRect(0, 0, W, H);
    opts.onFrame?.("cover", t);
  });

  await opts.onCovered();
  await frame();

  // Drain: the ink pulls back to the far edge, leaving a few drying spatters behind.
  const toX = direction > 0 ? -W * 0.06 : W * 1.06;
  const drain = makeBlot(opts.seed + 7, 1.1);
  const spatter = makeBlot(opts.seed + 9, 1.6);
  const R0 = Math.hypot(W, H) * 1.55;
  const drainMs = 680;
  await animate(drainMs, (t, now) => {
    ctx.clearRect(0, 0, W, H);
    const e = easeInOut(t);
    const R = R0 * (1 - e);
    ctx.fillStyle = INK;
    ctx.beginPath();
    if (R > 1) traceBlot(ctx, drain, toX, H * 0.45, R, now / 900);
    ctx.fill();
    // spatters linger and fade
    const a = Math.max(0, 1 - t * 1.3);
    if (a > 0) {
      ctx.globalAlpha = a;
      ctx.beginPath();
      traceDrops(ctx, spatter, W * 0.5, H * 0.5, Math.min(W, H) * 0.48, Math.min(W, H) * 0.9, 1);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
    opts.onFrame?.("drain", t);
  });
  c.remove();
}

export interface RevealOptions {
  host: HTMLElement;
  image: HTMLImageElement;
  w: number;
  h: number;
  seed: number;
  /** object-position y fraction for the cover crop (0..1) */
  posY?: number;
  duration?: number;
}

/** Ink the art of one panel in: the picture blooms out of a spreading stain with a wet ink rim. */
export async function inkReveal(opts: RevealOptions): Promise<void> {
  const { host, image, w, h } = opts;
  const { c, ctx } = makeCanvas(w, h, 2);
  c.className = "panel-reveal";
  host.append(c);
  const iw = image.naturalWidth || 16;
  const ih = image.naturalHeight || 9;
  const s = Math.max(w / iw, h / ih);
  const dw = iw * s;
  const dh = ih * s;
  const dx = (w - dw) / 2;
  const dy = (h - dh) * (opts.posY ?? 0.5);
  const b = makeBlot(opts.seed, 0.9);
  const r = (opts.seed % 1000) / 1000;
  const cx = w * (0.3 + 0.4 * r);
  const cy = h * (0.35 + 0.3 * ((opts.seed >> 10) % 100) / 100);
  const Rmax = Math.hypot(Math.max(cx, w - cx), Math.max(cy, h - cy)) * 1.45;
  const rim = Math.max(6, Math.min(w, h) * 0.035);
  await animate(opts.duration ?? 620, (t, now) => {
    const e = easeOutCubic(t);
    const R = Rmax * e + 2;
    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.beginPath();
    traceBlot(ctx, b, cx, cy, R, now / 700, 90);
    ctx.clip();
    try {
      ctx.drawImage(image, dx, dy, dw, dh);
    } catch {
      ctx.fillStyle = INK;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.restore();
    // wet ink rim on the spreading edge
    ctx.beginPath();
    traceBlot(ctx, b, cx, cy, R, now / 700, 90);
    ctx.lineWidth = rim * (1 - t);
    ctx.strokeStyle = INK;
    ctx.globalAlpha = Math.min(1, (1 - t) * 1.6);
    ctx.stroke();
    ctx.globalAlpha = 1;
  });
  c.remove();
}
