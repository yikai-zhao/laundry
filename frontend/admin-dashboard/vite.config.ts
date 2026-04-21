import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || "/admin/",
  server: {
    host: true,
    port: 5175,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/storage": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
