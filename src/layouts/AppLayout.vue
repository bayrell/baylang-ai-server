<template>
    <div class="layout">
        <header class="layout__header">
            <div class="layout__brand" @click="openHome">
                <span class="layout__logo">BL</span>
                <span class="layout__title">BayLang AI</span>
            </div>

            <nav class="layout__nav" v-if="isAuthenticated">
                <a href="#" :class="{ active: current === 'chats' }" @click.prevent="open('chats')">Чаты</a>
                <a href="#" :class="{ active: current === 'settings' }" @click.prevent="open('settings')">Настройки</a>
            </nav>

            <div class="layout__user" v-if="isAuthenticated">
                <span class="layout__email">{{ user ? user.email : "" }}</span>
                <button class="btn btn--ghost" @click="logout">Выйти</button>
            </div>

            <div class="layout__user" v-else>
                <button class="btn btn--ghost" @click="open('login')">Вход</button>
                <button class="btn btn--primary" @click="open('register')">Регистрация</button>
            </div>
        </header>

        <main class="layout__content">
            <component :is="component" v-if="component" />
            <div class="layout__loader" v-else>Загрузка…</div>
        </main>
    </div>
</template>

<script>
export default {
    name: "AppLayout",

    computed: {
        current()
        {
            return this.$layout.getRouter().getCurrentPage();
        },

        component()
        {
            const page = this.$layout.getRouter().getCurrentPage();
            const model = page ? this.$layout.getPage(page) : null;
            return model ? model.getComponent() : null;
        },

        isAuthenticated()
        {
            return Boolean(localStorage.getItem("access_token"));
        },

        user()
        {
            return this.$layout.getUser();
        },
    },

    methods: {
        open(name, params = {})
        {
            this.$layout.getRouter().open(name, params);
        },

        openHome()
        {
            this.open("index");
        },

        async logout()
        {
            await this.$layout.logout();
        },
    },
}
</script>

<style scoped>
.layout
{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.layout__header
{
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 14px 24px;
    background: rgba(16, 19, 26, 0.92);
    border-bottom: 1px solid rgba(120, 220, 190, 0.12);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 10;
}

.layout__brand
{
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    user-select: none;
}

.layout__logo
{
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, #34d399, #22d3ee);
    color: #06231c;
    font-weight: 700;
    font-size: 13px;
}

.layout__title
{
    font-weight: 600;
    letter-spacing: 0.02em;
}

.layout__nav
{
    display: flex;
    gap: 18px;
    margin-left: 12px;
}

.layout__nav a
{
    color: var(--text-muted);
    text-decoration: none;
    font-size: 14px;
    padding: 6px 2px;
    border-bottom: 1px solid transparent;
    transition: color 0.15s ease, border-color 0.15s ease;
}

.layout__nav a:hover,
.layout__nav a.active
{
    color: var(--accent);
    border-bottom-color: var(--accent);
}

.layout__user
{
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 12px;
}

.layout__email
{
    color: var(--text-muted);
    font-size: 13px;
}

.layout__content
{
    flex: 1;
    width: 100%;
    max-width: 1180px;
    margin: 0 auto;
    padding: 24px;
}

.layout__loader
{
    color: var(--text-muted);
    text-align: center;
    padding: 60px 0;
}

@media (max-width: 720px)
{
    .layout__header
    {
        flex-wrap: wrap;
        gap: 12px;
    }

    .layout__email
    {
        display: none;
    }
}
</style>
