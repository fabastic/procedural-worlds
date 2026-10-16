import { defineConfig } from "vite";

// Static site: everything in public/ (including public/stories/**) is copied
// verbatim to dist/. Hash routing means no server-side routes are needed.
export default defineConfig({
  base: "/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    target: "es2022",
    assetsInlineLimit: 0,
  },
  server: { port: 5173 },
  preview: { port: 4173 },
});
