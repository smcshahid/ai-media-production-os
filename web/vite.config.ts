/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  test: {
    environment: "jsdom",
    // Start tests on /login so the client's 401 redirect guard is a no-op
    // (jsdom does not implement navigation).
    environmentOptions: { jsdom: { url: "http://localhost:5173/login" } },
    globals: true,
    setupFiles: ["./src/tests/setup.ts"],
    css: false,
  },
});
