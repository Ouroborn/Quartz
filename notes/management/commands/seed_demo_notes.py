"""
Наполняет базу демонстрационными заметками для трёх сценариев из README/презентации:
1. Учебный процесс (изучение Django)
2. Управление проектом (проектирование API)
3. Личные исследования (изучение FastAPI)

Использование:
    python manage.py seed_demo_notes
    python manage.py seed_demo_notes --username=demo --password=demo12345
    python manage.py seed_demo_notes --clear   # снести старые демо-заметки этого пользователя перед созданием

Теги проставляются вручную (без реального обращения к ИИ — демо должно
работать даже без настроенного провайдера), а связи между заметками строятся
той же функцией _update_relations, что использует боевой ai_services.py —
так граф выглядит ровно так же, как после настоящего ИИ-анализа.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from notes.models import Note, Tag
from notes.ai_services import _update_relations


# ---------------------------------------------------------------------------
# Сценарий 1: Учебный процесс — изучение Django
# ---------------------------------------------------------------------------
LEARNING_NOTES = [
    {
        "title": "Основы Django моделей",
        "tags": ["django", "models", "backend"],
        "content": (
            "# Основы Django моделей\n\n"
            "Модель в Django — это класс, наследующийся от `models.Model`, который описывает "
            "структуру таблицы в базе данных. Каждый атрибут класса соответствует полю таблицы.\n\n"
            "```python\n"
            "class Article(models.Model):\n"
            "    title = models.CharField(max_length=200)\n"
            "    published_at = models.DateTimeField(auto_now_add=True)\n"
            "```\n\n"
            "Ключевые моменты:\n"
            "- Django сам генерирует SQL для создания таблицы через миграции.\n"
            "- `Meta`-класс задаёт метаданные: сортировку, verbose_name, индексы.\n"
            "- Методы модели (`__str__`, кастомные методы) — обычные методы Python, "
            "их удобно использовать для бизнес-логики, связанной с конкретной записью."
        ),
    },
    {
        "title": "ORM запросы",
        "tags": ["django", "orm", "models", "queries"],
        "content": (
            "# ORM-запросы в Django\n\n"
            "Django ORM переводит методы QuerySet в SQL. Базовые операции:\n\n"
            "```python\n"
            "Article.objects.filter(title__icontains='django')\n"
            "Article.objects.exclude(published_at__isnull=True)\n"
            "Article.objects.get(pk=1)\n"
            "```\n\n"
            "`filter()` и `exclude()` возвращают новый QuerySet, а не выполняют запрос сразу — "
            "это называется ленивыми вычислениями (см. отдельную заметку). Реальный SQL "
            "выполняется только при итерации, вызове `len()`, `list()` или `bool()`."
        ),
    },
    {
        "title": "Django ORM: агрегации и annotate",
        "tags": ["django", "orm", "queries"],
        "content": (
            "# Агрегации и annotate\n\n"
            "`aggregate()` считает одно значение по всему QuerySet:\n"
            "```python\n"
            "from django.db.models import Avg, Count\n"
            "Article.objects.aggregate(Avg('views'))\n"
            "```\n\n"
            "`annotate()` добавляет вычисляемое поле к каждому объекту в QuerySet — например, "
            "количество комментариев у каждой статьи:\n"
            "```python\n"
            "Article.objects.annotate(comments_count=Count('comments'))\n"
            "```\n\n"
            "Частая ошибка — комбинировать несколько `Count()` через `annotate()` на связанных "
            "таблицах без `distinct=True`, что приводит к завышенным цифрам из-за JOIN'ов."
        ),
    },
    {
        "title": "Django миграции",
        "tags": ["django", "models", "backend"],
        "content": (
            "# Миграции в Django\n\n"
            "Миграции — это способ версионировать изменения схемы БД вместе с кодом.\n\n"
            "```bash\n"
            "python manage.py makemigrations\n"
            "python manage.py migrate\n"
            "```\n\n"
            "`makemigrations` сравнивает текущие модели с последним состоянием миграций и "
            "генерирует Python-файл с операциями (`CreateModel`, `AddField`, `AlterField`...). "
            "`migrate` применяет эти операции к реальной базе. Для необратимых изменений "
            "(например, удаление поля с данными) стоит писать `RunPython`-миграции с "
            "функцией отката."
        ),
    },
    {
        "title": "QuerySet и ленивые вычисления",
        "tags": ["django", "orm", "queries", "python"],
        "content": (
            "# Ленивые вычисления QuerySet\n\n"
            "QuerySet не обращается к базе, пока это не станет необходимо. Это позволяет "
            "свободно комбинировать фильтры:\n\n"
            "```python\n"
            "qs = Article.objects.filter(is_published=True)\n"
            "qs = qs.filter(author=request.user)  # SQL всё ещё не выполнен\n"
            "list(qs)  # а вот теперь выполнен\n"
            "```\n\n"
            "Из-за ленивости легко случайно выполнить N+1 запросов в цикле шаблона — "
            "для этого есть `select_related()` (JOIN для ForeignKey/OneToOne) и "
            "`prefetch_related()` (отдельный запрос + склейка в Python для ManyToMany)."
        ),
    },
    {
        "title": "Django Admin: кастомизация",
        "tags": ["django", "backend"],
        "content": (
            "# Кастомизация Django Admin\n\n"
            "Стандартная админка регистрируется в пару строк:\n"
            "```python\n"
            "@admin.register(Article)\n"
            "class ArticleAdmin(admin.ModelAdmin):\n"
            "    list_display = ['title', 'published_at']\n"
            "    list_filter = ['is_published']\n"
            "    search_fields = ['title']\n"
            "```\n\n"
            "Полезные приёмы: `list_editable` для редактирования прямо в списке, "
            "`inlines` для редактирования связанных объектов на одной странице, "
            "`get_queryset()` override для ограничения видимых записей по правам пользователя."
        ),
    },
    {
        "title": "Связи между моделями: ForeignKey, ManyToMany",
        "tags": ["django", "models", "orm"],
        "content": (
            "# Связи между моделями\n\n"
            "- `ForeignKey` — связь \"многие к одному\" (у статьи один автор, у автора много статей).\n"
            "- `ManyToManyField` — связь \"многие ко многим\" (у статьи много тегов, у тега много статей).\n"
            "- `OneToOneField` — расширение модели один-к-одному (профиль пользователя).\n\n"
            "```python\n"
            "class Article(models.Model):\n"
            "    author = models.ForeignKey(User, on_delete=models.CASCADE)\n"
            "    tags = models.ManyToManyField(Tag)\n"
            "```\n\n"
            "`on_delete` обязателен для ForeignKey и определяет, что делать при удалении "
            "родительской записи: `CASCADE`, `SET_NULL`, `PROTECT` и другие варианты."
        ),
    },
    {
        "title": "Django Forms и валидация",
        "tags": ["django", "backend", "forms"],
        "content": (
            "# Django Forms и валидация\n\n"
            "`forms.Form` — для произвольных форм, `forms.ModelForm` — форма, привязанная "
            "к модели, с автоматической генерацией полей и валидацией на основе ограничений модели.\n\n"
            "```python\n"
            "class ArticleForm(forms.ModelForm):\n"
            "    class Meta:\n"
            "        model = Article\n"
            "        fields = ['title', 'content']\n\n"
            "    def clean_title(self):\n"
            "        title = self.cleaned_data['title']\n"
            "        if len(title) < 5:\n"
            "            raise forms.ValidationError('Слишком короткий заголовок')\n"
            "        return title\n"
            "```\n\n"
            "Методы `clean_<field>()` валидируют отдельное поле, `clean()` — валидацию, "
            "зависящую от нескольких полей сразу."
        ),
    },
    {
        "title": "Django Views: Function-based vs Class-based",
        "tags": ["django", "backend", "views"],
        "content": (
            "# FBV vs CBV\n\n"
            "Function-based views (FBV) — обычные функции, принимающие `request` и "
            "возвращающие `HttpResponse`. Прозрачны и просты для несложной логики.\n\n"
            "Class-based views (CBV) удобны, когда есть повторяющиеся паттерны: "
            "`ListView`, `DetailView`, `CreateView`, `UpdateView` уже реализуют стандартный "
            "CRUD и переопределяются через атрибуты/методы вместо копирования кода.\n\n"
            "```python\n"
            "class ArticleListView(ListView):\n"
            "    model = Article\n"
            "    paginate_by = 20\n"
            "```\n\n"
            "Правило выбора: если view — это стандартный CRUD, берите CBV; если логика "
            "нестандартная и ветвистая — часто читаемее написать FBV."
        ),
    },
    {
        "title": "Django Signals",
        "tags": ["django", "backend", "models"],
        "content": (
            "# Django Signals\n\n"
            "Сигналы позволяют выполнять код в ответ на события — например, создание объекта:\n\n"
            "```python\n"
            "from django.db.models.signals import post_save\n"
            "from django.dispatch import receiver\n\n"
            "@receiver(post_save, sender=User)\n"
            "def create_profile(sender, instance, created, **kwargs):\n"
            "    if created:\n"
            "        Profile.objects.create(user=instance)\n"
            "```\n\n"
            "Сигналы удобны для декаплинга логики между приложениями, но злоупотребление ими "
            "делает поток выполнения неявным и трудным для отладки — для логики внутри "
            "одного приложения часто лучше явный вызов метода или override `save()`."
        ),
    },
]

# ---------------------------------------------------------------------------
# Сценарий 2: Управление проектом — проектирование API
# ---------------------------------------------------------------------------
PROJECT_NOTES = [
    {
        "title": "Требования к API",
        "tags": ["api", "requirements", "architecture"],
        "content": (
            "# Требования к API\n\n"
            "Черновой список функциональных требований для REST API проекта:\n\n"
            "- CRUD для основных сущностей (пользователи, заказы, товары).\n"
            "- Пагинация списков (courser-based, а не offset — для больших таблиц).\n"
            "- Единый формат ошибок для всех эндпоинтов.\n"
            "- Версионирование через префикс `/api/v1/`.\n"
            "- Ограничение по правам доступа (см. Authentication).\n\n"
            "Нефункциональные требования: p95 времени ответа < 300мс, доступность 99.9%, "
            "полное покрытие эндпоинтов интеграционными тестами до релиза."
        ),
    },
    {
        "title": "Authentication",
        "tags": ["api", "auth", "security"],
        "content": (
            "# Аутентификация API\n\n"
            "Выбор между несколькими схемами:\n\n"
            "- **Session-based** — просто, но плохо масштабируется на несколько серверов "
            "без общего хранилища сессий.\n"
            "- **Token-based (JWT)** — stateless, подходит для мобильных клиентов и SPA, "
            "но нужен механизм отзыва токенов (blacklist / короткий TTL + refresh).\n"
            "- **OAuth2** — если нужен вход через сторонние сервисы (Google, GitHub) "
            "или API используют внешние партнёры.\n\n"
            "Решение для проекта: JWT access-токен (15 минут) + refresh-токен (14 дней), "
            "хранение refresh в httpOnly cookie."
        ),
    },
    {
        "title": "Error Handling",
        "tags": ["api", "error-handling", "architecture"],
        "content": (
            "# Обработка ошибок API\n\n"
            "Единый формат ответа при ошибке облегчает жизнь фронтенду и внешним потребителям API:\n\n"
            "```json\n"
            "{\n"
            "  \"error\": {\n"
            "    \"code\": \"VALIDATION_ERROR\",\n"
            "    \"message\": \"Поле email обязательно\",\n"
            "    \"fields\": {\"email\": [\"Обязательное поле\"]}\n"
            "  }\n"
            "}\n"
            "```\n\n"
            "Договорённости по кодам: 400 — ошибка валидации входных данных, 401 — не "
            "аутентифицирован, 403 — аутентифицирован, но нет прав, 404 — ресурс не найден, "
            "409 — конфликт состояния (например, повторная попытка создать уникальную запись), "
            "429 — превышен лимит запросов, 5xx — ошибка сервера (логируется с полным traceback)."
        ),
    },
    {
        "title": "Rate Limiting и Throttling",
        "tags": ["api", "security", "architecture"],
        "content": (
            "# Rate Limiting\n\n"
            "Ограничение частоты запросов защищает API от перегрузки и злоупотреблений.\n\n"
            "Варианты алгоритмов:\n"
            "- **Fixed window** — просто считать запросы в окне (например, минута), но "
            "возможен всплеск на границе окон.\n"
            "- **Sliding window log** — точнее, но требует хранить временные метки запросов.\n"
            "- **Token bucket** — хорошо сглаживает всплески, распространён в проде.\n\n"
            "Лимиты стоит различать по типу клиента: для анонимных запросов — жёстче, "
            "для аутентифицированных пользователей — мягче, для внутренних сервисов — "
            "отдельный (более высокий) лимит по API-ключу."
        ),
    },
    {
        "title": "Версионирование API",
        "tags": ["api", "architecture"],
        "content": (
            "# Версионирование API\n\n"
            "Три распространённых подхода:\n\n"
            "1. **URL-путь**: `/api/v1/orders/` — самый явный и простой для дебага, "
            "но версия \"размазывается\" по всем эндпоинтам сразу.\n"
            "2. **Заголовок**: `Accept: application/vnd.myapp.v2+json` — чище URL, "
            "но менее очевидно при простом просмотре запроса в логах.\n"
            "3. **Query-параметр**: `?version=2` — просто, но легко забыть указать, "
            "и клиент незаметно получит дефолтную версию.\n\n"
            "Для этого проекта выбран путь через URL как самый предсказуемый вариант "
            "при командной разработке."
        ),
    },
    {
        "title": "Логирование и мониторинг",
        "tags": ["api", "architecture", "devops"],
        "content": (
            "# Логирование и мониторинг API\n\n"
            "Минимальный набор для продакшена:\n\n"
            "- Структурированные логи (JSON) вместо plain text — легче парсить в системах "
            "агрегации логов.\n"
            "- Request ID, прокидываемый через все сервисы — позволяет проследить один "
            "запрос через всю цепочку вызовов.\n"
            "- Метрики: количество запросов по эндпоинту, время ответа (percentiles), "
            "коды ответов по типам.\n"
            "- Алерты на резкий рост 5xx-ошибок или деградацию latency, а не только "
            "\"сервис недоступен\"."
        ),
    },
    {
        "title": "Схема базы данных проекта",
        "tags": ["architecture", "database"],
        "content": (
            "# Схема базы данных\n\n"
            "Основные таблицы и связи:\n\n"
            "- `users` — базовые данные пользователя.\n"
            "- `orders` — заказы, ForeignKey на `users`.\n"
            "- `order_items` — позиции заказа, ForeignKey на `orders` и `products`.\n"
            "- `products` — каталог товаров.\n\n"
            "Ключевые решения: денормализация цены товара в `order_items` (чтобы изменение "
            "цены в каталоге не меняло задним числом сумму старых заказов), индексы на "
            "`(user_id, created_at)` для быстрой выборки истории заказов пользователя."
        ),
    },
    {
        "title": "CI/CD пайплайн",
        "tags": ["devops", "architecture"],
        "content": (
            "# CI/CD пайплайн\n\n"
            "Этапы пайплайна при пуше в основную ветку:\n\n"
            "1. Линтинг и статический анализ (flake8/ruff, mypy).\n"
            "2. Юнит- и интеграционные тесты.\n"
            "3. Сборка Docker-образа с тегом по хешу коммита.\n"
            "4. Автодеплой на staging при успешных тестах.\n"
            "5. Ручное подтверждение для деплоя на прод.\n\n"
            "Важно: миграции БД выполняются отдельным шагом перед раскаткой новой версии "
            "приложения, а не внутри `entrypoint` контейнера — иначе при нескольких "
            "репликах миграция может запуститься параллельно несколько раз."
        ),
    },
    {
        "title": "Тестовая стратегия",
        "tags": ["testing", "architecture"],
        "content": (
            "# Тестовая стратегия проекта\n\n"
            "Пирамида тестов для API-проекта:\n\n"
            "- **Юнит-тесты** — бизнес-логика, сериализаторы, валидаторы. Быстрые, изолированные, "
            "большинство тестов должно быть здесь.\n"
            "- **Интеграционные тесты** — эндпоинты целиком, с реальной тестовой БД.\n"
            "- **Контрактные тесты** — проверяют, что формат ответа API не сломался для "
            "внешних потребителей (особенно важно при версионировании).\n"
            "- **E2E** — минимально, только критичные пользовательские сценарии, так как "
            "они медленные и хрупкие."
        ),
    },
    {
        "title": "Деплой и инфраструктура",
        "tags": ["devops", "architecture"],
        "content": (
            "# Деплой и инфраструктура\n\n"
            "Продовое окружение: несколько реплик приложения за балансировщиком, "
            "отдельная managed-БД, Redis для кэша и очередей фоновых задач.\n\n"
            "Стратегия деплоя — rolling update: новые реплики поднимаются и проходят "
            "healthcheck прежде, чем старые начинают выводиться из ротации. Это исключает "
            "полный простой сервиса во время релиза, ценой того, что старая и новая версия "
            "API какое-то время работают параллельно — важно держать обратную совместимость "
            "схемы БД между соседними релизами."
        ),
    },
]

# ---------------------------------------------------------------------------
# Сценарий 3: Личные исследования — изучение FastAPI
# ---------------------------------------------------------------------------
RESEARCH_NOTES = [
    {
        "title": "Введение в FastAPI",
        "tags": ["fastapi", "python", "backend"],
        "content": (
            "# Введение в FastAPI\n\n"
            "FastAPI — асинхронный веб-фреймворк на Python, построенный на Starlette и Pydantic. "
            "Главные плюсы: автогенерация OpenAPI-документации, валидация данных через типы "
            "Python, встроенная поддержка async/await.\n\n"
            "```python\n"
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/ping')\n"
            "async def ping():\n"
            "    return {'status': 'ok'}\n"
            "```\n\n"
            "В отличие от Django, FastAPI не навязывает ORM или структуру проекта — это "
            "минималистичный фреймворк, который нужно дособирать нужными библиотеками."
        ),
    },
    {
        "title": "Pydantic модели данных",
        "tags": ["fastapi", "pydantic", "python"],
        "content": (
            "# Pydantic модели данных\n\n"
            "Pydantic описывает форму данных через обычные аннотации типов и валидирует их "
            "на границе приложения:\n\n"
            "```python\n"
            "from pydantic import BaseModel, EmailStr\n\n"
            "class UserCreate(BaseModel):\n"
            "    email: EmailStr\n"
            "    age: int = 18\n"
            "```\n\n"
            "Если запрос не соответствует схеме, FastAPI автоматически возвращает 422 с "
            "детальным описанием, какое поле и почему не прошло валидацию — без единой "
            "строчки ручного кода."
        ),
    },
    {
        "title": "Dependency Injection в FastAPI",
        "tags": ["fastapi", "python", "architecture"],
        "content": (
            "# Dependency Injection в FastAPI\n\n"
            "Система зависимостей (`Depends`) позволяет переиспользовать логику между "
            "эндпоинтами — например, получение текущего пользователя или сессии БД:\n\n"
            "```python\n"
            "def get_db():\n"
            "    db = SessionLocal()\n"
            "    try:\n"
            "        yield db\n"
            "    finally:\n"
            "        db.close()\n\n"
            "@app.get('/users/{id}')\n"
            "async def get_user(id: int, db: Session = Depends(get_db)):\n"
            "    ...\n"
            "```\n\n"
            "Зависимости можно вкладывать друг в друга и переопределять в тестах через "
            "`app.dependency_overrides` — удобно для подмены реальной БД на тестовую."
        ),
    },
    {
        "title": "Асинхронные эндпоинты",
        "tags": ["fastapi", "async", "python"],
        "content": (
            "# Асинхронные эндпоинты\n\n"
            "FastAPI поддерживает и `def`, и `async def` обработчики. Разница важна: "
            "синхронный `def`-эндпоинт выполняется в отдельном thread pool, а `async def` — "
            "в основном event loop.\n\n"
            "Частая ошибка новичков — вызвать блокирующую (синхронную) операцию внутри "
            "`async def`-эндпоинта: это заблокирует весь event loop и остановит обработку "
            "остальных запросов, пока блокирующий вызов не завершится. Для блокирующих "
            "операций либо используют асинхронные библиотеки (asyncpg вместо psycopg2), "
            "либо выносят вызов в thread pool через `run_in_threadpool`."
        ),
    },
    {
        "title": "FastAPI + SQLAlchemy",
        "tags": ["fastapi", "database", "python"],
        "content": (
            "# FastAPI + SQLAlchemy\n\n"
            "FastAPI не включает ORM, самый частый выбор — SQLAlchemy. Два варианта работы:\n\n"
            "- **Синхронный** SQLAlchemy Session внутри `def`-эндпоинтов (проще для старта).\n"
            "- **Асинхронный** через `AsyncSession` и `asyncpg`/`asyncmy` драйверы — даёт "
            "реальный выигрыш в конкурентности, но требует асинхронных версий всех "
            "запросов и transaction-менеджмента.\n\n"
            "```python\n"
            "async with AsyncSession(engine) as session:\n"
            "    result = await session.execute(select(User).where(User.id == user_id))\n"
            "```"
        ),
    },
    {
        "title": "Аутентификация в FastAPI (OAuth2)",
        "tags": ["fastapi", "auth", "security"],
        "content": (
            "# Аутентификация в FastAPI\n\n"
            "FastAPI предоставляет готовые схемы безопасности из коробки, включая "
            "`OAuth2PasswordBearer` для password-flow с JWT-токенами:\n\n"
            "```python\n"
            "oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')\n\n"
            "@app.get('/me')\n"
            "async def read_me(token: str = Depends(oauth2_scheme)):\n"
            "    return decode_token(token)\n"
            "```\n\n"
            "Схема автоматически добавляется в OpenAPI-документацию, поэтому Swagger UI "
            "сразу показывает кнопку \"Authorize\" для тестирования защищённых эндпоинтов "
            "без написания дополнительного кода."
        ),
    },
    {
        "title": "Тестирование FastAPI с pytest",
        "tags": ["fastapi", "testing", "python"],
        "content": (
            "# Тестирование FastAPI\n\n"
            "`TestClient` из Starlette позволяет тестировать эндпоинты без поднятия "
            "реального сервера:\n\n"
            "```python\n"
            "from fastapi.testclient import TestClient\n\n"
            "client = TestClient(app)\n\n"
            "def test_ping():\n"
            "    response = client.get('/ping')\n"
            "    assert response.status_code == 200\n"
            "```\n\n"
            "Для тестирования async-кода с реальными async-зависимостями удобнее "
            "`httpx.AsyncClient` вместе с `pytest-asyncio` — особенно если приложение "
            "использует асинхронную сессию БД, которую нельзя дёшево подменить синхронным клиентом."
        ),
    },
    {
        "title": "Фоновые задачи в FastAPI",
        "tags": ["fastapi", "async", "python"],
        "content": (
            "# Фоновые задачи (BackgroundTasks)\n\n"
            "Для лёгких задач, которые не обязательно ждать перед ответом клиенту "
            "(отправка письма, запись в лог), FastAPI даёт встроенный `BackgroundTasks`:\n\n"
            "```python\n"
            "@app.post('/send-email')\n"
            "async def send(background_tasks: BackgroundTasks):\n"
            "    background_tasks.add_task(send_email, 'user@example.com')\n"
            "    return {'status': 'queued'}\n"
            "```\n\n"
            "Важно: это не полноценная очередь задач — задачи выполняются в том же "
            "процессе после отправки ответа. Для тяжёлых или требующих повторных попыток "
            "задач (обработка видео, интеграции с внешними API) нужен полноценный "
            "брокер очередей вроде Celery или arq."
        ),
    },
    {
        "title": "WebSocket в FastAPI",
        "tags": ["fastapi", "async", "python"],
        "content": (
            "# WebSocket в FastAPI\n\n"
            "FastAPI поддерживает WebSocket-эндпоинты нативно, без дополнительных библиотек:\n\n"
            "```python\n"
            "@app.websocket('/ws')\n"
            "async def websocket_endpoint(websocket: WebSocket):\n"
            "    await websocket.accept()\n"
            "    while True:\n"
            "        data = await websocket.receive_text()\n"
            "        await websocket.send_text(f'echo: {data}')\n"
            "```\n\n"
            "Для трансляции сообщений между несколькими подключёнными клиентами (чат, "
            "live-обновления) нужен отдельный менеджер соединений, хранящий список "
            "активных `WebSocket`-объектов, и/или Pub/Sub через Redis, если приложение "
            "работает в нескольких репликах."
        ),
    },
    {
        "title": "Деплой FastAPI приложения",
        "tags": ["fastapi", "devops"],
        "content": (
            "# Деплой FastAPI приложения\n\n"
            "FastAPI-приложение запускается через ASGI-сервер — обычно Uvicorn, часто "
            "под управлением Gunicorn с воркер-классом Uvicorn для нескольких процессов:\n\n"
            "```bash\n"
            "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4\n"
            "```\n\n"
            "В проде перед приложением обычно ставят reverse-proxy (nginx/Traefik) для "
            "терминации TLS, сжатия и раздачи статики, а само приложение упаковывают в "
            "Docker-образ на базе `python:slim` для минимизации размера."
        ),
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные заметки для трёх сценариев (учёба / проект / исследования)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", default="demo",
            help="Пользователь, которому будут принадлежать демо-заметки (создастся, если не существует)"
        )
        parser.add_argument(
            "--password", default="demo12345",
            help="Пароль для нового демо-пользователя (используется только при первом создании)"
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Удалить все существующие заметки этого пользователя перед созданием демо-набора"
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        user, user_created = User.objects.get_or_create(username=username)
        if user_created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Создан пользователь '{username}' / '{password}'"))
        else:
            self.stdout.write(f"Использую существующего пользователя '{username}'")

        if options["clear"]:
            deleted_count, _ = Note.objects.filter(user=user).delete()
            self.stdout.write(f"Удалено старых заметок: {deleted_count}")

        all_groups = [
            ("Учебный процесс", LEARNING_NOTES),
            ("Управление проектом", PROJECT_NOTES),
            ("Личные исследования", RESEARCH_NOTES),
        ]

        created_notes = []
        for group_name, group_notes in all_groups:
            for item in group_notes:
                note, created = Note.objects.update_or_create(
                    user=user, title=item["title"],
                    defaults={"content": item["content"]},
                )
                tag_objs = [Tag.objects.get_or_create(name=name)[0] for name in item["tags"]]
                note.tags.set(tag_objs)
                created_notes.append(note)
            self.stdout.write(f"  {group_name}: {len(group_notes)} заметок")

        # Строим связи между заметками по общим тегам — той же функцией,
        # которую использует боевой ai_services.run_ai_analysis.
        for note in created_notes:
            _update_relations(note, "демо-данные")

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово: {len(created_notes)} заметок создано/обновлено для пользователя '{username}'."
        ))
        self.stdout.write(f"Откройте /notes/ и /graph/ под этим пользователем, чтобы увидеть демо.")
