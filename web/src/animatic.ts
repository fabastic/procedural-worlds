// Animatic: the whole story as one MP4, played full screen.
import { fetchManifest, storyUrl } from "./data";
import { icons } from "./icons";
import { escapeHtml } from "./util";
import type { View } from "./view";

export async function mountAnimatic(main: HTMLElement, slug: string): Promise<View> {
  const m = await fetchManifest(slug);
  const root = document.createElement("section");
  root.className = "animatic";
  root.setAttribute("aria-label", `${m.title}, animatic`);
  const readHref = `#/read/${encodeURIComponent(slug)}`;
  if (!m.animatic) {
    root.innerHTML = `
      <div class="animatic-missing">
        <h1>No animatic yet</h1>
        <p>Export one with <code>tools/blender.sh -b --factory-startup -P tools/export_animatic.py -- story_out/${escapeHtml(slug)}</code>, then <code>npm run sync</code>.</p>
        <a class="btn btn-ink" href="${readHref}">Read the comic instead</a>
      </div>`;
    main.append(root);
    return { destroy: () => root.remove() };
  }
  root.innerHTML = `
    <video class="animatic-video" controls autoplay playsinline muted preload="auto"
      poster="${m.cover ? storyUrl(slug, m.cover) : ""}" src="${storyUrl(slug, m.animatic)}"></video>
    <div class="animatic-bar">
      <a class="btn btn-ghost" href="#/">${icons.back}<span>Library</span></a>
      <h1 class="animatic-title">${escapeHtml(m.title)}</h1>
      <a class="btn btn-ghost" href="${readHref}">${icons.next}<span>Read the comic</span></a>
      <button class="btn btn-ghost" type="button" data-fs>${icons.fullscreen}<span>Full screen</span></button>
    </div>`;
  main.append(root);
  const video = root.querySelector<HTMLVideoElement>("video")!;
  const fs = root.querySelector<HTMLButtonElement>("[data-fs]")!;
  if (!document.fullscreenEnabled) fs.remove();
  fs.addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else root.requestFullscreen().catch(() => video.requestFullscreen?.().catch(() => {}));
  });
  video.play().catch(() => {
    /* autoplay blocked: controls are visible */
  });
  return {
    destroy: () => {
      video.pause();
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      root.remove();
    },
  };
}
