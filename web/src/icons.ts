// Small hand-drawn icons (slightly irregular paths on purpose). Stroke = currentColor.
const svg = (body: string, vb = "0 0 32 32") =>
  `<svg class="icon" viewBox="${vb}" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;

export const icons = {
  prev: svg(`<path d="M20.5 6.8 10.2 15.6l10.6 9.5"/><path d="M21.6 8.4 13 15.9l8.4 7.4" stroke-width="1.4" opacity=".55"/>`),
  next: svg(`<path d="M11.3 6.6 21.8 16l-10.6 9.4"/><path d="M10.6 8.8 18.9 16.2l-8 7" stroke-width="1.4" opacity=".55"/>`),
  play: svg(`<path d="M10.6 6.9c.1 5.9-.2 12.3.1 18.4L25.1 16.2Z" fill="currentColor" stroke-width="2.2"/>`),
  pause: svg(`<path d="M11.2 7.2c.3 6 .1 11.9 0 17.7M20.8 7c-.2 6.1.2 12 .1 18" stroke-width="3.6"/>`),
  chapters: svg(`<path d="M6.4 8.2c6.6-.3 13.3.2 19.6-.1M6.2 16.1c6.8.2 13.2-.2 19.8 0M6.6 24c6.2-.3 12.9.2 19.1-.1"/><circle cx="4" cy="8.1" r=".6" fill="currentColor"/><circle cx="4" cy="16" r=".6" fill="currentColor"/><circle cx="4.1" cy="24" r=".6" fill="currentColor"/>`),
  fullscreen: svg(`<path d="M5.8 12.1c-.1-2.3.1-4.4-.1-6.4 2.3.2 4.3-.1 6.5.1M20 5.9c2.2.1 4.2-.2 6.3 0-.1 2.1.1 4.3 0 6.4M26.2 20.1c.2 2.1-.1 4.2.1 6.2-2.2-.1-4.3.2-6.4 0M12.1 26.2c-2.2-.1-4.2.1-6.3 0 .1-2.2-.1-4.3 0-6.3"/>`),
  exitFullscreen: svg(`<path d="M12 5.9c0 2.1.2 4.1 0 6.2-2.1.1-4.2-.1-6.2 0M26.1 12.1c-2.1-.1-4.1.1-6.2 0-.1-2.1.1-4.2 0-6.2M19.9 26.2c.1-2.1-.1-4.1 0-6.2 2.1-.1 4.2.1 6.3 0M5.8 19.9c2.1.1 4.1-.1 6.2 0 .1 2.1-.1 4.2.1 6.3"/>`),
  library: svg(`<path d="M5.6 7.1c.2 6.1-.2 12.2.1 18.3M10.4 6.8c-.1 6.2.2 12.4 0 18.6M15.6 9.6l4.8-1.9 6 16.7-4.6 1.9Z"/><path d="M4 26.2c7.9-.2 16.1.1 24.1-.1" stroke-width="2"/>`),
  copy: svg(`<path d="M11.2 10.6c4.9-.2 9.8.2 14.6-.1.2 5.1-.1 10.2.1 15.2-4.8.2-9.8-.1-14.6.1-.2-5 .1-10.1-.1-15.2Z"/><path d="M7.4 21.6c-.2-4.9.1-9.9-.1-14.9 4.8-.2 9.6.1 14.4-.1"/>`),
  check: svg(`<path d="M6.5 16.8c2.4 2 4.4 4.3 6.4 6.7 3.9-5.6 8-10.6 12.8-15.4"/>`),
  download: svg(`<path d="M16.1 5.4c-.2 5.6.2 11.1-.1 16.4M9.6 15.4c2.3 2.2 4.4 4.4 6.5 6.6 2.2-2.4 4.3-4.5 6.6-6.7M6.2 26.3c6.6-.2 13.2.2 19.7-.1"/>`),
  film: svg(`<path d="M5.6 8.4c7-.2 14 .2 20.9-.1.1 5.2-.1 10.4.1 15.6-7 .2-14-.1-20.9.1-.2-5.2.1-10.4-.1-15.6Z"/><path d="M13.4 12.2c2.6 1.2 5.2 2.6 7.6 4-2.5 1.3-5 2.8-7.6 4 .1-2.6-.1-5.4 0-8Z" fill="currentColor" stroke-width="1.6"/>`),
  back: svg(`<path d="M13.4 8.1 6.2 16l7.4 7.6M7.2 16.1c6.4-.2 12.6.1 18.6-.1"/>`),
  close: svg(`<path d="M8.2 8.1c5.4 5 10.6 10.4 15.7 15.8M23.8 8.3C18.4 13.4 13.3 18.6 8 23.9"/>`),
  restart: svg(`<path d="M8.4 10.9A9.6 9.6 0 1 1 6.8 18"/><path d="M7.6 5.6c.1 1.9-.2 3.6.1 5.5 1.9.1 3.7-.2 5.5 0"/>`),
};
