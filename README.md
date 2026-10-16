# Deribit Prices Service

Сервис собирает индексную цену (`index price`) по валютам `btc_usd` и `eth_usd` с биржи
[Deribit](https://docs.deribit.com/), сохраняет её в PostgreSQL и отдаёт через HTTP API.

Сбор запускается периодической задачей Celery раз в минуту. Каждая запись содержит тикер,
цену и время получения в формате UNIX timestamp.

## Стек

| Компонент | Технология |
|---|---|
| API | FastAPI |
| База данных | PostgreSQL, SQLAlchemy 2.0 (async), Alembic |
| Периодические задачи | Celery + Celery beat |
| Брокер | Redis |
| HTTP-клиент биржи | aiohttp |
| Тесты | pytest |

## Структура проекта

```
app/
├── api/
│   ├── dependencies.py       # провайдеры зависимостей FastAPI
│   └── routers/prices.py     # HTTP-эндпоинты
├── clients/deribit_client.py # HTTP-клиент Deribit
├── core/
│   ├── config.py             # настройки приложения
│   └── database.py           # движок и фабрика сессий
├── models/price.py           # ORM-модель
├── repositories/             # доступ к данным
├── schemas/price.py          # Pydantic-схемы и перечень тикеров
├── services/price_service.py # бизнес-логика
├── tasks/                    # приложение Celery и задача сбора цен
└── main.py                   # фабрика приложения
alembic/                      # миграции
tests/                        # unit-тесты
```

## Быстрый старт в Docker

Требуется Docker и Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Поднимаются пять контейнеров: `db`, `redis`, `api`, `worker`, `beat`. Миграции применяются
автоматически при старте `api`.

После запуска доступны:

- API — http://localhost:8000
- Swagger UI — http://localhost:8000/docs

Первые записи появляются в базе через минуту после старта (интервал сбора задаётся
переменной `PRICE_COLLECTION_INTERVAL`).

Проверить сохранённые данные:

```bash
docker compose exec db psql -U prices -d prices -c "select * from prices order by timestamp desc limit 10;"
```

Остановить и удалить данные:

```bash
docker compose down -v
```

## Запуск без Docker

Нужны локально запущенные PostgreSQL и Redis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# в .env заменить хосты db и redis на localhost

alembic upgrade head
uvicorn app.main:create_app --factory --reload
```

В отдельных терминалах — воркер и планировщик:

```bash
celery -A app.tasks.celery_app:celery_app worker --loglevel=info
celery -A app.tasks.celery_app:celery_app beat --loglevel=info
```

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | параметры контейнера с БД | `prices` |
| `DATABASE_URL` | DSN для приложения | — |
| `REDIS_URL` | адрес брокера Celery | — |
| `DERIBIT_BASE_URL` | базовый URL API биржи | `https://www.deribit.com/api/v2` |
| `DERIBIT_REQUEST_TIMEOUT` | таймаут запроса к бирже, секунды | `10` |
| `PRICE_COLLECTION_INTERVAL` | интервал сбора цен, секунды | `60` |

## API

Все методы — `GET`, у всех обязателен query-параметр `ticker` со значением `btc_usd` или
`eth_usd`. Неизвестный или отсутствующий тикер даёт `422`, отсутствие данных — `404`.

### `GET /prices` — все сохранённые данные по валюте

```bash
curl "http://localhost:8000/prices?ticker=btc_usd"
```

```json
[
  {"ticker": "btc_usd", "price": "81289.29000000", "timestamp": 1792172159}
]
```

### `GET /prices/latest` — последняя цена валюты

```bash
curl "http://localhost:8000/prices/latest?ticker=eth_usd"
```

```json
{"ticker": "eth_usd", "price": "2415.94000000", "timestamp": 1792172159}
```

### `GET /prices/filter` — цены с фильтром по дате

Границы диапазона передаются в UNIX timestamp, обе необязательные и могут задаваться
по отдельности.

```bash
curl "http://localhost:8000/prices/filter?ticker=btc_usd&date_from=1792170000&date_to=1792180000"
```

```json
[
  {"ticker": "btc_usd", "price": "81289.29000000", "timestamp": 1792172159}
]
```

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

Тесты не требуют ни запущенной базы, ни сети: репозиторий проверяется на SQLite в памяти,
обращения к бирже и слой данных подменяются моками.

## Design decisions

**Разделение на слои.** Код разбит на клиент биржи, репозиторий, сервис и API. Репозиторий
знает только про запросы к базе, сервис содержит бизнес-логику и не зависит от деталей
SQLAlchemy, роутеры отвечают только за HTTP. Благодаря этому задача Celery и HTTP-API
переиспользуют один и тот же `PriceService`, а в тестах любой слой подменяется моком.

**Отсутствие глобального состояния.** Настройки описаны классом `Settings` и передаются
явно. Движок базы и HTTP-клиент создаются в `lifespan` фабрики `create_app()` и живут в
`app.state`, а в обработчики попадают через `Depends`. Приложение запускается как
`uvicorn app.main:create_app --factory`, поэтому модульного экземпляра `app` нет.
Единственный объект уровня модуля — приложение Celery: это точка входа для `celery -A`,
и создаётся оно той же фабрикой `create_celery_app()`.

**Цена хранится как `Numeric(20, 8)`.** Числа с плавающей точкой округляют денежные
значения, поэтому цена хранится и возвращается как `Decimal`. В JSON она сериализуется
строкой — так клиент не теряет точность при разборе ответа.

**Время хранится как UNIX timestamp в `BigInteger`.** Этого требует постановка задачи,
и это снимает вопросы часовых поясов. Фильтр по дате принимает те же timestamp, что
лежат в базе, поэтому границы диапазона не нужно преобразовывать.

**Составной индекс `(ticker, timestamp)`.** Все три запроса фильтруют по тикеру и
сортируют по времени, так что один индекс покрывает и выборку последней цены, и фильтр
по диапазону.

**`asyncio.run` внутри задачи Celery.** Приложение асинхронное, а воркер Celery —
синхронный, поэтому задача запускает корутину через `asyncio.run`. Каждый запуск создаёт
свой event loop, и переиспользовать пул соединений между запусками нельзя: соединения
остались бы привязаны к уже закрытому циклу. Поэтому в задаче движок создаётся с
`NullPool` и закрывается в `finally`.

**Повторные попытки при ошибке биржи.** Сетевые сбои и таймауты клиент оборачивает в
`DeribitClientError`, а задача повторяется до трёх раз с экспоненциальной задержкой.
Пропуск одного тика лучше, чем потерянная минута данных.

**Тикеры как перечисление.** `Ticker` — `StrEnum`, который FastAPI использует для
валидации query-параметра. Неизвестная валюта отсекается на входе с кодом `422` и не
доходит до базы, а список поддерживаемых значений виден в Swagger.

**Состав контейнеров.** В задании предлагалось два контейнера — приложение и база.
Celery требует брокер, поэтому добавлен `redis`, а воркер и планировщик вынесены в
отдельные контейнеры: это разные процессы с разным жизненным циклом, их удобно
перезапускать и масштабировать независимо. Все контейнеры приложения собираются из
одного образа и отличаются только командой запуска.

**404 вместо пустого списка.** Если данных по валюте нет, сервис бросает
`PriceNotFoundError`, а обработчик уровня приложения превращает его в `404`. Так
клиент сразу отличает «данные ещё не собраны» от успешного пустого ответа.
