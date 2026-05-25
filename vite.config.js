import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "engine/web/static/js",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        app: "engine/web/react/main.tsx",
        "theme-init": "engine/web/react/theme-init.js",
      },
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
})
