import json
import logging

from openai import OpenAI

from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
MODEL_NAME = "gpt-4o-mini"
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _get_client():
    if client is None:
        raise RuntimeError("Не задан OPENAI_API_KEY.")

    return client


def _build_image_content(prompt, image_urls):
    content = [{"type": "input_text", "text": prompt}]

    for image_url in image_urls:
        content.append({"type": "input_image", "image_url": image_url})

    return content


def _create_response(content):
    return _get_client().responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "user",
                "content": content
            }
        ]
    )


def _parse_questions_response(raw_text):
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.exception("OpenAI returned invalid JSON for TZ Pro questions")
        raise ValueError("OpenAI вернул некорректный JSON для вопросов.") from exc

    questions = parsed.get("questions")
    if not isinstance(questions, list):
        raise ValueError("OpenAI вернул ответ без списка questions.")

    return parsed


def generate_tz_lite(image_url):
    prompt = """
You are an expert in creating high-converting product image funnels for marketplaces.

Your task:
Analyze ONE product image and generate a clear technical brief (ТЗ) for a designer.

IMPORTANT:
- Final answer MUST be in Russian
- Do NOT use markdown (no ###, **, tables, code blocks)
- Use simple, clean formatting suitable for Telegram
- Keep text short and readable
- No long explanations
- No internal analysis

---

OUTPUT STRUCTURE:

ТЗ для фотоворонки

Общий стиль:
- Цвета:
- Фон:
- Стиль:
- Тон:

---

Слайды 1–5 (подробно)

Формат строго:

Слайд X — смысл

Что показываем:
Текст:
Цель:

Требования к тексту:
- максимум 1–2 короткие строки
- без клише
- конкретика
- читается за 1–2 секунды

---

Дополнительные слайды (кратко):

Слайд 6 — ...
Слайд 7 — ...
Слайд 8 — ...

(каждый — 1 короткая идея)

---

ПРАВИЛА:

- не выдумывать характеристики
- не использовать шаблонную структуру
- каждый слайд должен быть уникальным по смыслу
- избегать общих фраз типа "высокое качество"
- писать как маркетолог, а не как инструкция

---

Результат:
готовое ТЗ, которое можно сразу отдать дизайнеру
"""

    response = _create_response(_build_image_content(prompt, [image_url]))

    return response.output_text


def generate_tz_pro_questions(image_urls):
    prompt = """
Ты анализируешь товар по изображениям.

Твоя задача — сформировать 6 вопросов пользователю, чтобы уточнить данные для создания фотоворонки.

---

СТРУКТУРА:

Нужно вернуть:

- 4 фиксированных вопроса (всегда одинаковые)
- 2 умных вопроса (генерируются под товар)

---

ФИКСИРОВАННЫЕ ВОПРОСЫ:

Вопрос 1 — Что главное нужно подчеркнуть?

A. Внешний вид / дизайн
B. Функцию / пользу
C. Удобство / комфорт
D. Результат / эффект

Вопрос 2 — Как лучше показать товар?

A. В использовании
B. В окружении
C. Через детали
D. Смешанно

Вопрос 3 — Какой формат подачи нужен?

A. Минимализм
B. Инфографика
C. Эмоция / атмосфера
D. Смешанный

Вопрос 4 — Какой блок обязательно нужен?

A. Размеры / габариты
B. Характеристики / состав
C. Использование / сценарии
D. Комплектация

---

УМНЫЕ ВОПРОСЫ (5 и 6):

Требования:

- должны закрывать пробелы, которые нельзя понять по фото
- должны влиять на ТЗ
- должны быть конкретными
- каждый вопрос должен иметь 4 варианта ответа A/B/C/D
- не должны дублировать фиксированные вопросы
- не должны быть абстрактными
- не должны быть формальными

---

ЗАПРЕЩЕНО:

- задавать абстрактные вопросы
- задавать вопросы без влияния на визуал
- дублировать фиксированные вопросы

---

ФОРМАТ ОТВЕТА:

Верни строго JSON, без пояснений, без markdown, без текста до или после JSON.

Структура должна быть ровно такой:

{
  "questions": [
    {
      "question": "Что главное нужно подчеркнуть?",
      "options": {
        "A": "Внешний вид / дизайн",
        "B": "Функцию / пользу",
        "C": "Удобство / комфорт",
        "D": "Результат / эффект"
      }
    },
    {
      "question": "Как лучше показать товар?",
      "options": {
        "A": "В использовании",
        "B": "В окружении",
        "C": "Через детали",
        "D": "Смешанно"
      }
    },
    {
      "question": "Какой формат подачи нужен?",
      "options": {
        "A": "Минимализм",
        "B": "Инфографика",
        "C": "Эмоция / атмосфера",
        "D": "Смешанный"
      }
    },
    {
      "question": "Какой блок обязательно нужен?",
      "options": {
        "A": "Размеры / габариты",
        "B": "Характеристики / состав",
        "C": "Использование / сценарии",
        "D": "Комплектация"
      }
    },
    {
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      }
    },
    {
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      }
    }
  ]
}
"""

    response = _create_response(_build_image_content(prompt, image_urls))

    raw_text = response.output_text.strip()
    return _parse_questions_response(raw_text)

def generate_tz_pro_result(image_urls, answers, mode, base_prompt, mode_prompt):
    answers_text = "\n".join(
        [
            f"{index + 1}. Вопрос: {item['question']}\n"
            f"Ответ: {item['selected_option']} — {item['selected_text']}"
            for index, item in enumerate(answers)
        ]
    )

    content = [
        {
            "type": "input_text",
            "text": (
                f"{base_prompt}\n\n"
                f"{mode_prompt}\n\n"
                f"ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:\n{answers_text}\n\n"
                f"Сформируй готовое ТЗ."
            )
        }
    ]

    for image_url in image_urls:
        content.append({"type": "input_image", "image_url": image_url})

    response = _create_response(content)

    return response.output_text
