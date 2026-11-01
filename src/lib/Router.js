/**
 * Простой роутер проекта.
 *
 * Регистрирует url, name и модель страницы, умеет подставлять параметры
 * (`/chat/:id`), искать маршрут по url и открывать страницы через
 * History API (`pushState`).
 */
export class Router
{
    constructor(layout = null)
    {
        this.layout = layout;
        this.routes = [];
        this.pages = {};
        this.current = null;
    }

    /**
     * Зарегистрировать новый route и модель страницы.
     *
     * @param {string} name     Имя страницы (например "chat").
     * @param {string} url      Шаблон url (например "/chat/:id").
     * @param {Function} ModelClass Класс модели страницы.
     * @param {object} options  Доп. настройки ({ auth: true }).
     */
    add(name, url, ModelClass, options = {})
    {
        const route = {
            name,
            url,
            ...compile(url),
            ModelClass,
            options,
        };

        this.routes.push(route);

        const model = new ModelClass();
        model.$layout = this.layout;
        this.pages[name] = model;
        this.pages[ModelClass.name] = model;

        return route;
    }

    /**
     * Вернуть url для маршрута с подстановкой параметров.
     */
    url(name, params = {})
    {
        const route = this.routes.find(item => item.name === name);
        if (!route) {
            return "/";
        }

        return route.url.replace(PARAM_PATTERN, (match, key) => {
            const value = params && params[key] !== undefined && params[key] !== null
                ? params[key]
                : "";
            return encodeURIComponent(String(value));
        });
    }

    /**
     * Найти route по url. Возвращает { name, params, route } либо null.
     */
    find(url)
    {
        const path = String(url || "").split("?")[0].split("#")[0] || "/";

        for (const route of this.routes) {
            const match = route.regex.exec(path);
            if (match) {
                const params = {};
                route.names.forEach((name, index) => {
                    params[name] = decodeURIComponent(match[index + 1]);
                });
                return { name: route.name, params, route };
            }
        }

        return null;
    }

    /**
     * Открыть страницу по имени.
     */
    async open(name, params = {}, options = {})
    {
        return this.openUrl(this.url(name, params), { ...options, params });
    }

    /**
     * Открыть страницу по url.
     */
    async openUrl(url, options = {})
    {
        const found = this.find(url);
        if (!found) {
            window.location.href = url;
            return null;
        }

        const target = this.url(found.name, found.params);
        if (window.location.pathname !== target) {
            if (options.replace) {
                window.history.replaceState({}, "", target);
            } else {
                window.history.pushState({}, "", target);
            }
        }

        return this.show(found.name, found.params);
    }

    /**
     * Показать страницу (без изменения истории).
     */
    async show(name, params = {})
    {
        const route = this.routes.find(item => item.name === name);
        if (!route) {
            return null;
        }

        // Защищённые страницы доступны только авторизованным пользователям.
        if (route.options && route.options.auth && !this.isAuthenticated()) {
            return this.open("login", {}, { replace: true });
        }

        const model = this.pages[name];
        if (!model) {
            return null;
        }

        this.current = { name, params: params || {} };

        if (model.state) {
            model.state.params = { ...(model.state.params || {}), ...(params || {}) };
        }

        if (typeof model.init === "function") {
            await model.init(model.state ? model.state.params : params);
        }

        return model;
    }

    /**
     * Инициализация роутера: текущая страница и обработка back/forward.
     */
    async init()
    {
        window.addEventListener("popstate", () => {
            this.openUrl(window.location.pathname, { replace: true });
        });

        const found = this.find(window.location.pathname);
        if (!found) {
            await this.open("index", {}, { replace: true });
            return;
        }

        await this.show(found.name, found.params);
    }

    /**
     * Имя текущей страницы.
     */
    getCurrentPage()
    {
        return this.current ? this.current.name : null;
    }

    /**
     * Есть ли access-токен в localStorage.
     */
    isAuthenticated()
    {
        return Boolean(localStorage.getItem("access_token"));
    }

    /**
     * Модель страницы по имени (или по имени класса модели).
     */
    getPage(name)
    {
        return this.pages[name] || null;
    }
}

const PARAM_PATTERN = /:([A-Za-z0-9_]+)/g;

/**
 * Скомпилировать шаблон url в регулярное выражение.
 */
function compile(url)
{
    const names = [];
    const escaped = url.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = escaped.replace(PARAM_PATTERN, (match, name) => {
        names.push(name);
        return "([^/]+)";
    });

    return { names, regex: new RegExp("^" + pattern + "/?$") };
}

export default Router;
