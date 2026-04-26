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
You analyze product images.

Your task is to generate EXACTLY 6 questions for the user to уточнить данные для создания фотоворонки.

STRUCTURE:

You MUST return:

4 FIXED questions (always identical)
2 AI-generated questions (dynamic)

FIXED QUESTIONS (DO NOT MODIFY):

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

AI QUESTIONS (5–6) — CRITICAL RULES

You MUST:

analyze what is NOT visible in images
ask ONLY about missing information
ensure questions directly affect visual output
make questions DIFFERENT each time
adapt questions to product type

STRICTLY FORBIDDEN:

asking about season
asking about weather
asking about time of year
asking generic questions
repeating same question logic
rephrasing fixed questions

If any question is about season → result is INVALID.

GOOD QUESTION TYPES:

material details
fit / structure
functionality
usage specifics
differentiators
product behavior

BAD QUESTION TYPES:

когда использовать
для какого сезона
что важно
что лучше
любые общие вопросы без конкретики

FORMAT REQUIREMENTS:

Questions must be clear and short
Each question MUST have exactly 4 options (A/B/C/D)
Options must be meaningful and different
No duplicate meanings between options

OUTPUT FORMAT (STRICT):

Return ONLY JSON.

No explanations.
No markdown.
No extra text.

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
