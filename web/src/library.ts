// Library: a shelf of inked cover cards, one per story in stories/index.json.
import { fetchIndex, fetchManifest, storyMinutes, storyUrl, type StoryIndexEntry } from "./data";
import { icons } from "./icons";
import { blotPath, hash, inkBorder, makeBlot } from "./ink";
import { escapeHtml } from "./util";
import type { View } from "./view";

export async function mountLibrary(main: HTMLElement): Promise<View> {
  const root = document.createElement("div");
  root.className = "library";
  const heroBlot = blotPath(makeBlot(424242, 1.1), 120, 120, 70);
  root.innerHTML = `
    <header class="lib-hero">
      <svg class="lib-hero-blot" viewBox="0 0 240 240" aria-hidden="true"><path d="${heroBlot}"/></svg>
      <p class="kicker">The library</p>
      <h1 class="lib-title">Stories told through places, inked by hand-made rules, <em>quietly moving.</em></h1>
      <p class="lib-lede">Every panel is a Blender scene drawn in ink: no actors, only rooms, coastlines and streets, narration boxes and voices from just off the page.</p>
    </header>
    <section class="shelf" aria-label="Stories"><p class="shelf-loading">Inking the covers&hellip;</p></section>
    <aside class="lib-new">
      <p>Have a story of your own?</p>
      <a class="btn btn-ink" href="#/new">${icons.download}<span>Paste your story</span></a>
    </aside>`;
  main.append(root);
  const shelf = root.querySelector<HTMLElement>(".shelf")!;

  let stories: StoryIndexEntry[] = [];
  try {
    stories = await fetchIndex();
  } catch (err) {
    shelf.innerHTML = `<div class="empty"><p>Couldn&rsquo;t read <code>stories/index.json</code>.</p><p class="muted">${escapeHtml(String((err as Error).message))}</p><p>Run <code>npm run sync</code> in <code>web/</code> after rendering a story.</p></div>`;
    return { destroy: () => root.remove() };
  }
  if (!stories.length) {
    shelf.innerHTML = `<div class="empty"><p>No stories on the shelf yet.</p><a class="btn btn-ink" href="#/new">Paste your first story</a></div>`;
    return { destroy: () => root.remove() };
  }

  shelf.innerHTML = "";
  const list = document.createElement("ul");
  list.className = "shelf-list";
  shelf.append(list);
  stories.forEach((s, i) => list.append(card(s, i)));

  // Fill in details (panel count, duration, animatic link) from each manifest.
  stories.forEach((s) => {
    fetchManifest(s.slug)
      .then((m) => {
        const li = list.querySelector<HTMLElement>(`[data-slug="${CSS.escape(s.slug)}"]`);
        if (!li) return;
        const meta = li.querySelector(".card-meta")!;
        const mins = Math.max(1, Math.round(storyMinutes(m)));
        meta.textContent = `${m.beats.length} panels · ${m.scenes.length} chapter${m.scenes.length === 1 ? "" : "s"} · about ${mins} min`;
        if (m.animatic) {
          const a = document.createElement("a");
          a.className = "btn";
          a.href = `#/animatic/${encodeURIComponent(s.slug)}`;
          a.dataset.fullscreen = "";
          a.innerHTML = `${icons.film}<span>Animatic</span>`;
          li.querySelector(".card-actions")!.append(a);
        }
      })
      .catch(() => {
        /* a broken manifest still leaves the card readable from index.json */
      });
  });

  return { destroy: () => root.remove() };
}

function card(s: StoryIndexEntry, i: number): HTMLElement {
  const li = document.createElement("li");
  li.className = "card";
  li.dataset.slug = s.slug;
  li.style.setProperty("--tilt", `${((hash(s.slug) % 100) / 100 - 0.5) * 1.6}deg`);
  li.style.setProperty("--i", String(i));
  const href = `#/read/${encodeURIComponent(s.slug)}`;
  const b = inkBorder(320, 180, hash(s.slug + "/card"), 0.9);
  const cover = s.cover ? storyUrl(s.slug, s.cover) : "";
  li.innerHTML = `
    <a class="card-cover" href="${href}" tabindex="-1" aria-hidden="true">
      <span class="card-media">${cover ? `<img alt="" loading="lazy" src="${cover}">` : ""}</span>
      <svg class="card-border" viewBox="0 0 320 180" preserveAspectRatio="none">
        <path d="${b.main}" stroke-width="5" vector-effect="non-scaling-stroke"/>
        <path d="${b.weight}" stroke-width="2.6" vector-effect="non-scaling-stroke"/>
      </svg>
    </a>
    <div class="card-body">
      <h2 class="card-title"><a href="${href}">${escapeHtml(s.title || s.slug)}</a></h2>
      ${s.logline ? `<p class="card-logline">${escapeHtml(s.logline)}</p>` : ""}
      <p class="card-meta">&nbsp;</p>
      <div class="card-actions">
        <a class="btn btn-ink" href="${href}" aria-label="Read ${escapeHtml(s.title || s.slug)}">${icons.next}<span>Read</span></a>
      </div>
    </div>`;
  return li;
}
