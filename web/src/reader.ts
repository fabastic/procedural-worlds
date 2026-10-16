// The motion-comic reader: pages of inked panels revealed one at a time.
import { dwellSeconds, fetchManifest, shotType, storyUrl, type Beat, type Manifest } from "./data";
import { icons } from "./icons";
import { blotPath, hash, inkBorder, makeBlot, pencilRough, prefersReducedMotion, svgEl } from "./ink";
import { layoutPage, panelKind, planPages, type Rect } from "./layout";
import { letterPanel, letterSize, type LineSpec, type Side } from "./lettering";
import { inkReveal, inkWipe } from "./transitions";
import { escapeHtml } from "./util";
import type { View } from "./view";

type Page = { kind: "cover" } | { kind: "panels"; beats: number[]; scene: number } | { kind: "end" };
type PanelState = "hidden" | "revealed" | "active";

interface PanelView {
  beatIdx: number;
  beat: Beat;
  el: HTMLElement;
  media: HTMLElement;
  img: HTMLImageElement;
  border: SVGSVGElement;
  letters: HTMLElement;
  rect: Rect;
  seed: number;
  state: PanelState;
  video?: HTMLVideoElement;
  lettered: boolean;
  lines: LineSpec[];
}

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"];
const roman = (n: number) => ROMAN[n] ?? String(n + 1);

const SHOT_LABEL: Record<string, string> = {
  establishing: "Establishing shot",
  wide: "Wide shot",
  medium: "Medium shot",
  close: "Close-up",
  POV: "Point-of-view shot",
  low: "Low-angle shot",
  high: "High-angle shot",
  OTS: "Over-the-shoulder shot",
};

const KEN_BURNS: Record<string, [string, string]> = {
  push_in: ["scale(1.005)", "scale(1.075)"],
  dolly_in: ["scale(1.005)", "scale(1.075)"],
  zoom_in: ["scale(1.005)", "scale(1.075)"],
  pull_out: ["scale(1.08)", "scale(1.005)"],
  dolly_out: ["scale(1.08)", "scale(1.005)"],
  zoom_out: ["scale(1.08)", "scale(1.005)"],
  pan_left: ["scale(1.07) translateX(2.2%)", "scale(1.07) translateX(-2.2%)"],
  pan_right: ["scale(1.07) translateX(-2.2%)", "scale(1.07) translateX(2.2%)"],
  tilt_up: ["scale(1.07) translateY(-2%)", "scale(1.07) translateY(2%)"],
  tilt_down: ["scale(1.07) translateY(2%)", "scale(1.07) translateY(-2%)"],
  crane_up: ["scale(1.07) translateY(-2%)", "scale(1.07) translateY(2%)"],
  orbit: ["scale(1.05) rotate(-0.4deg)", "scale(1.07) rotate(0.4deg)"],
  static: ["scale(1.01)", "scale(1.04)"],
};

function decodeWithTimeout(img: HTMLImageElement, ms: number): Promise<void> {
  if (img.complete && img.naturalWidth) return Promise.resolve();
  return Promise.race([img.decode().catch(() => undefined), new Promise<void>((r) => setTimeout(r, ms))]);
}

export async function mountReader(main: HTMLElement, slug: string, start?: string): Promise<View> {
  const manifest = await fetchManifest(slug);
  if (!manifest.beats.length) throw new Error("This story has no beats yet.");
  await Promise.race([document.fonts?.ready, new Promise((r) => setTimeout(r, 1500))]);
  const reader = new Reader(main, manifest, start);
  return { destroy: () => reader.destroy() };
}

class Reader {
  private m: Manifest;
  private pages: Page[];
  private beatPage: number[] = [];
  private beatSlot: number[] = [];
  private pageIdx = 0;
  private panelIdx = 0;
  private panels: PanelView[] = [];
  private speakerSide = new Map<string, Side>();

  private root: HTMLElement;
  private stage: HTMLElement;
  private pageEl: HTMLElement | null = null;
  private live: HTMLElement;
  private ctlPrev: HTMLButtonElement;
  private ctlNext: HTMLButtonElement;
  private ctlPlay: HTMLButtonElement;
  private ctlFull: HTMLButtonElement | null;
  private ctlChapters: HTMLButtonElement;
  private chapterLabel: HTMLElement;
  private countLabel: HTMLElement;
  private progressFill: HTMLElement;
  private progressEl: HTMLElement;
  private sheet: HTMLElement;

  private autoplay = false;
  private autoTimer = 0;
  private busy = false;
  private queued: "next" | "prev" | null = null;
  private boilTimer = 0;
  private boilStep = 0;
  private resizeTimer = 0;
  private ro: ResizeObserver;
  private destroyed = false;
  private reduced = prefersReducedMotion();
  private swipe: { x: number; y: number; id: number } | null = null;
  private suppressClick = false;
  private disposers: (() => void)[] = [];

