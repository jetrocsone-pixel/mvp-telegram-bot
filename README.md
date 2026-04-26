# MVP Telegram Bot

Небольшой Telegram-бот на `FastAPI` с webhook-обработкой.

Что умеет:
- удалять фон у изображения через `remove.bg`
- генерировать `ТЗ Lite` по одному фото
- генерировать `ТЗ Pro` по 1-3 фото с промежуточными вопросами

## Структура

- `app/main.py` — вход в приложение и webhook-маршрутизация
- `app/handlers/` — обработчики текста, фото, документов и callback-кнопок
- `app/services/openai_service.py` — работа с OpenAI
- `app/services/remove_bg.py` — работа с remove.bg
- `app/telegram_api.py` — отправка сообщений и файлов в Telegram
- `app/texts.py` — тексты кнопок и пользовательские сообщения

## Переменные окружения

Нужны 3 переменные:

- `BOT_TOKEN` — токен Telegram-бота
- `OPENAI_API_KEY` — ключ OpenAI
- `REMOVE_BG_API_KEY` — ключ remove.bg

## Локальный запуск

1. Установить зависимости:

```powershell
pip install -r requirements.txt
```

2. Задать переменные окружения в PowerShell:

```powershell
$env:BOT_TOKEN="your_bot_token"
$env:OPENAI_API_KEY="your_openai_key"
$env:REMOVE_BG_API_KEY="your_remove_bg_key"
```

3. Запустить приложение:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Проверить healthcheck:

```powershell
curl http://127.0.0.1:8000/
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Webhook

Для работы с Telegram нужен публичный URL.

Пример установки webhook:

```text
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-domain/webhook
```

## Деплой в Render

Минимальная схема:

1. Залить проект в GitHub.
2. Подключить репозиторий в Render.
3. Создать `Web Service`.
4. Указать команду запуска:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. В Render задать переменные:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `REMOVE_BG_API_KEY`

6. После деплоя установить webhook на адрес:

```text
https://your-render-service.onrender.com/webhook
```

## Базовая проверка после деплоя

Проверьте:

1. `GET /` возвращает `{"status":"ok"}`
2. Бот отвечает на `/start`
3. Удаление фона возвращает `removed_bg.png`
4. `ТЗ Lite` отрабатывает по одному фото
5. `ТЗ Pro` принимает 1-3 фото, задаёт 6 вопросов и возвращает итоговое ТЗ

## Git workflow

Типовой цикл:

```powershell
git status
git diff
git add .
git commit -m "Describe changes"
git push
```

## Ограничения текущей версии

- состояние пользователей хранится в памяти процесса
- при перезапуске приложения диалоги сбрасываются
- для нескольких инстансов нужен внешний storage
