// Data contract produced by the Blender pipeline (tools/render_story.py).
// index.json:   { stories: [{ slug, title, logline, cover }] }
// manifest.json: see Manifest below. All media paths are relative to the story folder.

export type ShotType = "establishing" | "wide" | "medium" | "close" | "POV" | "low" | "high" | "OTS";

export interface Shot {
  type: string;
  focus?: string;
  camera_move?: string;
  duration_s?: number;
}

export interface DialogueLine {
  speaker: string;
  text: string;
}

export interface Beat {
  id: string;
  scene_id: string;
  shot: Shot;
  caption?: string;
  dialogue?: DialogueLine[];
  still: string;
  clip?: string;
  width?: number;
  height?: number;
}

export interface Scene {
  id: string;
  name: string;
  generator?: string;
  layers?: Record<string, unknown>;
}

export interface Manifest {
  slug: string;
  title: string;
  logline?: string;
  protagonist?: { name: string; eye_height_m?: number };
  cover?: string;
  animatic?: string;
  scenes: Scene[];
  beats: Beat[];
}

export interface StoryIndexEntry {
  slug: string;
  title: string;
  logline?: string;
  cover?: string;
}

const BASE = import.meta.env.BASE_URL;

/** Resolve a manifest-relative media path to a URL the browser can load. */
export function storyUrl(slug: string, rel: string): string {
  if (/^(https?:)?\/\//.test(rel) || rel.startsWith("/") || rel.startsWith("data:")) return rel;
  const clean = rel.replace(/^\.\//, "");
  return `${BASE}stories/${encodeURIComponent(slug)}/${encodeURI(clean)}`;
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  const type = res.headers.get("content-type") ?? "";
  if (type.includes("text/html")) throw new Error(`Expected JSON but got HTML for ${url}`);
  return (await res.json()) as T;
}

let indexCache: Promise<StoryIndexEntry[]> | null = null;

export function fetchIndex(): Promise<StoryIndexEntry[]> {
  indexCache ??= getJson<{ stories?: StoryIndexEntry[] }>(`${BASE}stories/index.json`)
    .then((d) => (Array.isArray(d.stories) ? d.stories.filter((s) => s && typeof s.slug === "string") : []))
    .catch((err) => {
      indexCache = null;
      throw err;
    });
  return indexCache;
}

const manifestCache = new Map<string, Promise<Manifest>>();

export function fetchManifest(slug: string): Promise<Manifest> {
  let p = manifestCache.get(slug);
  if (!p) {
    p = getJson<Partial<Manifest>>(`${BASE}stories/${encodeURIComponent(slug)}/manifest.json`)
      .then((m) => normalizeManifest(m, slug))
      .catch((err) => {
        manifestCache.delete(slug);
        throw err;
      });
    manifestCache.set(slug, p);
  }
  return p;
}

const SHOT_TYPES: Record<string, ShotType> = {
  establishing: "establishing",
  wide: "wide",
  medium: "medium",
  close: "close",
  closeup: "close",
  "close-up": "close",
  close_up: "close",
  pov: "POV",
  low: "low",
  high: "high",
  ots: "OTS",
};

export function shotType(beat: Beat): ShotType {
  return SHOT_TYPES[String(beat.shot?.type ?? "").toLowerCase()] ?? "medium";
}

/** Be lenient with what the pipeline hands us: fill defaults, drop beats without a still. */
export function normalizeManifest(raw: Partial<Manifest>, slug: string): Manifest {
  const beats: Beat[] = (Array.isArray(raw.beats) ? raw.beats : [])
    .filter((b): b is Beat => !!b && typeof b.still === "string" && b.still.length > 0)
    .map((b, i) => ({
      ...b,
      id: b.id || `b${String(i + 1).padStart(2, "0")}`,
      scene_id: b.scene_id || "scene",
      shot: { duration_s: 3, ...(b.shot ?? {}), type: b.shot?.type || "medium" },
      dialogue: Array.isArray(b.dialogue)
        ? b.dialogue.filter((d) => d && typeof d.text === "string" && d.text.trim()).map((d) => ({
            speaker: String(d.speaker ?? "").trim(),
            text: d.text.trim(),
          }))
        : [],
      caption: typeof b.caption === "string" && b.caption.trim() ? b.caption.trim() : undefined,
    }));
  const scenes: Scene[] = (Array.isArray(raw.scenes) ? raw.scenes : []).filter((s) => s && s.id);
  for (const b of beats) {
    if (!scenes.some((s) => s.id === b.scene_id)) scenes.push({ id: b.scene_id, name: humanize(b.scene_id) });
  }
  // Keep scene order as the beats visit them (chapters follow reading order).
  const order = [...new Set(beats.map((b) => b.scene_id))];
  scenes.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
  return {
    slug: raw.slug || slug,
    title: raw.title || humanize(slug),
    logline: raw.logline,
    protagonist: raw.protagonist,
    cover: raw.cover || beats[0]?.still,
    animatic: raw.animatic || undefined,
    scenes: scenes.filter((s) => order.includes(s.id)),
    beats,
  };
}

export function humanize(id: string): string {
  const s = id.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Seconds a reader needs for a beat: its shot duration plus reading time for its text. */
export function dwellSeconds(beat: Beat): number {
  const texts = [beat.caption ?? "", ...(beat.dialogue ?? []).map((d) => d.text)].filter(Boolean);
  const words = texts.join(" ").split(/\s+/).filter(Boolean).length;
  const reading = words / 3.3 + texts.length * 0.5;
  return Math.max(beat.shot.duration_s ?? 3, 1.5) + reading;
}

export function storyMinutes(m: Manifest): number {
  return m.beats.reduce((t, b) => t + dwellSeconds(b), 0) / 60;
}
