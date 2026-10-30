Функционал:
- Авторизация
- Чат с пользователем
- История чатов, возможность создать новый чат
- Выбор списка чатов Select list, показывать последние 50 чатов
- Интерфейс истории чатом с фильтром и поиском
- Настройка агентов (системный промтп, модель)
- Настройка моделей (название модели, провайдер, температура и т.п.)
- Настройка провайдеров (название, url, api key). По умолчанию openrouter. У openrouter есть возможность добавить список провайдеров через запятую.

Можно использовать pydantic AI.

Добавить
```
os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
```

Пример:
```
from pydantic_ai import (
    Agent,
    RunContext,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart
)
from pydantic_ai.models.openrouter import (
    OpenRouterModel,
    OpenRouterModelSettings,
    OpenRouterProviderConfig,
)
from pydantic_ai.providers.openrouter import OpenRouterProvider

APP_URL = "https://baylang.com/"
APP_TITLE = "BayLang AI"

def build_agent(capabilities=None):
    if capabilities is None:
        capabilities = []

    config = OpenRouterProviderConfig()
    
    if openrouter_providers:
        items = openrouter_providers.split(",")
        config["only"] = list(map(lambda s: s.strip(), items))
    
    model = OpenRouterModel(
        model_name,
        provider=OpenRouterProvider(
            api_key=api_key,
            app_url=APP_URL,
            app_title=APP_TITLE,
        ),
        settings=OpenRouterModelSettings(
            openrouter_cache_instructions=True,
            openrouter_cache_messages=True,
            openrouter_cache_tool_definitions=True,
            openrouter_provider=config,
        ),
    )

    capabilities.append(hooks)

    agent = Agent(
        model,
        retries=10,
        capabilities=capabilities,
    )

    return agent
```

Отправка сообщения:
```
async def send(self, user_message: str) -> str:
    """Один шаг agent loop: user -> agent -> assistant."""
    self.history.append(
        ModelRequest(parts=[UserPromptPart(content=user_message)])
    )

    result = await self.agent.run(
        user_message,
        message_history=self.context,
        usage_limits=UsageLimits(request_limit=None),
    )

    self.history.append(
        ModelResponse(parts=[TextPart(content=result.output)])
    )
    # полная переписка (с ответами инструментов) уходит в контекст
    self.context = list(result.all_messages())
    return result.output
```

Конвертация в контекста в json:
```
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python

""" Convert to json """"
object = to_jsonable_python(self.context)

""" Restore """
context = ModelMessagesTypeAdapter.validate_python(object)
```
