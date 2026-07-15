import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: { outDir: "../core/static", emptyOutDir: true },
  server: { proxy: { "/tests": "http://127.0.0.1:4319", "/runs": "http://127.0.0.1:4319", "/kdg": "http://127.0.0.1:4319", "/ws": { target: "ws://127.0.0.1:4319", ws: true } } },
});
