// "Paste your story": collect the text, save it as my_story.txt, show the local pipeline.
import { icons } from "./icons";
import { escapeHtml, store } from "./util";
import type { View } from "./view";

const DRAFT_KEY = "pw.story-draft";

const STEPS: { title: string; cmd: string; note: string }[] = [
  {
    title: "Break it into beats",
    cmd: "python story/parse.py my_story.txt -o story/examples/my_story.json",
    note: "Splits the text into scenes and beats: setting, shot, focus, a narration caption and off-panel dialogue. With <code>GEMINI_API_KEY</code> set it uses the smart parser; without it, an offline keyword parser does the job.",
  },
  {
    title: "Build and ink every place",
    cmd: "tools/blender.sh -b --factory-startup -P tools/render_story.py -- story/examples/my_story.json",
    note: "Blender generates each setting, inks it and renders every beat as a short looping clip plus a still into <code>story_out/my-story/</code>.",
  },
  {
    title: "Cut the animatic (optional)",
    cmd: "tools/blender.sh -b --factory-startup -P tools/export_animatic.py -- story_out/my-story",
    note: "One MP4 of the whole story with captions and ink transitions.",
  },
  {
    title: "Read it here",
    cmd: "cd web && npm run sync && npm run dev",
    note: "Copies <code>story_out/</code> into the player and serves it at <code>localhost:5173</code>. Your story appears in the library.",
  },
];

const EXAMPLE = `The Night Ferry

The harbour was empty except for the ferry, its one lamp swinging in the wind.

Inside the ticket office, a radio crackled on the counter. "Last crossing cancelled," it said. "Storm warning for the whole coast."

Ines locked the office anyway and walked down to the pier. The water was black and loud.

Out past the breakwater, a light blinked three times. Then again.

"Someone's out there," she said to nobody, and untied the ferry.`;

export function mountPaste(main: HTMLElement): View {
  const root = document.createElement("div");
  root.className = "paste";
  root.innerHTML = `
    <header class="paste-head">
      <p class="kicker">Paste your story</p>
      <h1 class="paste-title">Any story, told as an inked comic that quietly moves.</h1>
      <p class="paste-lede">Generation runs on your own machine: it needs Blender and takes a few minutes per story. Nothing you type here leaves your browser.</p>
    </header>
    <div class="paste-grid">
      <section class="paste-editor" aria-labelledby="step-paste">
        <h2 id="step-paste" class="step-title"><span class="step-num">1</span> Paste or write it</h2>
        <div class="sheet">
          <label class="sr-only" for="story-text">Story text</label>
          <textarea id="story-text" spellcheck="true" placeholder="Once, on a rock in the middle of the sea, there was a lighthouse..."></textarea>
        </div>
        <div class="editor-bar">
          <p class="editor-count" aria-live="polite" data-count>0 words</p>
          <div class="editor-actions">
            <button class="btn btn-ghost" type="button" data-example>Use an example</button>
            <button class="btn btn-ghost" type="button" data-clear>Clear</button>
            <button class="btn btn-ink" type="button" data-save disabled>${icons.download}<span>Save story text</span></button>
          </div>
        </div>
        <p class="editor-hint">Saves <code>my_story.txt</code>. Put it in the repository root, then run the steps.</p>
        <aside class="tips">
          <h3>What reads well</h3>
          <ul>
            <li>Places and things: a kitchen, a harbour, an alley, a lighthouse. There are no drawn characters, so the camera tells the story through settings, objects and point of view.</li>
            <li>Dialogue in quotes becomes speech balloons from just off the panel.</li>
            <li>Short paragraphs become beats; a new place starts a new chapter.</li>
          </ul>
        </aside>
      </section>
      <section class="paste-steps" aria-labelledby="step-run">
        <h2 id="step-run" class="step-title"><span class="step-num">2</span> Make it, locally</h2>
        <ol class="steps">
          ${STEPS.map(
            (s, i) => `
            <li class="step">
              <h3><span class="step-letter">${String.fromCharCode(97 + i)}</span> ${escapeHtml(s.title)}</h3>
              <div class="code">
                <pre><code>${escapeHtml(s.cmd)}</code></pre>
                <button class="copy" type="button" data-copy="${escapeHtml(s.cmd)}" aria-label="Copy command: ${escapeHtml(s.title)}">${icons.copy}<span>Copy</span></button>
              </div>
              <p class="step-note">${s.note}</p>
            </li>`,
          ).join("")}
        </ol>
        <p class="key-note"><strong>GEMINI_API_KEY</strong> enables the smart parser (better scene splits, shots and dialogue). Without it the offline keyword parser is used, so everything still works with no account and no network.</p>
      </section>
    </div>`;
  main.append(root);

  const ta = root.querySelector<HTMLTextAreaElement>("#story-text")!;
  const count = root.querySelector<HTMLElement>("[data-count]")!;
  const save = root.querySelector<HTMLButtonElement>("[data-save]")!;

  const update = () => {
    const words = ta.value.trim() ? ta.value.trim().split(/\s+/).length : 0;
    const paras = ta.value.split(/\n\s*\n/).filter((p) => p.trim()).length;
    count.textContent = `${words} word${words === 1 ? "" : "s"}${paras ? ` · ${paras} paragraph${paras === 1 ? "" : "s"}` : ""}`;
    save.disabled = !ta.value.trim();
    store.set(DRAFT_KEY, ta.value);
  };
  ta.value = store.get(DRAFT_KEY) ?? "";
  ta.addEventListener("input", update);
  update();

  root.addEventListener("click", async (e) => {
    const t = e.target as HTMLElement;
    if (t.closest("[data-example]")) {
      ta.value = EXAMPLE;
      update();
      ta.focus();
    } else if (t.closest("[data-clear]")) {
      ta.value = "";
      update();
      ta.focus();
    } else if (t.closest("[data-save]")) {
      download("my_story.txt", ta.value.replace(/\r\n/g, "\n").trimEnd() + "\n");
    } else {
      const btn = t.closest<HTMLButtonElement>("[data-copy]");
      if (btn) {
        const ok = await copy(btn.dataset.copy ?? "");
        const label = btn.querySelector("span")!;
        btn.classList.toggle("is-copied", ok);
        label.textContent = ok ? "Copied" : "Select & copy";
        btn.querySelector("svg")!.outerHTML = ok ? icons.check : icons.copy;
        setTimeout(() => {
          btn.classList.remove("is-copied");
          label.textContent = "Copy";
          btn.querySelector("svg")!.outerHTML = icons.copy;
        }, 1600);
        if (!ok) selectText(btn.parentElement!.querySelector("code")!);
      }
    }
  });

  return { destroy: () => root.remove() };
}

function download(name: string, text: string): void {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function copy(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.append(ta);
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch {
      ok = false;
    }
    ta.remove();
    return ok;
  }
}

function selectText(el: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  sel?.removeAllRanges();
  sel?.addRange(range);
}
