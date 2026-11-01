/**
 * Страница регистрации: email, имя и пароль.
 */
import RegisterPage from "./RegisterPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class RegisterPageModel extends BasePageModel
{
    state = {
        params: {},
        email: "",
        name: "",
        password: "",
        confirm: "",
        error: "",
        loading: false,
    };

    getComponent()
    {
        return RegisterPage;
    }

    getTitle()
    {
        return "Регистрация";
    }

    async init()
    {
        if (localStorage.getItem("access_token")) {
            await this.$layout.getRouter().open("chats", {}, { replace: true });
        }
    }

    /**
     * Отправить форму регистрации.
     */
    async submit()
    {
        if (this.state.loading) {
            return;
        }

        if (this.state.password !== this.state.confirm) {
            this.state.error = "Пароли не совпадают";
            return;
        }

        this.state.loading = true;
        this.state.error = "";

        try {
            const data = await api.register(
                this.state.email.trim(),
                this.state.name.trim(),
                this.state.password,
            );
            this.state.password = "";
            this.state.confirm = "";
            this.$layout.state.user = data.user || null;
            await this.$layout.getRouter().open("chats");
        } catch (error) {
            this.state.error = error.message || "Ошибка регистрации";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Перейти ко входу.
     */
    goLogin()
    {
        return this.$layout.getRouter().open("login");
    }
}
