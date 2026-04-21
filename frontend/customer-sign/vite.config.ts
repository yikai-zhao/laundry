import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || "/sign/",
  server: {
    host: true,
    port: 5174,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/storage": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
