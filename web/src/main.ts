import "@fontsource/bangers/400.css";
import "@fontsource/patrick-hand/400.css";
import "./styles/base.css";
import "./styles/reader.css";
import "./styles/pages.css";

import { mountAnimatic } from "./animatic";
import { wobblyRule } from "./ink";
import { mountLibrary } from "./library";
import { mountPaste } from "./paste";
import { mountReader } from "./reader";
import { escapeHtml } from "./util";
import type { View } from "./view";

type Route =
  | { name: "library" }
  | { name: "new" }
  | { name: "read"; slug: string; beat?: string }
  | { name: "animatic"; slug: string }
  | { name: "missing"; path: string };

function parse(hash: string): Route {
  const path = hash.replace(/^#\/?/, "");
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  if (!parts.length) return { name: "library" };
  if (parts[0] === "new") return { name: "new" };
  if (parts[0] === "read" && parts[1]) return { name: "read", slug: parts[1], beat: parts[2] };
  if (parts[0] === "animatic" && parts[1]) return { name: "animatic", slug: parts[1] };
  return { name: "missing", path };
}

const app = document.getElementById("app")!;
app.innerHTML = `
  <header class="topbar">
    <a class="brand" href="#/" aria-label="Procedural Worlds, library">
      <svg class="brand-blot" viewBox="0 0 64 64" aria-hidden="true"><path d="M32 9c7 1 9 8 15 9s10 7 7 14-1 12-7 16-12 8-18 6-12-3-15-10-5-13-1-19 9-6 11-11 3-6 8-5z"/><circle cx="54" cy="12" r="3"/><circle cx="10" cy="54" r="2"/></svg>
      <span class="brand-name">Procedural Worlds</span>
    </a>
    <nav class="topnav" aria-label="Main">
      <a href="#/" data-nav="library">Library</a>
      <a href="#/new" data-nav="new">Paste<span class="nav-long"> your story</span></a>
    </nav>
    <svg class="topbar-rule" viewBox="0 0 1200 8" preserveAspectRatio="none" aria-hidden="true"><path d="${wobblyRule(1200, 4, 7, 1.1)}"/></svg>
  </header>
  <main id="main" class="main" tabindex="-1"></main>`;

const main = app.querySelector<HTMLElement>("#main")!;
let view: View | null = null;
let token = 0;

async function render(): Promise<void> {
  const route = parse(location.hash);
  const my = ++token;
  view?.destroy();
  view = null;
  main.replaceChildren();
  document.body.dataset.route = route.name;
  app.querySelectorAll<HTMLAnchorElement>("[data-nav]").forEach((a) => {
    const active = a.dataset.nav === route.name;
    a.classList.toggle("is-active", active);
    if (active) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  try {
    let v: View;
    switch (route.name) {
      case "library":
        document.title = "Procedural Worlds";
        v = await mountLibrary(main);
        break;
      case "new":
        document.title = "Paste your story · Procedural Worlds";
        v = mountPaste(main);
        break;
      case "read":
        document.title = "Reading · Procedural Worlds";
        v = await mountReader(main, route.slug, route.beat);
        break;
      case "animatic":
        document.title = "Animatic · Procedural Worlds";
        v = await mountAnimatic(main, route.slug);
        break;
      default:
        v = notFound(main, `There is no page at #/${route.path}.`);
    }
    if (my !== token) {
      v.destroy();
      return;
    }
    view = v;
    if (route.name === "library" || route.name === "new") {
      main.querySelector<HTMLElement>("h1")?.setAttribute("tabindex", "-1");
    }
  } catch (err) {
    if (my !== token) return;
    main.replaceChildren();
    view = notFound(main, (err as Error).message || String(err));
  }
}

function notFound(host: HTMLElement, message: string): View {
  const el = document.createElement("div");
  el.className = "notfound";
  el.innerHTML = `
    <h1 class="notfound-title">Blot!</h1>
    <p>${escapeHtml(message)}</p>
    <a class="btn btn-ink" href="#/">Back to the library</a>`;
  host.append(el);
  return { destroy: () => el.remove() };
}

// Links marked data-fullscreen (animatic) ask for full screen inside the click gesture.
document.addEventListener("click", (e) => {
  const a = (e.target as HTMLElement).closest<HTMLAnchorElement>("a[data-fullscreen]");
  if (a && document.fullscreenEnabled && !document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  }
});

let lastRoute = "";
window.addEventListener("hashchange", () => {
  // the reader rewrites the hash as you read (replaceState, no event); only re-render real navigations
  const r = parse(location.hash);
  const key = r.name === "read" ? `read/${r.slug}` : location.hash;
  if (key === lastRoute && r.name === "read") return;
  lastRoute = key;
  void render();
});
lastRoute = (() => {
  const r = parse(location.hash);
  return r.name === "read" ? `read/${r.slug}` : location.hash;
})();
void render();
