import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/storage": { target: "http://localhost:8000", changeOrigin: true },
      "/admin": { target: "http://localhost:5175", changeOrigin: true },
      "/sign": { target: "http://localhost:5174", changeOrigin: true },
    },
  },
});
