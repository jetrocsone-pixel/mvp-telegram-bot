import json
import logging

from openai import OpenAI

from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
MODEL_NAME = "gpt-4o-mini"
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


TZ_LITE_PROMPT = """
Ты анализируешь фото товара для маркетплейса.

Задача: по ОДНОЙ фотографии товара создать готовое ТЗ для дизайнера на продающую фотоворонку.

Требования:
- определи товар только по тому, что реально видно на фото
- не выдумывай характеристики, которых нельзя понять по изображению
- выдели ключевые смыслы, которые стоит показать в карточке
- предложи структуру слайдов

Формат ответа:

Слайд 1 — ...
Что изображено:
Текст на изображении:
Цель слайда:

Слайд 2 — ...
Что изображено:
Текст на изображении:
Цель слайда:

Слайд 3 — ...
Что изображено:
Текст на изображении:
Цель слайда:

Слайд 4 — ...
Что изображено:
Текст на изображении:
Цель слайда:

Слайд 5 — ...
Что изображено:
Текст на изображении:
Цель слайда:

Если уместно, добавь слайды 6-8 кратко.

Ответ должен быть четким, структурным, без лишней теории.
"""


TZ_PRO_QUESTIONS_PROMPT = """
Ты анализируешь товар по изображениям.

Твоя задача — сформировать 6 вопросов пользователю, чтобы уточнить данные для создания фотоворонки.

Нужно вернуть:
- 4 фиксированных вопроса
- 2 умных вопроса по товару

Фиксированные вопросы должны быть ровно такими:

1. Что главное нужно подчеркнуть?
A. Внешний вид / дизайн
B. Функцию / пользу
C. Удобство / комфорт
D. Результат / эффект

2. Как лучше показать товар?
A. В использовании
B. В окружении
C. Через детали
D. Смешанно

3. Какой формат подачи нужен?
A. Минимализм
B. Инфографика
C. Эмоция / атмосфера
D. Смешанный

4. Какой блок обязательно нужен?
A. Размеры / габариты
B. Характеристики / состав
C. Использование / сценарии
D. Комплектация

Для вопросов 5 и 6:
- спрашивай только то, чего не видно по фото
- вопросы должны влиять на визуальную подачу
- не дублируй фиксированные вопросы
- не задавай абстрактные вопросы
- у каждого вопроса должно быть 4 варианта ответа A/B/C/D

Верни строго JSON без markdown и без пояснений в формате:
{
  "questions": [
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
                "content": content,
            }
        ],
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

    if len(questions) != 6:
        raise ValueError("OpenAI вернул не 6 вопросов.")

    return parsed


def generate_tz_lite(image_url):
    response = _create_response(_build_image_content(TZ_LITE_PROMPT, [image_url]))
    return response.output_text


def generate_tz_pro_questions(image_urls):
    response = _create_response(_build_image_content(TZ_PRO_QUESTIONS_PROMPT, image_urls))
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

    prompt = (
        f"{base_prompt}\n\n"
        f"{mode_prompt}\n\n"
        f"ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:\n{answers_text}\n\n"
        f"Сформируй готовое ТЗ."
    )

    response = _create_response(_build_image_content(prompt, image_urls))
    return response.output_text