  constructor(main: HTMLElement, m: Manifest, start?: string) {
    this.m = m;
    const plan = planPages(m.beats);
    this.pages = [{ kind: "cover" }];
    plan.forEach((beats) => {
      const scene = Math.max(0, m.scenes.findIndex((s) => s.id === m.beats[beats[0]].scene_id));
      beats.forEach((b, slot) => {
        this.beatPage[b] = this.pages.length;
        this.beatSlot[b] = slot;
      });
      this.pages.push({ kind: "panels", beats, scene });
    });
    this.pages.push({ kind: "end" });

    // Off-panel speakers keep a consistent side for the whole story.
    let flip: Side = "right";
    for (const b of m.beats) {
      for (const d of b.dialogue ?? []) {
        const key = d.speaker.toUpperCase();
        if (!this.speakerSide.has(key)) {
          this.speakerSide.set(key, flip);
          flip = flip === "right" ? "left" : "right";
        }
      }
    }

    this.root = document.createElement("section");
    this.root.className = "reader";
    this.root.setAttribute("aria-label", `${m.title}, motion comic`);
    this.root.innerHTML = `
      <div class="stage" tabindex="0" aria-describedby="reader-help">
        <p id="reader-help" class="sr-only">Press Space or the right arrow for the next panel, left arrow to go back, A to toggle autoplay, C for chapters, F for full screen.</p>
      </div>
      <div class="sr-only" aria-live="polite" aria-atomic="true" data-live></div>
      <div class="controls" role="toolbar" aria-label="Reader controls">
        <svg class="controls-rule" viewBox="0 0 1000 8" preserveAspectRatio="none" aria-hidden="true"><path d="" /></svg>
        <div class="controls-group">
          <a class="ctl ctl-ghost" href="#/" aria-label="Back to the library">${icons.library}</a>
          <button class="ctl" type="button" data-act="prev" aria-label="Previous panel" aria-keyshortcuts="ArrowLeft">${icons.prev}</button>
          <button class="ctl ctl-play" type="button" data-act="play" aria-pressed="false" aria-label="Autoplay" aria-keyshortcuts="A">
            <svg class="play-ring" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="19.5" pathLength="1"/></svg>
            <span class="ctl-play-icon">${icons.play}</span>
          </button>
          <button class="ctl ctl-next" type="button" data-act="next" aria-label="Next panel" aria-keyshortcuts="ArrowRight Space">${icons.next}</button>
        </div>
        <div class="controls-progress">
          <div class="progress-labels"><span class="progress-chapter" data-chapter></span><span class="progress-count" data-count></span></div>
          <div class="progress" data-progress role="progressbar" aria-label="Story progress" aria-valuemin="0" aria-valuemax="100">
            <div class="progress-track"></div>
            <div class="progress-fill" data-fill></div>
          </div>
        </div>
        <div class="controls-group">
          <button class="ctl" type="button" data-act="chapters" aria-haspopup="dialog" aria-expanded="false" aria-label="Chapters" aria-keyshortcuts="C">${icons.chapters}</button>
          <button class="ctl" type="button" data-act="fullscreen" aria-label="Full screen" aria-keyshortcuts="F">${icons.fullscreen}</button>
        </div>
      </div>
      <div class="chapters" role="dialog" aria-label="Chapters" hidden>
        <div class="chapters-head"><h2>Chapters</h2><button class="ctl ctl-ghost" type="button" data-act="close-chapters" aria-label="Close chapters">${icons.close}</button></div>
        <ol class="chapters-list"></ol>
      </div>`;
    main.append(this.root);

    const q = <T extends Element>(sel: string) => this.root.querySelector(sel) as T;
    this.stage = q(".stage");
    this.live = q("[data-live]");
    this.ctlPrev = q('[data-act="prev"]');
    this.ctlNext = q('[data-act="next"]');
    this.ctlPlay = q('[data-act="play"]');
    this.ctlChapters = q('[data-act="chapters"]');
    this.ctlFull = q('[data-act="fullscreen"]');
    this.chapterLabel = q("[data-chapter]");
    this.countLabel = q("[data-count]");
    this.progressFill = q("[data-fill]");
    this.progressEl = q("[data-progress]");
    this.sheet = q(".chapters");
    if (!document.fullscreenEnabled) {
      this.ctlFull?.remove();
      this.ctlFull = null;
    }

    this.buildProgressTicks();
    this.buildChapterList();
    this.bind();

    this.ro = new ResizeObserver(() => {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = window.setTimeout(() => this.relayout(), 120);
    });
    this.ro.observe(this.stage);

    // starting position
    let page = 0;
    let slot = 0;
    if (start === "end") page = this.pages.length - 1;
    else if (start) {
      const bi = m.beats.findIndex((b) => b.id === start);
      if (bi >= 0) {
        page = this.beatPage[bi];
        slot = this.beatSlot[bi];
      }
    }
    this.renderPage(page, slot);
    this.pageIdx = page;
    if (this.pages[page].kind === "panels") this.activate(slot);
    else this.afterMove();
    this.updateRule();
    if (!this.reduced) this.boilTimer = window.setInterval(() => this.boil(), 167);
    requestAnimationFrame(() => this.stage.focus({ preventScroll: true }));
  }

