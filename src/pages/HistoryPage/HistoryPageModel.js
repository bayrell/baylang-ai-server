/**
 * История чатов: select list последних 50 чатов, поиск и фильтр.
 */
import HistoryPage from "./HistoryPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class HistoryPageModel extends BasePageModel
{
    state = {
        params: {},
        chats: [],
        total: 0,
        query: "",
        filter: "all", // 'all' | 'today' | 'week' | 'month'
        limit: 50,
        offset: 0,
        agents: [],
        selectedAgent: null,
        loading: false,
        error: "",
    };

    _timer = null;

    getComponent()
    {
        return HistoryPage;
    }

    getTitle()
    {
        return "История чатов";
    }

    async init()
    {
        await this.load();
        await this.loadAgents();
    }

    /**
     * Загрузить список чатов с учётом поиска и фильтра.
     */
    async load()
    {
        this.state.loading = true;
        this.state.error = "";

        try {
            const params = new URLSearchParams({
                q: this.state.query,
                filter: this.state.filter,
                limit: String(this.state.limit),
                offset: String(this.state.offset),
            });

            const data = await api.get(`/api/chats?${params.toString()}`);
            this.state.chats = Array.isArray(data.items) ? data.items : [];
            this.state.total = Number(data.total || 0);
        } catch (error) {
            this.state.error = error.message || "Не удалось загрузить чаты";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Отложенная перезагрузка (для поля поиска).
     */
    debouncedLoad()
    {
        if (this._timer) {
            clearTimeout(this._timer);
        }
        this._timer = setTimeout(() => {
            this.state.offset = 0;
            this.load();
        }, 300);
    }

    /**
     * Сбросить фильтр.
     */
    async resetFilter()
    {
        this.state.filter = "all";
        this.state.query = "";
        this.state.offset = 0;
        await this.load();
    }

    /**
     * Загрузить список агентов (для выбора при создании чата).
     */
    async loadAgents()
    {
        try {
            const agents = await api.get("/api/agents");
            this.state.agents = Array.isArray(agents) ? agents : [];
        } catch (error) {
            this.state.agents = [];
        }
    }

    /**
     * Создать новый чат и открыть его.
     */
    async createChat()
    {
        try {
            const chat = await api.post("/api/chats", {
                title: "Новый чат",
                agent_id: this.state.selectedAgent,
            });
            await this.$layout.getRouter().open("chat", { id: chat.id });
        } catch (error) {
            this.state.error = error.message || "Не удалось создать чат";
        }
    }

    /**
     * Открыть существующий чат.
     */
    openChat(chat)
    {
        return this.$layout.getRouter().open("chat", { id: chat.id });
    }

    /**
     * Удалить чат.
     */
    async removeChat(chat)
    {
        if (!window.confirm(`Удалить чат «${chat.title}»?`)) {
            return;
        }

        try {
            await api.delete(`/api/chats/${chat.id}`);
            await this.load();
        } catch (error) {
            this.state.error = error.message || "Не удалось удалить чат";
        }
    }

    /**
     * Форматирование даты.
     */
    formatDate(value)
    {
        if (!value) {
            return "";
        }
        const date = new Date(String(value).replace(" ", "T"));
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }
        return date.toLocaleString("ru-RU", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    }
}
