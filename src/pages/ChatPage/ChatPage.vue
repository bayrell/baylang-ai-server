<style scoped>
.chat
{
    display: flex;
    flex-direction: column;
    height: calc(100vh - 140px);
    min-height: 480px;
}

.chat__header
{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}

.chat__title
{
    margin: 0;
    font-size: 19px;
}

.chat__agent
{
    color: var(--text-muted);
    font-size: 12px;
}

.chat__error
{
    margin: 12px 0 0;
    color: #fca5a5;
    font-size: 13px;
}

.chat__messages
{
    flex: 1;
    overflow-y: auto;
    padding: 18px 4px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.chat__empty
{
    color: var(--text-muted);
    text-align: center;
    padding: 40px 0;
}

.message
{
    max-width: 78%;
    padding: 12px 16px;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: var(--surface);
}

.message--user
{
    align-self: flex-end;
    background: rgba(52, 211, 153, 0.12);
    border-color: rgba(52, 211, 153, 0.3);
}

.message--assistant
{
    align-self: flex-start;
}

.message__role
{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 6px;
}

.message__content
{
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 14px;
    line-height: 1.55;
}

.message__content--typing
{
    color: var(--text-muted);
    font-style: italic;
}

.chat__composer
{
    display: flex;
    gap: 12px;
    align-items: flex-end;
    padding-top: 14px;
    border-top: 1px solid var(--border);
}

.chat__input
{
    flex: 1;
    resize: vertical;
    min-height: 74px;
    font-family: inherit;
}
</style>

<template>
    <div class="chat">
        <header class="chat__header">
            <div class="chat__info">
                <h1 class="chat__title">{{ model.state.title || "Чат" }}</h1>
                <span class="chat__agent" v-if="model.state.agentName">Агент: {{ model.state.agentName }}</span>
            </div>
            <button class="btn btn--ghost" @click="model.newChat()">＋ Новый чат</button>
        </header>

        <p class="chat__error" v-if="model.state.error">{{ model.state.error }}</p>

        <div class="chat__messages" ref="messages">
            <p class="chat__empty" v-if="!model.state.loading && !model.state.messages.length">
                Напишите первое сообщение — агент ответит в реальном времени.
            </p>

            <div
                v-for="(message, index) in model.state.messages"
                :key="index"
                class="message"
                :class="message.role === 'user' ? 'message--user' : 'message--assistant'"
            >
                <div class="message__role">
                    {{ message.role === "user" ? "Вы" : "Агент" }}
                </div>
                <div class="message__content">{{ message.content }}</div>
            </div>

            <div class="message message--assistant" v-if="model.state.typing && !model.state.streaming">
                <div class="message__role">Агент</div>
                <div class="message__content message__content--typing">печатает…</div>
            </div>
        </div>

        <form class="chat__composer" @submit.prevent="model.send()">
            <textarea
                class="field__input chat__input"
                v-model="model.state.input"
                rows="3"
                placeholder="Напишите сообщение… (Enter — отправить, Shift+Enter — перенос строки)"
                @keydown="model.onKeydown($event)"
            ></textarea>

            <button class="btn btn--primary" type="submit" :disabled="model.state.typing">
                {{ model.state.typing ? "Отправка…" : "Отправить" }}
            </button>
        </form>
    </div>
</template>

<script>
export default {
    name: "ChatPage",

    computed: {
        model()
        {
            return this.$layout.getPage("ChatPageModel");
        },
    },

    watch: {
        "model.state.messages": {
            deep: true,
            handler()
            {
                this.$nextTick(() => {
                    const box = this.$refs.messages;
                    if (box) {
                        box.scrollTop = box.scrollHeight;
                    }
                });
            },
        },
    },
}
</script>