  destroy(): void {
    this.destroyed = true;
    clearTimeout(this.autoTimer);
    clearTimeout(this.resizeTimer);
    clearInterval(this.boilTimer);
    this.ro.disconnect();
    for (const d of this.disposers) d();
    for (const p of this.panels) this.stopMotion(p);
    if (document.fullscreenElement === this.root) document.exitFullscreen().catch(() => {});
    this.root.remove();
  }

  // ------------------------------------------------------------------ input

  private bind(): void {
    const on = <K extends keyof (WindowEventMap & DocumentEventMap)>(
      t: Window | Document,
      type: K,
      fn: (e: (WindowEventMap & DocumentEventMap)[K]) => void,
    ) => {
      t.addEventListener(type, fn as EventListener);
      this.disposers.push(() => t.removeEventListener(type, fn as EventListener));
    };

    this.root.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;
      const act = target.closest<HTMLElement>("[data-act]")?.dataset.act;
      if (act) {
        e.preventDefault();
        this.command(act);
        return;
      }
      const jump = target.closest<HTMLElement>("[data-jump-scene]");
      if (jump) {
        e.preventDefault();
        this.jumpToScene(Number(jump.dataset.jumpScene));
        return;
      }
      if (target.closest("a,button,input,textarea")) return;
      if (target.closest(".stage")) {
        if (this.suppressClick) {
          this.suppressClick = false;
          return;
        }
        this.next();
      }
    });

    this.progressEl.addEventListener("click", (e) => {
      if ((e.target as HTMLElement).closest("[data-jump-scene]")) return;
      const r = this.progressEl.getBoundingClientRect();
      const f = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
      const bi = Math.min(this.m.beats.length - 1, Math.floor(f * this.m.beats.length));
      this.jumpToBeat(bi);
    });

    this.stage.addEventListener("pointerdown", (e) => {
      if (e.pointerType === "mouse") return;
      this.swipe = { x: e.clientX, y: e.clientY, id: e.pointerId };
    });
    this.stage.addEventListener("pointerup", (e) => {
      const s = this.swipe;
      this.swipe = null;
      if (!s || s.id !== e.pointerId) return;
      const dx = e.clientX - s.x;
      const dy = e.clientY - s.y;
      if (Math.abs(dx) > 42 && Math.abs(dx) > Math.abs(dy) * 1.3) {
        this.suppressClick = true;
        setTimeout(() => (this.suppressClick = false), 400);
        if (dx < 0) this.next();
        else this.prev();
      }
    });
    this.stage.addEventListener("pointercancel", () => (this.swipe = null));

    on(window, "keydown", (e) => {
      if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
      const t = e.target as HTMLElement | null;
      if (t && t.closest("input,textarea,select,[contenteditable]")) return;
      const onControl = !!t?.closest("button,a");
      switch (e.key) {
        case "ArrowRight":
        case "PageDown":
          e.preventDefault();
          this.next();
          break;
        case " ":
        case "Enter":
          if (onControl) return;
          e.preventDefault();
          this.next();
          break;
        case "ArrowLeft":
        case "PageUp":
          e.preventDefault();
          this.prev();
          break;
        case "Home":
          e.preventDefault();
          this.goToPage(0, 0, -1);
          break;
        case "End":
          e.preventDefault();
          this.goToPage(this.pages.length - 1, 0, 1);
          break;
        case "a":
        case "A":
          this.toggleAutoplay();
          break;
        case "f":
        case "F":
          this.toggleFullscreen();
          break;
        case "c":
        case "C":
          this.toggleChapters();
          break;
        case "Escape":
          if (!this.sheet.hidden) {
            this.toggleChapters(false);
            e.preventDefault();
          }
          break;
      }
    });

    on(document, "fullscreenchange", () => {
      const fs = document.fullscreenElement === this.root;
      this.root.classList.toggle("is-fullscreen", fs);
      if (this.ctlFull) {
        this.ctlFull.innerHTML = fs ? icons.exitFullscreen : icons.fullscreen;
        this.ctlFull.setAttribute("aria-label", fs ? "Exit full screen" : "Full screen");
      }
    });

    on(document, "visibilitychange", () => {
      if (document.hidden) clearTimeout(this.autoTimer);
      else this.scheduleAuto();
    });
  }

  private command(act: string): void {
    switch (act) {
      case "next":
        return this.next();
      case "prev":
        return this.prev();
      case "play":
        return this.toggleAutoplay();
      case "chapters":
        return this.toggleChapters();
      case "close-chapters":
        return this.toggleChapters(false);
      case "fullscreen":
        return this.toggleFullscreen();
      case "restart":
        return void this.goToPage(1, 0, 1);
    }
  }

  // ------------------------------------------------------------- navigation

  next(): void {
    if (this.busy) {
      this.queued = "next";
      return;
    }
    const page = this.pages[this.pageIdx];
    if (page.kind === "panels" && this.panelIdx < page.beats.length - 1) {
      void this.revealNext();
    } else if (this.pageIdx < this.pages.length - 1) {
      void this.goToPage(this.pageIdx + 1, 0, 1);
    } else {
      this.setAutoplay(false);
    }
  }

  prev(): void {
    if (this.busy) {
      this.queued = "prev";
      return;
    }
    const page = this.pages[this.pageIdx];
    if (page.kind === "panels" && this.panelIdx > 0) {
      const cur = this.panels[this.panelIdx];
      this.setState(cur, "hidden");
      this.activate(this.panelIdx - 1);
    } else if (this.pageIdx > 0) {
      const target = this.pages[this.pageIdx - 1];
      const last = target.kind === "panels" ? target.beats.length - 1 : 0;
      void this.goToPage(this.pageIdx - 1, last, -1);
    }
  }

  private async revealNext(): Promise<void> {
    this.busy = true;
    clearTimeout(this.autoTimer);
    await this.reveal(this.panelIdx + 1, true);
    this.busy = false;
    this.flushQueue();
  }

  private flushQueue(): void {
    const q = this.queued;
    this.queued = null;
    if (q === "next") this.next();
    else if (q === "prev") this.prev();
  }

  private jumpToScene(sceneIdx: number): void {
    this.toggleChapters(false);
    const sceneId = this.m.scenes[sceneIdx]?.id;
    const bi = this.m.beats.findIndex((b) => b.scene_id === sceneId);
    if (bi >= 0) this.jumpToBeat(bi);
  }

  private jumpToBeat(bi: number): void {
    if (this.busy) return;
    const page = this.beatPage[bi];
    const slot = this.beatSlot[bi];
    if (page === this.pageIdx) {
      if (slot === this.panelIdx) return;
      // same page: reveal up to the slot, hide the rest
      this.panels.forEach((p, i) => {
        if (i < slot && p.state === "hidden") this.setState(p, "revealed");
        if (i > slot) this.setState(p, "hidden");
      });
      if (this.panels[slot].state === "hidden") void this.reveal(slot, true);
      else this.activate(slot);
      return;
    }
    void this.goToPage(page, slot, page > this.pageIdx ? 1 : -1);
  }

  /** Change page with the ink wipe. Forward: the target panel inks in after the wipe. */
  private async goToPage(page: number, slot: number, dir: 1 | -1): Promise<void> {
    if (this.busy || page === this.pageIdx || page < 0 || page >= this.pages.length) return;
    this.busy = true;
    clearTimeout(this.autoTimer);
    this.toggleChapters(false);
    const forward = dir > 0;
    const target = this.pages[page];
    await inkWipe({
      host: this.stage,
      direction: dir,
      seed: hash(this.m.slug) + page * 31,
      reduced: this.reduced,
      onFrame: (phase, t) => {
        this.root.dataset.wipe = `${phase}:${t.toFixed(2)}`;
      },
      onCovered: async () => {
        for (const p of this.panels) this.stopMotion(p);
        this.pageIdx = page;
        this.renderPage(page, forward ? slot - 1 : slot);
        if (target.kind === "panels") {
          const imgs = this.panels.slice(0, slot + 1).map((p) => decodeWithTimeout(p.img, 1200));
          await Promise.all(imgs);
        }
      },
    });
    delete this.root.dataset.wipe;
    if (this.destroyed) return;
    if (target.kind === "panels") {
      if (forward) await this.reveal(slot, true);
      else this.activate(slot);
    } else {
      this.panelIdx = 0;
      this.afterMove();
    }
    this.busy = false;
    this.flushQueue();
  }

  // -------------------------------------------------------------- rendering

  private stageBox() {
    const cs = getComputedStyle(this.stage);
    const padX = parseFloat(cs.paddingLeft) || 0;
    const padY = parseFloat(cs.paddingTop) || 0;
    const W = Math.min(this.stage.clientWidth - padX * 2, 1760);
    const H = this.stage.clientHeight - padY * 2;
    return { W: Math.max(W, 120), H: Math.max(H, 120), padX, padY };
  }

  /** Render page `idx` with panels [0..revealedThrough] already inked (no animation). */
  private renderPage(idx: number, revealedThrough: number): void {
    this.pageEl?.remove();
    this.panels = [];
    const page = this.pages[idx];
    const el = document.createElement("div");
    el.className = `page page--${page.kind}`;
    this.pageEl = el;
    this.stage.append(el);
    if (page.kind === "cover") this.renderCover(el);
    else if (page.kind === "end") this.renderEnd(el);
    else this.renderPanels(el, page, revealedThrough);
    this.preload(idx + 1);
  }

  private placePage(el: HTMLElement, width: number, height: number): void {
    const { H, padX, padY } = this.stageBox();
    const left = padX + (this.stage.clientWidth - padX * 2 - width) / 2;
    const top = padY + (H - height) / 2;
    el.style.left = `${Math.round(left)}px`;
    el.style.top = `${Math.round(Math.max(padY * 0.5, top))}px`;
    el.style.width = `${Math.round(width)}px`;
    el.style.height = `${Math.round(height)}px`;
  }

  private renderPanels(el: HTMLElement, page: Extract<Page, { kind: "panels" }>, revealedThrough: number): void {
    const { W, H } = this.stageBox();
    const narrow = W < 640 || W / H < 0.85;
    const gutter = narrow ? 12 : Math.round(Math.min(22, Math.max(12, W * 0.013)));
    const beats = page.beats.map((i) => this.m.beats[i]);
    const kinds = beats.map(panelKind);
    const aspects = beats.map((b) => (b.width && b.height ? b.width / b.height : 16 / 9));
    const lay = layoutPage(kinds, aspects, W, H, gutter, narrow);
    this.placePage(el, lay.width, lay.height);
    el.setAttribute("aria-label", `Page ${this.pageNumber(this.pageIdx)}`);

    let lastSpeaker = "";
    page.beats.forEach((bi, slot) => {
      const beat = this.m.beats[bi];
      const rect = lay.rects[slot];
      const seed = hash(`${this.m.slug}/${beat.id}`);
      const fig = document.createElement("figure");
      fig.className = `panel panel--${shotType(beat).toLowerCase()}`;
      fig.style.left = `${rect.x}px`;
      fig.style.top = `${rect.y}px`;
      fig.style.width = `${rect.w}px`;
      fig.style.height = `${rect.h}px`;

      const ghost = svgEl("svg", { class: "panel-ghost", width: rect.w, height: rect.h, "aria-hidden": "true" });
      ghost.append(svgEl("path", { d: pencilRough(rect.w, rect.h, seed) }));

      const media = document.createElement("div");
      media.className = "panel-media";
      const img = document.createElement("img");
      img.className = "panel-still";
      img.alt = "";
      img.decoding = "async";
      img.draggable = false;
      img.src = storyUrl(this.m.slug, beat.still);
      img.addEventListener("error", () => fig.classList.add("is-missing"), { once: true });
      media.append(img);

      const border = svgEl("svg", { class: "panel-border", width: rect.w, height: rect.h, "aria-hidden": "true" });
      const scale = Math.min(1.25, Math.max(0.8, Math.min(rect.w, rect.h) / 360));
      const paths = inkBorder(rect.w, rect.h, seed, scale);
      const sw = Math.max(4.5, Math.min(8, Math.min(rect.w, rect.h) * 0.016));
      border.append(
        svgEl("path", { class: "b-main", d: paths.main, pathLength: 1, "stroke-width": sw.toFixed(1) }),
        svgEl("path", { class: "b-weight", d: paths.weight, pathLength: 1, "stroke-width": (sw * 0.55).toFixed(1) }),
      );

      const letters = document.createElement("div");
      letters.className = "panel-letters";

      const cap = document.createElement("figcaption");
      cap.className = "sr-only";
      cap.textContent = this.describe(beat);

      fig.append(ghost, media, border, letters, cap);
      el.append(fig);

      // speaker labels: shown when the voice changes
      const lines: LineSpec[] = (beat.dialogue ?? []).map((d) => {
        const key = d.speaker.toUpperCase();
        const showSpeaker = key !== lastSpeaker;
        lastSpeaker = key;
        return { speaker: d.speaker, text: d.text, side: this.speakerSide.get(key) ?? "right", showSpeaker };
      });
      const pv: PanelView = { beatIdx: bi, beat, el: fig, media, img, border, letters, rect, seed, state: "hidden", lettered: false, lines };
      this.panels.push(pv);
      this.setState(pv, slot <= revealedThrough ? "revealed" : "hidden");
    });
  }

  private renderCover(el: HTMLElement): void {
    const { W, H } = this.stageBox();
    const coverBeat = this.m.beats.find((b) => b.still === this.m.cover) ?? this.m.beats[0];
    const aspect = coverBeat.width && coverBeat.height ? coverBeat.width / coverBeat.height : 16 / 9;
    const narrow = W < 640 || W / H < 0.85;
    // phones get a tall poster crop of the cover; wide screens a cinematic splash
    const lay = narrow
      ? { rects: [{ x: 0, y: 0, w: W, h: Math.min(H, W * 1.55) }], width: W, height: Math.min(H, W * 1.55) }
      : layoutPage(["big"], [aspect], W, H * 0.94, 0, false);
    this.placePage(el, lay.width, lay.height);
    const rect = lay.rects[0];
    const seed = hash(this.m.slug + "/cover");
    const paths = inkBorder(rect.w, rect.h, seed, 1.2);
    const sw = Math.max(5, Math.min(9, Math.min(rect.w, rect.h) * 0.018));
    const title = escapeHtml(this.m.title);
    const words = this.m.title.split(/\s+/);
    el.innerHTML = `
      <figure class="cover-frame" style="width:${rect.w}px;height:${rect.h}px">
        <div class="panel-media is-in"><img class="cover-img" alt="" src="${storyUrl(this.m.slug, this.m.cover ?? coverBeat.still)}"></div>
        <svg class="panel-border" width="${rect.w}" height="${rect.h}" aria-hidden="true">
          <path class="b-main" d="${paths.main}" stroke-width="${sw.toFixed(1)}"/>
          <path class="b-weight" d="${paths.weight}" stroke-width="${(sw * 0.55).toFixed(1)}"/>
        </svg>
        <div class="cover-title">
          <h1 class="cover-heading" aria-label="${title}">${words.map((w) => `<span>${escapeHtml(w)}</span>`).join(" ")}</h1>
          ${this.m.logline ? `<p class="caption cover-logline" style="--rot:-1.2deg"><span class="caption-text">${escapeHtml(this.m.logline)}</span></p>` : ""}
        </div>
        <p class="cover-hint"><span>${this.m.beats.length} panels &middot; ${this.m.scenes.length} chapters</span><span class="cover-go">Tap, click or press &rarr; to begin</span></p>
      </figure>`;
  }

  private renderEnd(el: HTMLElement): void {
    const { W, H } = this.stageBox();
    const w = Math.min(W, 760);
    const h = Math.min(H, 520);
    this.placePage(el, w, h);
    const blot = blotPath(makeBlot(hash(this.m.slug + "/end"), 0.9), 380, 230, 150);
    el.innerHTML = `
      <div class="end-card">
        <svg class="end-blot" viewBox="0 0 760 460" aria-hidden="true"><path d="${blot}"/></svg>
        <h2 class="end-title">The End</h2>
        <p class="end-story">${escapeHtml(this.m.title)}</p>
        <div class="end-actions">
          <button class="btn btn-ink" type="button" data-act="restart">${icons.restart}<span>Read again</span></button>
          <a class="btn" href="#/">${icons.library}<span>Library</span></a>
          ${this.m.animatic ? `<a class="btn" href="#/animatic/${encodeURIComponent(this.m.slug)}" data-fullscreen>${icons.film}<span>Watch the animatic</span></a>` : ""}
        </div>
      </div>`;
  }

  private relayout(): void {
    if (this.destroyed) return;
    if (this.busy) {
      this.resizeTimer = window.setTimeout(() => this.relayout(), 200);
      return;
    }
    const page = this.pages[this.pageIdx];
    for (const p of this.panels) this.stopMotion(p);
    this.renderPage(this.pageIdx, page.kind === "panels" ? this.panelIdx : 0);
    if (page.kind === "panels") this.activate(this.panelIdx, false);
    this.updateRule();
  }

  // ------------------------------------------------------------ panel state

  private setState(p: PanelView, state: PanelState): void {
    p.state = state;
    p.el.dataset.state = state;
    p.el.setAttribute("aria-hidden", state === "hidden" ? "true" : "false");
    if (state === "hidden") {
      this.stopMotion(p);
      p.media.classList.remove("is-in");
      p.letters.replaceChildren();
      p.lettered = false;
      p.border.style.filter = "";
    } else {
      p.media.classList.add("is-in");
      if (!p.lettered) this.letter(p, false);
    }
    if (state !== "active") {
      this.pauseMotion(p);
      p.border.style.filter = "";
    }
  }

  private letter(p: PanelView, animate: boolean): void {
    const lines = p.lines;
    const chars = (p.beat.caption?.length ?? 0) + lines.reduce((n, l) => n + l.text.length, 0);
    const lt = letterSize(p.rect.w, p.rect.h, chars);
    p.letters.style.setProperty("--lt", `${lt}px`);
    p.letters.replaceChildren();
    const els = letterPanel(p.letters, { caption: p.beat.caption, lines, w: p.rect.w, h: p.rect.h, seed: p.seed }, lt);
    if (animate && !this.reduced) {
      els.forEach((e, i) => {
        e.classList.add("pop");
        e.style.animationDelay = `${120 + i * 240}ms`;
      });
    }
    p.lettered = true;
  }

  /** Ink a panel in (or show it instantly) and make it the active one. */
  private async reveal(slot: number, animate: boolean): Promise<void> {
    const p = this.panels[slot];
    if (!p) return;
    if (!animate || this.reduced) {
      this.setState(p, "revealed");
      this.activate(slot);
      return;
    }
    p.state = "revealed";
    p.el.dataset.state = "inking";
    p.el.setAttribute("aria-hidden", "false");
    await decodeWithTimeout(p.img, 1500);
    if (this.destroyed || !p.el.isConnected) return;
    if (p.img.naturalWidth) {
      await inkReveal({ host: p.el, image: p.img, w: p.rect.w, h: p.rect.h, seed: p.seed });
    }
    if (this.destroyed || !p.el.isConnected) return;
    p.media.classList.add("is-in");
    p.el.dataset.state = "revealed";
    this.letter(p, true);
    this.activate(slot);
  }

  private activate(slot: number, announce = true): void {
    this.panels.forEach((p, i) => {
      if (i !== slot && p.state === "active") this.setState(p, "revealed");
    });
    const p = this.panels[slot];
    if (!p) return;
    if (p.state === "hidden") this.setState(p, "revealed");
    p.state = "active";
    p.el.dataset.state = "active";
    this.panelIdx = slot;
    this.startMotion(p);
    this.afterMove(announce);
  }

  private startMotion(p: PanelView): void {
    if (this.reduced) return;
    const clip = p.beat.clip;
    if (clip && !p.el.classList.contains("clip-failed")) {
      if (!p.video) {
        const v = document.createElement("video");
        v.className = "panel-clip";
        v.muted = true;
        v.defaultMuted = true;
        v.loop = true;
        v.playsInline = true;
        v.autoplay = true;
        v.preload = "auto";
        v.setAttribute("muted", "");
        v.setAttribute("playsinline", "");
        v.setAttribute("aria-hidden", "true");
        v.poster = p.img.src;
        v.addEventListener("playing", () => v.classList.add("is-playing"));
        v.addEventListener("error", () => {
          p.el.classList.add("clip-failed");
          v.remove();
          if (p.video === v) p.video = undefined;
          if (p.state === "active") this.kenBurns(p, true);
        });
        v.src = storyUrl(this.m.slug, clip);
        p.media.append(v);
        p.video = v;
      }
      p.video.play().catch(() => {
        /* autoplay refused: the poster still shows, ken burns takes over */
        if (p.state === "active") this.kenBurns(p, true);
      });
      return;
    }
    this.kenBurns(p, true);
  }

  private kenBurns(p: PanelView, on: boolean): void {
    if (this.reduced) return;
    const img = p.img;
    if (on) {
      const move = (p.beat.shot.camera_move ?? "static").toLowerCase().replace(/[\s-]+/g, "_");
      const [from, to] = KEN_BURNS[move] ?? KEN_BURNS.static;
      img.style.setProperty("--kb-from", from);
      img.style.setProperty("--kb-to", to);
      const dur = Math.min(18, Math.max(9, (p.beat.shot.duration_s ?? 3) * 3.2));
      img.style.setProperty("--kb-dur", `${dur.toFixed(1)}s`);
      img.classList.add("kb");
      img.classList.remove("kb-paused");
    } else if (img.classList.contains("kb")) {
      img.classList.add("kb-paused");
    }
  }

  private pauseMotion(p: PanelView): void {
    if (p.video) {
      p.video.pause();
      p.video.remove();
      p.video = undefined;
    }
    this.kenBurns(p, false);
  }

  private stopMotion(p: PanelView): void {
    this.pauseMotion(p);
  }

  private boil(): void {
    if (document.hidden) return;
    const p = this.panels[this.panelIdx];
    if (!p || p.state !== "active") return;
    this.boilStep = (this.boilStep + 1) % 3;
    p.border.style.filter = `url(#ink-boil-${this.boilStep})`;
  }

  // -------------------------------------------------------------- chrome

  private afterMove(announce = true): void {
    const page = this.pages[this.pageIdx];
    const beatIdx = page.kind === "panels" ? page.beats[this.panelIdx] : -1;
    const total = this.m.beats.length;
    const done = page.kind === "end" ? total : beatIdx + 1;
    const pct = (done / total) * 100;
    this.progressFill.style.width = `${pct}%`;
    this.progressEl.setAttribute("aria-valuenow", pct.toFixed(0));
    this.progressEl.setAttribute("aria-valuetext", page.kind === "panels" ? `Panel ${done} of ${total}` : page.kind === "cover" ? "Cover" : "The end");

    const sceneIdx = page.kind === "panels" ? page.scene : page.kind === "end" ? this.m.scenes.length - 1 : -1;
    const scene = this.m.scenes[sceneIdx];
    this.chapterLabel.textContent = page.kind === "cover" ? this.m.title : page.kind === "end" ? "The end" : `${roman(sceneIdx)} · ${scene?.name ?? ""}`;
    const pages = this.pages.length - 2;
    this.countLabel.textContent =
      page.kind === "panels" ? `Page ${this.pageNumber(this.pageIdx)} / ${pages}` : page.kind === "cover" ? `${pages} pages` : "";
    this.sheet.querySelectorAll<HTMLElement>("[data-jump-scene]").forEach((b) => {
      const current = Number(b.dataset.jumpScene) === sceneIdx;
      b.classList.toggle("is-current", current);
      if (current) b.setAttribute("aria-current", "true");
      else b.removeAttribute("aria-current");
    });
    this.progressEl.querySelectorAll<HTMLElement>("[data-jump-scene]").forEach((t) => {
      t.classList.toggle("is-passed", Number(t.dataset.beat) < done);
    });

    this.ctlPrev.disabled = this.pageIdx === 0;
    this.ctlNext.disabled = page.kind === "end";
    this.root.dataset.page = page.kind;

    // keep the URL pointing at the current beat (no history spam)
    const id = page.kind === "panels" ? this.m.beats[beatIdx].id : page.kind === "end" ? "end" : "";
    const hashUrl = `#/read/${encodeURIComponent(this.m.slug)}${id ? `/${encodeURIComponent(id)}` : ""}`;
    if (location.hash !== hashUrl) history.replaceState(history.state, "", hashUrl);

    if (announce) {
      if (page.kind === "panels") {
        const beat = this.m.beats[beatIdx];
        this.live.textContent = `Page ${this.pageNumber(this.pageIdx)}, panel ${this.panelIdx + 1} of ${page.beats.length}. ${this.describe(beat)}`;
      } else if (page.kind === "cover") {
        this.live.textContent = `${this.m.title}. ${this.m.logline ?? ""}`;
      } else {
        this.live.textContent = "The end.";
      }
    }
    this.scheduleAuto();
    if (page.kind === "end") this.setAutoplay(false);
  }

  private pageNumber(idx: number): number {
    return idx; // page 0 is the cover
  }

  private describe(beat: Beat): string {
    const shot = SHOT_LABEL[shotType(beat)] ?? "Panel";
    const focus = beat.shot.focus ? ` of the ${beat.shot.focus.replace(/[_-]+/g, " ")}` : "";
    const parts = [`${shot}${focus}.`];
    if (beat.caption) parts.push(`Caption: ${beat.caption}`);
    for (const d of beat.dialogue ?? []) parts.push(`${d.speaker || "Someone"}, off panel: ${d.text}`);
    return parts.join(" ");
  }

  private buildProgressTicks(): void {
    const total = this.m.beats.length;
    this.m.scenes.forEach((s, i) => {
      const bi = this.m.beats.findIndex((b) => b.scene_id === s.id);
      if (bi < 0) return;
      const t = document.createElement("button");
      t.type = "button";
      t.className = "progress-tick";
      t.dataset.jumpScene = String(i);
      t.dataset.beat = String(bi);
      t.style.left = `${(bi / total) * 100}%`;
      t.setAttribute("aria-label", `Chapter ${roman(i)}: ${s.name}`);
      t.title = `${roman(i)} · ${s.name}`;
      this.progressEl.append(t);
    });
  }

  private buildChapterList(): void {
    const list = this.sheet.querySelector("ol")!;
    this.m.scenes.forEach((s, i) => {
      const first = this.m.beats.find((b) => b.scene_id === s.id);
      const count = this.m.beats.filter((b) => b.scene_id === s.id).length;
      const li = document.createElement("li");
      li.innerHTML = `
        <button type="button" class="chapter" data-jump-scene="${i}">
          <span class="chapter-thumb">${first ? `<img alt="" loading="lazy" src="${storyUrl(this.m.slug, first.still)}">` : ""}</span>
          <span class="chapter-num">${roman(i)}</span>
          <span class="chapter-name">${escapeHtml(s.name)}</span>
          <span class="chapter-meta">${count} panel${count === 1 ? "" : "s"}</span>
        </button>`;
      list.append(li);
    });
  }

  private toggleChapters(force?: boolean): void {
    const open = force ?? this.sheet.hidden;
    if (open === !this.sheet.hidden) return;
    this.sheet.hidden = !open;
    this.ctlChapters.setAttribute("aria-expanded", String(open));
    if (open) {
      (this.sheet.querySelector(".is-current") as HTMLElement | null ?? this.sheet.querySelector<HTMLElement>(".chapter"))?.focus();
    } else if (this.sheet.contains(document.activeElement)) {
      this.ctlChapters.focus();
    }
  }

  private toggleFullscreen(): void {
    if (!document.fullscreenEnabled) return;
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else this.root.requestFullscreen().catch(() => {});
  }

  private toggleAutoplay(): void {
    this.setAutoplay(!this.autoplay);
  }

  private setAutoplay(on: boolean): void {
    if (this.autoplay === on) return;
    this.autoplay = on;
    this.ctlPlay.setAttribute("aria-pressed", String(on));
    this.ctlPlay.setAttribute("aria-label", on ? "Pause autoplay" : "Autoplay");
    this.ctlPlay.querySelector(".ctl-play-icon")!.innerHTML = on ? icons.pause : icons.play;
    this.root.classList.toggle("is-autoplay", on);
    if (on && this.pages[this.pageIdx].kind === "end") {
      this.autoplay = false;
      void this.goToPage(1, 0, 1).then(() => this.setAutoplay(true));
      return;
    }
    this.scheduleAuto();
  }

  private scheduleAuto(): void {
    clearTimeout(this.autoTimer);
    const ring = this.ctlPlay.querySelector<SVGCircleElement>(".play-ring circle")!;
    ring.style.animation = "none";
    if (!this.autoplay || this.busy || document.hidden) return;
    const page = this.pages[this.pageIdx];
    let secs: number;
    if (page.kind === "cover") secs = 3.2;
    else if (page.kind === "end") return;
    else secs = dwellSeconds(this.m.beats[page.beats[this.panelIdx]]);
    void ring.getBoundingClientRect();
    ring.style.animation = `ring ${secs}s linear forwards`;
    this.autoTimer = window.setTimeout(() => this.next(), secs * 1000);
  }

  private preload(pageIdx: number): void {
    const page = this.pages[pageIdx];
    if (!page || page.kind !== "panels") return;
    for (const bi of page.beats) {
      const im = new Image();
      im.decoding = "async";
      im.src = storyUrl(this.m.slug, this.m.beats[bi].still);
    }
  }

  private updateRule(): void {
    const path = this.root.querySelector<SVGPathElement>(".controls-rule path");
    if (!path) return;
    // a single wobbly ink rule above the controls
    let d = "M0 4";
    const r = hash(this.m.slug);
    for (let i = 1; i <= 12; i++) {
      const y = 4 + Math.sin(i * 1.7 + r) * 1.6;
      d += `Q${i * 83.3 - 41} ${4 + Math.cos(i * 2.3 + r) * 2.2} ${i * 83.3} ${y.toFixed(2)}`;
    }
    path.setAttribute("d", d);
  }
}

