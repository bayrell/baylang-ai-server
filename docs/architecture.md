Backend: FastApi Docker + Cloudflare
Frontend: VueJS + Model

Требуется создать Container DI в python. Функции для работы с контейнером:
- register(name, f)
- singleton(name, f)
- get(name) - Получить класс по названию (создать его если не существует). также возвращает singleton

Для FastApi рекомендуется использовать Depends и container.

Примеры:
```
database = container.get("database")
app = container.get("app")
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
container.singleton("app", lambda: App())
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
        WorkerEntrypoint.__init__(self, args, kwargs)
        self.app = create_cloudflare_app(self.env)
        
    async def fetch(self, request):
        import asgi
        return await asgi.fetch(app, request.js_object, self.env)
```
