/**
 * Точка входа frontend-приложения.
 *
 * Создаётся глобальная модель AppLayoutModel, регистрируются маршруты
 * и подключается корневой компонент.
 */
import { createApp, reactive } from "vue";

import App from "@/pages/App.vue";
import { AppLayoutModel } from "@/layouts/AppLayoutModel";
import "./assets/main.css";

/* Create layout */
const layout = reactive(new AppLayoutModel());

/* Create app */
const app = createApp(App);
app.config.globalProperties.$layout = layout;

/* Mount app */
app.mount(".root_container");

/* Init layout: маршруты и текущая страница */
layout.init();
