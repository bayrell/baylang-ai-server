<style scoped>
.index
{
    text-align: center;
    padding: 80px 0;
    color: var(--text-muted);
}
</style>

<template>
    <div class="index">
        <h1>BayLang AI</h1>
        <p>Перенаправляем…</p>
    </div>
</template>

<script>
export default {
    name: "IndexPage",

    computed: {
        model()
        {
            return this.$layout.getPage("IndexPageModel");
        },
    },
}
</script>
