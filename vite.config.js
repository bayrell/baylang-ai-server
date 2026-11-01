import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
    plugins: [vue()],

    resolve: {
        alias: {
            "@": path.resolve(__dirname, "src"),
        },
    },

    build: {
        // Сборка складывается в src/dist и раздаётся FastAPI-приложением.
        outDir: "src/dist",
        emptyOutDir: true,
        assetsDir: "assets",
    },

    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: process.env.API_URL || "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
});
