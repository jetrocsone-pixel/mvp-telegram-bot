# MVP Telegram Bot

Телеграм-бот на `FastAPI` с webhook-обработкой.

Сейчас бот умеет:
- удалять фон у изображения через `remove.bg`
- генерировать `ТЗ Lite` по одному фото
- генерировать `ТЗ Pro` по 1-3 фото с промежуточными вопросами

## Текущая структура проекта

Основные файлы:

- `app/main.py` — вход в приложение, healthcheck и webhook
- `app/config.py` — переменные окружения
- `app/telegram_api.py` — работа с Telegram API
- `app/texts.py` — тексты кнопок и сообщений
- `app/callbacks.py` — callback-константы
- `app/menus.py` — inline и reply-клавиатуры
- `app/state.py` — in-memory state пользователей

Обработчики:

- `app/handlers/text_handler.py` — обработка текста и `/start`
- `app/handlers/callback_handler.py` — сценарии `ТЗ Lite` / `ТЗ Pro`
- `app/handlers/photo_handler.py` — обработка фото
- `app/handlers/document_handler.py` — обработка документов-изображений
- `app/handlers/image_helpers.py` — общий код для image-сценариев

Сервисы:

- `app/services/openai_service.py` — вызовы OpenAI
- `app/services/remove_bg.py` — вызовы remove.bg
- `app/services/prompts.py` — prompt-ы для `ТЗ Pro`

Инфраструктура:

- `app/logging_config.py` — базовая настройка логирования

## Что важно про текущую реализацию

- состояние пользователей хранится в памяти процесса
- при перезапуске Render диалоги сбрасываются
- для нескольких инстансов нужен внешний storage
- длинные сообщения в Telegram режутся на части, чтобы не упираться в лимит `4096` символов

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

2. Задать переменные окружения:

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

После запуска нужен публичный URL.

Пример установки webhook:

```text
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-domain/webhook
```

## Деплой в Render

Минимальная схема:

1. Залить проект в GitHub.
2. Подключить репозиторий в Render.
3. Создать `Web Service`.
4. Указать стартовую команду:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. В Render задать переменные:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `REMOVE_BG_API_KEY`

6. После успешного деплоя установить webhook:

```text
https://your-render-service.onrender.com/webhook
```

## Как безопасно выкатывать изменения

Перед `push`:

```powershell
git status
git diff
```

Потом:

```powershell
git add .
git commit -m "Describe changes"
git push
```

Важно:
- Render деплоит только то, что реально попало в GitHub
- если файл изменен локально, но не закоммичен, Render его не увидит
- если после деплоя ошибка `ImportError`, сначала проверьте, что нужный файл действительно вошел в последний commit

## Что проверять после деплоя

Проверьте:

1. `GET /` возвращает `{"status":"ok"}`
2. Бот отвечает на `/start`
3. Удаление фона возвращает `removed_bg.png`
4. `ТЗ Lite` отрабатывает по одному фото
5. `ТЗ Pro`:
   - принимает 1-3 фото
   - задает 6 вопросов
   - показывает выбор режима `Стандарт / Баланс / Креатив`
   - возвращает итоговое ТЗ
6. Длинный итог `ТЗ Pro` доходит пользователю полностью, а не теряется

## Частые причины падения деплоя

1. Локальные правки не были закоммичены и не попали в GitHub.
2. Новый импорт добавлен, но соответствующий файл не был отправлен в репозиторий.
3. Ошибка в имени модуля или функции после рефакторинга.
4. Не заданы переменные окружения в Render.

## Логи

Смотреть в Render:

- `Deploy logs` — ошибки сборки и старта
- `Runtime logs` — ошибки во время работы webhook

Если бот не запускается, нужен traceback целиком, начиная с первой строки ошибки.
