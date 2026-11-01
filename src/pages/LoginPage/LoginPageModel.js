/**
 * Страница входа по email + паролю.
 */
import LoginPage from "./LoginPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class LoginPageModel extends BasePageModel
{
    state = {
        params: {},
        email: "",
        password: "",
        error: "",
        loading: false,
    };

    getComponent()
    {
        return LoginPage;
    }

    getTitle()
    {
        return "Вход";
    }

    async init()
    {
        if (localStorage.getItem("access_token")) {
            await this.$layout.getRouter().open("chats", {}, { replace: true });
        }
    }

    /**
     * Отправить форму входа.
     */
    async submit()
    {
        if (this.state.loading) {
            return;
        }

        this.state.loading = true;
        this.state.error = "";

        try {
            const data = await api.login(this.state.email.trim(), this.state.password);
            this.state.password = "";
            this.$layout.state.user = data.user || null;
            await this.$layout.getRouter().open("chats");
        } catch (error) {
            this.state.error = error.message || "Ошибка входа";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Перейти к регистрации.
     */
    goRegister()
    {
        return this.$layout.getRouter().open("register");
    }
}
