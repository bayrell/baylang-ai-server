<template>
    <div class="auth">
        <form class="auth__card" @submit.prevent="model.submit()">
            <h1 class="auth__title">Вход</h1>
            <p class="auth__subtitle">Войдите, чтобы открыть свои чаты и настройки.</p>

            <label class="field">
                <span class="field__label">Email</span>
                <input
                    v-model="model.state.email"
                    class="field__input"
                    type="email"
                    autocomplete="email"
                    placeholder="user@example.com"
                />
            </label>

            <label class="field">
                <span class="field__label">Пароль</span>
                <input
                    v-model="model.state.password"
                    class="field__input"
                    type="password"
                    autocomplete="current-password"
                    placeholder="••••••••"
                />
            </label>

            <p class="auth__error" v-if="model.state.error">{{ model.state.error }}</p>

            <button class="btn btn--primary btn--block" type="submit" :disabled="model.state.loading">
                {{ model.state.loading ? "Входим…" : "Войти" }}
            </button>

            <p class="auth__footer">
                Нет аккаунта?
                <a href="#" @click.prevent="model.goRegister()">Зарегистрироваться</a>
            </p>
        </form>
    </div>
</template>

<script>
export default {
    name: "LoginPage",

    computed: {
        model()
        {
            return this.$layout.getPage("LoginPageModel");
        },
    },
}
</script>

<style scoped>
.auth
{
    display: grid;
    place-items: center;
    min-height: 70vh;
}

.auth__card
{
    width: 100%;
    max-width: 400px;
    padding: 32px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.auth__title
{
    margin: 0 0 6px;
    font-size: 24px;
}

.auth__subtitle
{
    margin: 0 0 24px;
    color: var(--text-muted);
    font-size: 14px;
}

.auth__error
{
    margin: 0 0 14px;
    padding: 10px 12px;
    border-radius: 10px;
    background: rgba(248, 113, 113, 0.12);
    border: 1px solid rgba(248, 113, 113, 0.35);
    color: #fca5a5;
    font-size: 13px;
}

.auth__footer
{
    margin: 18px 0 0;
    font-size: 13px;
    color: var(--text-muted);
    text-align: center;
}

.auth__footer a
{
    color: var(--accent);
}
</style>
