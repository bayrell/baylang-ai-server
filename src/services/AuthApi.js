/**
 * API-авторизации: login / register / refresh / logout / me.
 */
import { ApiService } from "./ApiService";

export class AuthApi extends ApiService
{
    /**
     * Обновить access-токен по refresh-токену.
     */
    async refresh()
    {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch(this.buildUrl("/api/auth/refresh"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            localStorage.setItem("access_token", data.access_token);
            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Вход по email + пароль.
     */
    async login(email, password)
    {
        const data = await this.request("POST", "/api/auth/login", { email, password });
        this.saveTokens(data);
        return data;
    }

    /**
     * Регистрация.
     */
    async register(email, name, password)
    {
        const data = await this.request("POST", "/api/auth/register", { email, name, password });
        this.saveTokens(data);
        return data;
    }

    /**
     * Выход: отзыв refresh-токена и очистка localStorage.
     */
    async logout()
    {
        const refreshToken = localStorage.getItem("refresh_token");
        try {
            await this.request("POST", "/api/auth/logout", { refresh_token: refreshToken || "" });
        } catch (error) {
            /* токен мог быть уже отозван — молча выходим */
        }
        this.clearTokens();
    }

    /**
     * Текущий пользователь.
     */
    async me()
    {
        return this.request("GET", "/api/auth/me");
    }

    /**
     * Сохранить токены в localStorage.
     */
    saveTokens(data)
    {
        if (data && data.access_token) {
            localStorage.setItem("access_token", data.access_token);
        }
        if (data && data.refresh_token) {
            localStorage.setItem("refresh_token", data.refresh_token);
        }
        if (data && data.user) {
            localStorage.setItem("user", JSON.stringify(data.user));
        }
    }

    /**
     * Очистить токены.
     */
    clearTokens()
    {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
    }

    /**
     * Есть ли сохранённый access-токен.
     */
    isAuthenticated()
    {
        return Boolean(localStorage.getItem("access_token"));
    }
}

export default AuthApi;
