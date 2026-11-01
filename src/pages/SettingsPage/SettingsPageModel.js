/**
 * Настройки: провайдеры, модели и агенты.
 */
import SettingsPage from "./SettingsPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

const EMPTY_PROVIDER = {
    id: null,
    name: "OpenRouter",
    url: "https://openrouter.ai/api/v1",
    api_key: "",
    only: "",
    is_default: false,
};

const EMPTY_MODEL = {
    id: null,
    provider_id: null,
    name: "",
    temperature: 0.7,
    max_tokens: null,
};

const EMPTY_AGENT = {
    id: null,
    name: "",
    system_prompt: "",
    model_id: null,
};

export class SettingsPageModel extends BasePageModel
{
    state = {
        params: {},
        tab: "providers", // 'providers' | 'models' | 'agents'
        providers: [],
        models: [],
        agents: [],
        loading: false,
        error: "",
        notice: "",

        providerForm: { ...EMPTY_PROVIDER },
        modelForm: { ...EMPTY_MODEL },
        agentForm: { ...EMPTY_AGENT },
    };

    getComponent()
    {
        return SettingsPage;
    }

    getTitle()
    {
        return "Настройки";
    }

    async init()
    {
        await this.loadAll();
    }

    /**
     * Загрузить провайдеров, модели и агентов.
     */
    async loadAll()
    {
        this.state.loading = true;
        this.state.error = "";

        try {
            const [providers, models, agents] = await Promise.all([
                api.get("/api/providers"),
                api.get("/api/models"),
                api.get("/api/agents"),
            ]);

            this.state.providers = Array.isArray(providers) ? providers : [];
            this.state.models = Array.isArray(models) ? models : [];
            this.state.agents = Array.isArray(agents) ? agents : [];

            if (this.state.modelForm.provider_id === null && this.state.providers.length) {
                this.state.modelForm.provider_id = this.state.providers[0].id;
            }
        } catch (error) {
            this.state.error = error.message || "Не удалось загрузить настройки";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Переключение вкладки.
     */
    setTab(tab)
    {
        this.state.tab = tab;
    }

    // ------------------------------------------------------------------
    // Провайдеры
    // ------------------------------------------------------------------
    /**
     * Заполнить форму редактирования провайдера.
     */
    editProvider(provider)
    {
        this.state.providerForm = {
            id: provider.id,
            name: provider.name,
            url: provider.url,
            api_key: "",
            only: (provider.only || []).join(", "),
            is_default: Boolean(provider.is_default),
        };
    }

    /**
     * Сбросить форму провайдера.
     */
    resetProviderForm()
    {
        this.state.providerForm = { ...EMPTY_PROVIDER };
    }

    /**
     * Сохранить провайдера.
     */
    async saveProvider()
    {
        this.state.error = "";
        this.state.notice = "";

        // Список upstream-провайдеров вводится через запятую.
        const only = String(this.state.providerForm.only || "")
            .split(",")
            .map(item => item.trim())
            .filter(Boolean);

        const payload = {
            name: this.state.providerForm.name.trim(),
            url: this.state.providerForm.url.trim(),
            api_key: this.state.providerForm.api_key.trim(),
            only,
            is_default: Boolean(this.state.providerForm.is_default),
        };

        try {
            if (this.state.providerForm.id) {
                await api.put(`/api/providers/${this.state.providerForm.id}`, payload);
            } else {
                await api.post("/api/providers", payload);
            }

            this.resetProviderForm();
            await this.loadAll();
            this.state.notice = "Провайдер сохранён";
        } catch (error) {
            this.state.error = error.message || "Не удалось сохранить провайдера";
        }
    }

    /**
     * Удалить провайдера.
     */
    async removeProvider(provider)
    {
        if (!window.confirm(`Удалить провайдера «${provider.name}»?`)) {
            return;
        }

        try {
            await api.delete(`/api/providers/${provider.id}`);
            await this.loadAll();
        } catch (error) {
            this.state.error = error.message || "Не удалось удалить провайдера";
        }
    }

    // ------------------------------------------------------------------
    // Модели
    // ------------------------------------------------------------------
    /**
     * Заполнить форму редактирования модели.
     */
    editModel(model)
    {
        this.state.modelForm = {
            id: model.id,
            provider_id: model.provider_id,
            name: model.name,
            temperature: model.temperature ?? 0.7,
            max_tokens: model.max_tokens ?? null,
        };
    }

    /**
     * Сбросить форму модели.
     */
    resetModelForm()
    {
        this.state.modelForm = {
            ...EMPTY_MODEL,
            provider_id: this.state.providers.length ? this.state.providers[0].id : null,
        };
    }

    /**
     * Сохранить модель.
     */
    async saveModel()
    {
        this.state.error = "";
        this.state.notice = "";

        const payload = {
            provider_id: Number(this.state.modelForm.provider_id),
            name: this.state.modelForm.name.trim(),
            temperature: Number(this.state.modelForm.temperature),
            max_tokens: this.state.modelForm.max_tokens ? Number(this.state.modelForm.max_tokens) : null,
        };

        try {
            if (this.state.modelForm.id) {
                await api.put(`/api/models/${this.state.modelForm.id}`, payload);
            } else {
                await api.post("/api/models", payload);
            }

            this.resetModelForm();
            await this.loadAll();
            this.state.notice = "Модель сохранена";
        } catch (error) {
            this.state.error = error.message || "Не удалось сохранить модель";
        }
    }

    /**
     * Удалить модель.
     */
    async removeModel(model)
    {
        if (!window.confirm(`Удалить модель «${model.name}»?`)) {
            return;
        }

        try {
            await api.delete(`/api/models/${model.id}`);
            await this.loadAll();
        } catch (error) {
            this.state.error = error.message || "Не удалось удалить модель";
        }
    }

    // ------------------------------------------------------------------
    // Агенты
    // ------------------------------------------------------------------
    /**
     * Заполнить форму редактирования агента.
     */
    editAgent(agent)
    {
        this.state.agentForm = {
            id: agent.id,
            name: agent.name,
            system_prompt: agent.system_prompt || "",
            model_id: agent.model_id ?? null,
        };
    }

    /**
     * Сбросить форму агента.
     */
    resetAgentForm()
    {
        this.state.agentForm = { ...EMPTY_AGENT };
    }

    /**
     * Сохранить агента.
     */
    async saveAgent()
    {
        this.state.error = "";
        this.state.notice = "";

        const payload = {
            name: this.state.agentForm.name.trim(),
            system_prompt: this.state.agentForm.system_prompt || "",
            model_id: this.state.agentForm.model_id ? Number(this.state.agentForm.model_id) : null,
        };

        try {
            if (this.state.agentForm.id) {
                await api.put(`/api/agents/${this.state.agentForm.id}`, payload);
            } else {
                await api.post("/api/agents", payload);
            }

            this.resetAgentForm();
            await this.loadAll();
            this.state.notice = "Агент сохранён";
        } catch (error) {
            this.state.error = error.message || "Не удалось сохранить агента";
        }
    }

    /**
     * Удалить агента.
     */
    async removeAgent(agent)
    {
        if (!window.confirm(`Удалить агента «${agent.name}»?`)) {
            return;
        }

        try {
            await api.delete(`/api/agents/${agent.id}`);
            await this.loadAll();
        } catch (error) {
            this.state.error = error.message || "Не удалось удалить агента";
        }
    }

    /**
     * Название провайдера по id.
     */
    providerName(providerId)
    {
        const provider = this.state.providers.find(item => item.id === providerId);
        return provider ? provider.name : "—";
    }
}
