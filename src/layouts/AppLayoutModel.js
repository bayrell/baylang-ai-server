/**
 * Глобальная модель приложения: хранит роутер и модели всех страниц.
 * Создаётся в main.js и устанавливается в globalProperties Vue.
 */
import { Router } from "@/lib/Router";

import IndexPageModel from "@/pages/IndexPage/IndexPageModel";
import LoginPageModel from "@/pages/LoginPage/LoginPageModel";
import RegisterPageModel from "@/pages/RegisterPage/RegisterPageModel";
import HistoryPageModel from "@/pages/HistoryPage/HistoryPageModel";
import ChatPageModel from "@/pages/ChatPage/ChatPageModel";
import SettingsPageModel from "@/pages/SettingsPage/SettingsPageModel";

export class AppLayoutModel
{
    constructor()
    {
        this.router = new Router(this);
        this.state = {
            ready: false,
            user: null,
        };
    }

    /**
     * Зарегистрировать маршруты приложения.
     */
    register_routes()
    {
        this.router.add("index", "/", IndexPageModel);
        this.router.add("login", "/login", LoginPageModel);
        this.router.add("register", "/register", RegisterPageModel);
        this.router.add("chats", "/chats", HistoryPageModel, { auth: true });
        this.router.add("chat", "/chat/:id", ChatPageModel, { auth: true });
        this.router.add("settings", "/settings", SettingsPageModel, { auth: true });
    }

    /**
     * Инициализация проекта и текущей страницы.
     */
    async init()
    {
        this.register_routes();
        await this.router.init();
        this.state.ready = true;
    }

    /**
     * Модель страницы по имени (или по имени класса модели).
     */
    getPage(name)
    {
        return this.router.getPage(name);
    }

    /**
     * Роутер приложения.
     */
    getRouter()
    {
        return this.router;
    }

    /**
     * Текущий пользователь (из localStorage).
     */
    getUser()
    {
        const raw = localStorage.getItem("user");
        if (!raw) {
            return null;
        }
        try {
            return JSON.parse(raw);
        } catch (error) {
            return null;
        }
    }

    /**
     * Выход из аккаунта.
     */
    async logout()
    {
        const { api } = await import("@/services/api");
        await api.logout();
        this.state.user = null;
        await this.router.open("login");
    }
}

export default AppLayoutModel;
