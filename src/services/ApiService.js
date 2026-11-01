/**
 * Базовый HTTP-клиент: JSON-запросы, заголовок Authorization и
 * автоматическое обновление access-токена по 401-ответу.
 */
export class ApiService
{
    constructor(baseUrl = "")
    {
        this.baseUrl = String(baseUrl || "").replace(/\/$/, "");
    }

    /**
     * Полный url с учётом базового адреса.
     */
    buildUrl(url)
    {
        return `${this.baseUrl}${url}`;
    }

    /**
     * Выполнить запрос. При 401 пробует обновить токен и повторить запрос.
     */
    async request(method, url, body = null, options = {})
    {
        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        };

        const token = localStorage.getItem("access_token");
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        let response;
        try {
            response = await fetch(this.buildUrl(url), {
                method,
                headers,
                body: body === null || body === undefined ? undefined : JSON.stringify(body),
                signal: options.signal,
            });
        } catch (error) {
            if (error && error.name === "AbortError") {
                throw error;
            }
            throw new Error("Сервер недоступен");
        }

        if (response.status === 401 && !options.retried) {
            const refreshed = await this.refresh();
            if (refreshed) {
                return this.request(method, url, body, { ...options, retried: true });
            }
        }

        if (!response.ok) {
            throw new Error(await this.parseError(response));
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    /**
     * Разобрать тело ошибки.
     */
    async parseError(response)
    {
        try {
            const data = await response.json();
            if (data && data.detail) {
                if (typeof data.detail === "string") {
                    return data.detail;
                }
                if (Array.isArray(data.detail) && data.detail.length) {
                    return data.detail[0].msg || "Ошибка запроса";
                }
            }
        } catch (error) {
            /* тело ответа не JSON */
        }

        return `Ошибка запроса (${response.status})`;
    }

    /**
     * Обновить access-токен. Переопределяется в AuthApi.
     */
    async refresh()
    {
        return false;
    }

    get(url, options = {}) { return this.request("GET", url, null, options); }
    post(url, body = null, options = {}) { return this.request("POST", url, body, options); }
    put(url, body = null, options = {}) { return this.request("PUT", url, body, options); }
    patch(url, body = null, options = {}) { return this.request("PATCH", url, body, options); }
    delete(url, options = {}) { return this.request("DELETE", url, null, options); }
}

export default ApiService;
