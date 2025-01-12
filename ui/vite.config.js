import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  root: "temboardui/static/src",
  base: "/static/",
  server: {
    origin: "http://localhost:5173",
    port: 5173,
  },
  build: {
    manifest: true,
    outDir: "..",
    emptyOutDir: false,
    assetsDir: ".",
    rollupOptions: {
      input: {
        activity: "/activity.js",
        home: "/home.js",
        temboard: "/temboard.js",
        "settings.instance": "/settings.instance.js",
        "settings.group": "/settings.group.js",
        statements: "/statements.js",
      },
    },
  },
  resolve: {
    alias: {
      vue: "vue/dist/vue.esm.js",
    },
  },
});
