Backend: FastApi Docker + Cloudflare
Frontend: VueJS + Model

Структура проекта:
- src/assets - Assets
- src/dist - Сборка Vuejs
- src/main.js - Точка входя для vuejs
- src/main.py - Точка входа для Cloudflare
- src/app.py - Точка входа для Docker
- src/core - Ядро Python
- src/plugins - Плагины
- src/pages - папка со страницами
- src/pages/IndexPage - папка со страницей. Находятся файлы IndexPage.vue и IndexPageModel.js

Требуется создать Container DI в python. Функции для работы с контейнером:
- register(name, f)
- singleton(name, f)
- get(name) - Получить класс по названию (создать его если не существует). Также возвращает singleton и кэширует его, если нужно.

Примеры:
```
database = container.get("database")
app = container.get("app")
```

Правила:
- Использовать Depends и container.
- Для работы с базой данных использовать паттерн Record репозитории, в котором находятся методы для работы с БД и sql запросы.

Пример:
```
def get_user_repository():
    return container.get("user_repository")

@app.get("/items"):
async def items(user_repo = Depends(get_user_repository)):
    return []
```

Регистрация репозиториев:
```
def register_repositories():
    container.singleton("user_repository", lambda container: UserRepository(container.get("database")))
```

Регистрация для Cloudflare:
```
container.singleton("database", lambda container: D1(container.get("env")))
```

Регистрация для Sqlite
```
container.singleton("database", lambda container: SqliteDatabase())
```

Регистрация App:
```
container.singleton("app", lambda: FastApi())
```

app.py
```
def register_routes():
    """
    Register fastapi routes
    """

def create_app():
    container.singleton("database", lambda container: SqliteDatabase())
    register_routes()
    register_static()
    return container.get("app")

def create_cloudflare_app(env):
    container.singleton("env", lambda: Env(env))
    container.singleton("database", lambda container: D1(container.get("env")))
    register_routes()
    return container.get("app")
```

main.py
```
class Default(WorkerEntrypoint):
    def __init__(self, *args, **kwargs):
        WorkerEntrypoint.__init__(self, *args, **kwargs)
        self.app = create_cloudflare_app(self.env)
        
    async def fetch(self, request):
        import asgi
        return await asgi.fetch(self.app, request.js_object, self.env)
```

Frontend:

В одной папке должен быть компонент + модель страницы. Компонент - рендер страницы и обработка event. Модель хранит state, данные и бизнес логику.

Структура шаблона:
```
<style scoped>
</style>

<template>
</template>

<script>
export default {
    name: "IndexPage",
    computed: {
        model()
        {
            return this.$layout.getPage("IndexPageModel");
        }
    }
}
</script>
```

Пример IndexPageModel:
```
import IndexPage from "./IndexPage.vue";
import BasePageModel from "@/pages/BasePageModel";

export class IndexPageModel extends BasePageModel
{
    getComponent()
    {
        return IndexPage;
    }
    
    getTitle()
    {
        return "Index page";
    }
    
    async init()
    {
    }
}
```

AppLayoutModel - это глобальная модель, которая хранит модели всех страниц проекта. Она создается в main.js и устанавливается в globalProperties vue.

Пример:
```
/* Create layout */
const layout = reactive(new AppLayoutModel());
layout.init();

/* Create app */
const app = createApp(App);
app.config.globalProperties.$layout = layout;

/* Mount app */
app.mount(".root_container");
```

AppLayoutModel:
- register_routes() - Регистрирует роуты
- async init() - Инициализирует проект, текущую страницу
- getPage(name) - получает модель страницы

Требуется создать простой роутер для проекта, который будет регистрировать url, name, а также history push state. Методы:
- add(name, url, model) - Регистрирует новый route и модель страницы
- url(name, params) - Возвращает url
- find(url) - Вовзращает route имя и url params
- open(name, params) - Открывает страницу
- openUrl(url) - Открывает страницу по url
- async init() - инициализирует текущую страницу
- getCurrentPage() - возвращает название текущей страницы
- getPage(name) - получает модель по названию страницы
