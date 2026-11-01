<style scoped>
.settings__tabs
{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
}

.settings__tab
{
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-muted);
    padding: 8px 14px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 14px;
}

.settings__tab.active
{
    color: var(--accent);
    border-color: rgba(52, 211, 153, 0.4);
    background: rgba(52, 211, 153, 0.08);
}

.settings__panel
{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px;
}

.settings__heading
{
    margin: 0 0 16px;
    font-size: 17px;
}

.settings__form
{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 10px;
    margin-bottom: 22px;
}

.settings__wide
{
    grid-column: 1 / -1;
}

.settings__checkbox
{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-muted);
    font-size: 13px;
}

.settings__form-actions
{
    grid-column: 1 / -1;
    display: flex;
    gap: 10px;
}

.settings__list
{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.settings__item
{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 16px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
}

.settings__item-main
{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.settings__item-sub
{
    color: var(--text-muted);
    font-size: 12px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 620px;
}

.settings__badge
{
    align-self: flex-start;
    margin-top: 4px;
    padding: 2px 8px;
    font-size: 11px;
    border-radius: 999px;
    color: var(--accent);
    background: rgba(52, 211, 153, 0.12);
}

.settings__item-actions
{
    display: flex;
    gap: 8px;
    flex-shrink: 0;
}

.settings__error
{
    color: #fca5a5;
    font-size: 13px;
    margin-bottom: 10px;
}

.settings__notice
{
    color: var(--accent);
    font-size: 13px;
    margin-bottom: 10px;
}

@media (max-width: 720px)
{
    .settings__item
    {
        flex-direction: column;
        align-items: stretch;
    }
}
</style>

<template>
    <div class="settings">
        <nav class="settings__tabs">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                class="settings__tab"
                :class="{ active: model.state.tab === tab.id }"
                @click="model.setTab(tab.id)"
            >
                {{ tab.title }}
            </button>
        </nav>

        <p class="settings__error" v-if="model.state.error">{{ model.state.error }}</p>
        <p class="settings__notice" v-if="model.state.notice">{{ model.state.notice }}</p>

        <!-- Провайдеры -->
        <section v-if="model.state.tab === 'providers'" class="settings__panel">
            <h2 class="settings__heading">Провайдеры</h2>

            <form class="settings__form" @submit.prevent="model.saveProvider()">
                <input class="field__input" v-model="model.state.providerForm.name" placeholder="Название" />
                <input class="field__input" v-model="model.state.providerForm.url" placeholder="URL" />
                <input
                    class="field__input"
                    v-model="model.state.providerForm.api_key"
                    type="password"
                    placeholder="API Key"
                />
                <input
                    class="field__input settings__wide"
                    v-model="model.state.providerForm.only"
                    placeholder="Провайдеры через запятую (например: anthropic, openai)"
                />
                <label class="settings__checkbox">
                    <input type="checkbox" v-model="model.state.providerForm.is_default" />
                    По умолчанию
                </label>

                <div class="settings__form-actions">
                    <button class="btn btn--primary" type="submit">
                        {{ model.state.providerForm.id ? "Обновить" : "Сохранить" }}
                    </button>
                    <button class="btn btn--ghost" type="button" @click="model.resetProviderForm()">Очистить</button>
                </div>
            </form>

            <ul class="settings__list">
                <li v-for="provider in model.state.providers" :key="provider.id" class="settings__item">
                    <div class="settings__item-main">
                        <strong>{{ provider.name }}</strong>
                        <span class="settings__item-sub">{{ provider.url }}</span>
                        <span class="settings__item-sub" v-if="provider.only.length">
                            Only: {{ provider.only.join(", ") }}
                        </span>
                        <span class="settings__badge" v-if="provider.is_default">по умолчанию</span>
                    </div>
                    <div class="settings__item-actions">
                        <button class="btn btn--ghost" @click="model.editProvider(provider)">Изменить</button>
                        <button class="btn btn--danger" @click="model.removeProvider(provider)">Удалить</button>
                    </div>
                </li>
            </ul>
        </section>

        <!-- Модели -->
        <section v-if="model.state.tab === 'models'" class="settings__panel">
            <h2 class="settings__heading">Модели</h2>

            <form class="settings__form" @submit.prevent="model.saveModel()">
                <select class="field__input" v-model="model.state.modelForm.provider_id">
                    <option :value="null" disabled>Выберите провайдера</option>
                    <option v-for="provider in model.state.providers" :key="provider.id" :value="provider.id">
                        {{ provider.name }}
                    </option>
                </select>
                <input
                    class="field__input"
                    v-model="model.state.modelForm.name"
                    placeholder="anthropic/claude-3.5-sonnet"
                />
                <input
                    class="field__input"
                    v-model.number="model.state.modelForm.temperature"
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    placeholder="Температура"
                />
                <input
                    class="field__input"
                    v-model.number="model.state.modelForm.max_tokens"
                    type="number"
                    min="1"
                    placeholder="max_tokens"
                />

                <div class="settings__form-actions">
                    <button class="btn btn--primary" type="submit">
                        {{ model.state.modelForm.id ? "Обновить" : "Сохранить" }}
                    </button>
                    <button class="btn btn--ghost" type="button" @click="model.resetModelForm()">Очистить</button>
                </div>
            </form>

            <ul class="settings__list">
                <li v-for="item in model.state.models" :key="item.id" class="settings__item">
                    <div class="settings__item-main">
                        <strong>{{ item.name }}</strong>
                        <span class="settings__item-sub">
                            {{ item.provider_name || model.providerName(item.provider_id) }} ·
                            t={{ item.temperature }} · max_tokens={{ item.max_tokens || "—" }}
                        </span>
                    </div>
                    <div class="settings__item-actions">
                        <button class="btn btn--ghost" @click="model.editModel(item)">Изменить</button>
                        <button class="btn btn--danger" @click="model.removeModel(item)">Удалить</button>
                    </div>
                </li>
            </ul>
        </section>

        <!-- Агенты -->
        <section v-if="model.state.tab === 'agents'" class="settings__panel">
            <h2 class="settings__heading">Агенты</h2>

            <form class="settings__form" @submit.prevent="model.saveAgent()">
                <input class="field__input" v-model="model.state.agentForm.name" placeholder="Имя агента" />
                <select class="field__input" v-model="model.state.agentForm.model_id">
                    <option :value="null">Без модели</option>
                    <option v-for="item in model.state.models" :key="item.id" :value="item.id">
                        {{ item.name }}
                    </option>
                </select>
                <textarea
                    class="field__input settings__wide"
                    rows="4"
                    v-model="model.state.agentForm.system_prompt"
                    placeholder="Системный промпт..."
                ></textarea>

                <div class="settings__form-actions">
                    <button class="btn btn--primary" type="submit">
                        {{ model.state.agentForm.id ? "Обновить" : "Сохранить" }}
                    </button>
                    <button class="btn btn--ghost" type="button" @click="model.resetAgentForm()">Очистить</button>
                </div>
            </form>

            <ul class="settings__list">
                <li v-for="agent in model.state.agents" :key="agent.id" class="settings__item">
                    <div class="settings__item-main">
                        <strong>{{ agent.name }}</strong>
                        <span class="settings__item-sub">{{ agent.model_name || "Модель не выбрана" }}</span>
                        <span class="settings__item-sub" v-if="agent.system_prompt">{{ agent.system_prompt }}</span>
                    </div>
                    <div class="settings__item-actions">
                        <button class="btn btn--ghost" @click="model.editAgent(agent)">Изменить</button>
                        <button class="btn btn--danger" @click="model.removeAgent(agent)">Удалить</button>
                    </div>
                </li>
            </ul>
        </section>
    </div>
</template>

<script>
export default {
    name: "SettingsPage",

    data()
    {
        return {
            tabs: [
                { id: "providers", title: "Провайдеры" },
                { id: "models", title: "Модели" },
                { id: "agents", title: "Агенты" },
            ],
        };
    },

    computed: {
        model()
        {
            return this.$layout.getPage("SettingsPageModel");
        },
    },
}
</script>
