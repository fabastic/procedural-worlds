#!/usr/bin/env node
// Copy rendered stories from story_out/<slug>/ into public/stories/<slug>/ and rebuild index.json.
//
//   npm run sync                         # reads ../story_out (repo root)
//   npm run sync -- --from /abs/story_out
//   STORY_OUT=/abs/story_out npm run sync
//
// Copies manifest.json, beats/**/still.jpg, beats/**/clip.mp4, animatic.mp4 (if present)
// and any other media the manifest references. The demo story is listed only when no real
// story exists. A missing story_out/ is not an error.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicStories = path.join(webDir, "public", "stories");
const DEMO = "demo";

function argValue(name) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  const eq = process.argv.find((a) => a.startsWith(`${name}=`));
  return eq ? eq.slice(name.length + 1) : undefined;
}

const fromArg = argValue("--from") ?? process.argv.slice(2).find((a) => !a.startsWith("--"));
const storyOut = path.resolve(webDir, fromArg ?? process.env.STORY_OUT ?? path.join("..", "story_out"));

const log = (...a) => console.log("[sync]", ...a);
const warn = (...a) => console.warn("[sync] warning:", ...a);

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    warn(`could not read ${file}: ${err.message}`);
    return null;
  }
}

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

function isInside(parent, child) {
  const rel = path.relative(parent, child);
  return rel && !rel.startsWith("..") && !path.isAbsolute(rel);
}

function copyStory(srcDir, slug) {
  const manifestPath = path.join(srcDir, "manifest.json");
  const manifest = readJson(manifestPath);
  if (!manifest || !Array.isArray(manifest.beats)) {
    warn(`skipping ${slug}: manifest.json has no beats array`);
    return false;
  }
  const dest = path.join(publicStories, slug);
  fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(dest, { recursive: true });

  const files = new Set(["manifest.json"]);
  for (const f of walk(path.join(srcDir, "beats"))) {
    const base = path.basename(f).toLowerCase();
    if (base === "still.jpg" || base === "clip.mp4") files.add(path.relative(srcDir, f));
  }
  if (fs.existsSync(path.join(srcDir, "animatic.mp4"))) files.add("animatic.mp4");
  // anything else the manifest points at (cover, custom still/clip names)
  const refs = [manifest.cover, manifest.animatic];
  for (const b of manifest.beats) refs.push(b?.still, b?.clip);
  for (const ref of refs) {
    if (typeof ref !== "string" || /^(https?:|data:|\/)/.test(ref)) continue;
    const abs = path.resolve(srcDir, ref);
    if (isInside(srcDir, abs) && fs.existsSync(abs)) files.add(path.relative(srcDir, abs));
  }

  let bytes = 0;
  const missing = [];
  for (const rel of files) {
    const from = path.join(srcDir, rel);
    const to = path.join(dest, rel);
    fs.mkdirSync(path.dirname(to), { recursive: true });
    fs.copyFileSync(from, to);
    bytes += fs.statSync(to).size;
  }
  for (const b of manifest.beats) {
    if (b?.still && !files.has(path.normalize(b.still))) missing.push(b.still);
  }
  if (manifest.animatic && !files.has(path.normalize(manifest.animatic))) {
    warn(`${slug}: manifest lists animatic "${manifest.animatic}" but the file is missing (the player hides the link)`);
  }
  if (missing.length) warn(`${slug}: ${missing.length} still(s) missing: ${missing.slice(0, 4).join(", ")}${missing.length > 4 ? ", ..." : ""}`);
  const clips = [...files].filter((f) => f.endsWith("clip.mp4")).length;
  log(`${slug}: ${manifest.beats.length} beats, ${clips} clips, ${(bytes / 1048576).toFixed(1)} MB`);
  return true;
}

function main() {
  fs.mkdirSync(publicStories, { recursive: true });
  const synced = [];
  if (!fs.existsSync(storyOut)) {
    log(`no story_out at ${storyOut}; keeping the stories already in public/stories`);
  } else {
    log(`reading ${storyOut}`);
    for (const entry of fs.readdirSync(storyOut, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const src = path.join(storyOut, entry.name);
      if (!fs.existsSync(path.join(src, "manifest.json"))) continue;
      if (copyStory(src, entry.name)) synced.push(entry.name);
    }
    if (!synced.length) log("no story folders with a manifest.json found");
  }

  // Rebuild index.json from every valid story in public/stories.
  const stories = [];
  for (const entry of fs.readdirSync(publicStories, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const m = readJson(path.join(publicStories, entry.name, "manifest.json"));
    if (!m || !Array.isArray(m.beats) || !m.beats.length) continue;
    stories.push({
      slug: entry.name,
      title: m.title || entry.name,
      logline: m.logline || "",
      cover: m.cover || m.beats[0]?.still || "",
    });
  }
  const real = stories.filter((s) => s.slug !== DEMO);
  const listed = (real.length ? real : stories).sort((a, b) => a.title.localeCompare(b.title));
  fs.writeFileSync(path.join(publicStories, "index.json"), JSON.stringify({ stories: listed }, null, 2) + "\n");
  log(`index.json: ${listed.map((s) => s.slug).join(", ") || "(empty)"}${real.length && stories.length > real.length ? " (demo hidden)" : ""}`);
}

main();
