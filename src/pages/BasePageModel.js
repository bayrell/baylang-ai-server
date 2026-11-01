/**
 * Базовый класс модели страницы.
 *
 * Модель хранит state, данные и бизнес-логику; компонент только рендерит
 * состояние и проксирует события.
 */
export class BasePageModel
{
    constructor()
    {
        this.state = {
            params: {},
        };
        this.$layout = null;
    }

    /**
     * Vue-компонент страницы.
     */
    getComponent()
    {
        return null;
    }

    /**
     * Заголовок страницы.
     */
    getTitle()
    {
        return "";
    }

    /**
     * Инициализация страницы (загрузка данных).
     */
    async init(params = {})
    {
        this.state.params = params || {};
    }

    /**
     * Переход на другую страницу.
     */
    navigate(name, params = {})
    {
        return this.$layout.getRouter().open(name, params);
    }
}

export default BasePageModel;
