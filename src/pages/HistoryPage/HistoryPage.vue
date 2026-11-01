<style scoped>
.history__header
{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
}

.history__title
{
    margin: 0;
    font-size: 22px;
}

.history__subtitle
{
    margin: 4px 0 0;
    color: var(--text-muted);
    font-size: 13px;
}

.history__actions
{
    display: flex;
    gap: 10px;
}

.history__select
{
    max-width: 190px;
}

.history__filters
{
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
}

.history__search
{
    flex: 1;
}

.history__error
{
    color: #fca5a5;
    font-size: 13px;
    margin-bottom: 12px;
}

.history__empty
{
    color: var(--text-muted);
    padding: 40px 0;
    text-align: center;
}

.chat-list
{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.chat-list__item
{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    cursor: pointer;
    transition: border-color 0.15s ease, transform 0.15s ease;
}

.chat-list__item:hover
{
    border-color: var(--accent);
    transform: translateY(-1px);
}

.chat-list__main
{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.chat-list__title
{
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.chat-list__meta
{
    display: flex;
    gap: 12px;
    color: var(--text-muted);
    font-size: 12px;
}

.chat-list__delete
{
    margin-left: auto;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    border-radius: 8px;
    width: 30px;
    height: 30px;
    cursor: pointer;
}

.chat-list__delete:hover
{
    color: #fca5a5;
    border-color: rgba(248, 113, 113, 0.5);
}

@media (max-width: 720px)
{
    .history__header,
    .history__filters
    {
        flex-direction: column;
        align-items: stretch;
    }

    .history__select
    {
        max-width: none;
    }
}
</style>

<template>
    <div class="history">
        <header class="history__header">
            <div>
                <h1 class="history__title">История чатов</h1>
                <p class="history__subtitle">Показано {{ model.state.chats.length }} из {{ model.state.total }}</p>
            </div>

            <div class="history__actions">
                <select class="field__input history__select" v-model="model.state.selectedAgent">
                    <option :value="null">Без агента</option>
                    <option v-for="agent in model.state.agents" :key="agent.id" :value="agent.id">
                        {{ agent.name }}
                    </option>
                </select>
                <button class="btn btn--primary" @click="model.createChat()">＋ Новый чат</button>
            </div>
        </header>

        <div class="history__filters">
            <input
                class="field__input history__search"
                v-model="model.state.query"
                placeholder="Поиск по названию чата…"
                @input="model.debouncedLoad()"
            />

            <select class="field__input history__select" v-model="model.state.filter" @change="model.load()">
                <option value="all">Все</option>
                <option value="today">Сегодня</option>
                <option value="week">Неделя</option>
                <option value="month">Месяц</option>
            </select>

            <button class="btn btn--ghost" @click="model.resetFilter()">Сбросить</button>
        </div>

        <p class="history__error" v-if="model.state.error">{{ model.state.error }}</p>

        <p class="history__empty" v-if="!model.state.loading && !model.state.chats.length">
            Пока нет ни одного чата. Создайте первый — и он появится здесь.
        </p>

        <ul class="chat-list">
            <li
                v-for="chat in model.state.chats"
                :key="chat.id"
                class="chat-list__item"
                @click="model.openChat(chat)"
            >
                <div class="chat-list__main">
                    <span class="chat-list__title">{{ chat.title }}</span>
                    <span class="chat-list__meta">
                        <span v-if="chat.agent_name">{{ chat.agent_name }}</span>
                        <span>{{ chat.message_count || 0 }} сообщ.</span>
                        <span>{{ model.formatDate(chat.updated_at) }}</span>
                    </span>
                </div>

                <button class="chat-list__delete" title="Удалить" @click.stop="model.removeChat(chat)">✕</button>
            </li>
        </ul>
    </div>
</template>

<script>
export default {
    name: "HistoryPage",

    computed: {
        model()
        {
            return this.$layout.getPage("HistoryPageModel");
        },
    },
}
</script>
