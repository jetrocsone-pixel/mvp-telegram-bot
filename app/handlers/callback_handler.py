import logging

from app.state import user_modes, user_data
from app.menus import (
    get_main_menu,
    get_pro_question_menu,
    get_tz_back_menu,
    get_tz_choice_menu,
    get_tz_pro_upload_menu,
)
from app.telegram_api import send_message, answer_callback_query
from app.services.openai_service import generate_tz_pro_questions, generate_tz_pro_result

logger = logging.getLogger(__name__)


def format_pro_question(question_data, question_number):
    return (
        f"Вопрос {question_number} из 6\n\n"
        f"{question_data['question']}\n\n"
        f"A. {question_data['options']['A']}\n"
        f"B. {question_data['options']['B']}\n"
        f"C. {question_data['options']['C']}\n"
        f"D. {question_data['options']['D']}"
    )


BASE_PROMPT_PRO = """
You are a senior expert in creating high-converting product image funnels for marketplaces (Wildberries, Ozon).

Your task is NOT to explain anything.

Your task is to produce a STRICT, structured technical brief (ТЗ) for a designer.

INPUT:

product images
user answers
USER ANSWERS PRIORITY

You MUST use user answers.

They directly define:

structure
emphasis
visual decisions

Ignoring them = incorrect result.

INTERNAL ANALYSIS (DO NOT OUTPUT)

Determine internally:

product type
2–3 key selling points
presentation logic

Immediately proceed to slide generation.

DO NOT describe this analysis.

VISUAL STYLE (OUTPUT REQUIRED)

Define clearly:

color palette (2–3 colors)
background type (SPECIFIC real-world scenes)
graphic style (icons / blocks / minimalism)
tone (premium / neutral / aggressive / emotional)

IMPORTANT:
Style MUST be consistent across ALL slides.

HARD RULES (STRICT)

You MUST follow:

Slide 1: product occupies 60–80% of frame
NO split-screen on first slide
ONE slide = ONE idea
text = 1–2 short lines ONLY
NO abstract backgrounds

FORBIDDEN:
"beauty", "nice", "lifestyle" without explanation

Each background MUST include:

location
objects
lighting
TECH CHARACTERISTICS (STRICT)

If product has ANY functionality:

You MUST:

include a characteristics slide
define EXACT structure

DO NOT write:
"table with characteristics"

You MUST define structure:

For tech:

power: ___
battery: ___
connection: ___
compatibility: ___
functions: ___

For clothing:

material: ___
fit: ___
stretch: ___
waistband: ___

DO NOT invent values.

SLIDES STRUCTURE (STRICT)

Generate 6–9 slides.

Each slide MUST follow EXACT structure:

Слайд X — [смысл]

Сюжет:
(what is happening)

Фон:
MUST include:

location
objects
lighting

Композиция:
(positioning of product)

Текст:
(1–2 short lines ONLY)

Графика:
(icons / highlights / arrows)

Цель:
(what user must understand)

MANDATORY CATEGORY STRUCTURE (CRITICAL)

You MUST follow strict category logic.

IF CLOTHING:

You MUST follow this order:

look / outfit
fit (how it sits)
details (construction)
fabric (behavior)
size (MANDATORY)
optional: styling (only if strong)

Maximum: 7 slides

FORBIDDEN:

comfort slides
trust slides
generic lifestyle slides
season slides

IF TECH:

You MUST include:

usage
key function
characteristics (MANDATORY)
connection / compatibility
additional features

IF UTILITY:

You MUST include:

problem
solution
process
result

If violated → result is incorrect.

FORBIDDEN GENERIC SLIDES

You MUST NOT create slides like:

"comfort"
"trust"
"final message"
"collection"
"season"

Each slide MUST answer a buying decision.

If not → remove slide.

SEASON HANDLING
DO NOT ask about season
DO NOT create season slides

Only include if clearly visible.

STRICT PROHIBITIONS
DO NOT skip structure
DO NOT generalize
DO NOT repeat slide meanings
DO NOT invent product data
DO NOT write explanations
FINAL CHECK (MANDATORY)

Before output:

each slide is unique
no duplicated meanings
all backgrounds are SPECIFIC
characteristics are structured

OUTPUT RULES:

Russian language ONLY
plain text ONLY
NO markdown
NO symbols (#, *, etc.)

FINAL RESULT:

A complete, structured, production-ready technical brief.
"""

MODE_STANDARD = """
MODE: STANDARD

Priority:
- clarity of the product
- safe structure
- predictable conversion

Rules:
- first slide must be simple and clean
- product is the main focus
- no complex compositions
- no visual overload
- structure must be clear and logical
"""

MODE_BALANCE = """
MODE: BALANCE

Priority:
- balance between sales logic and visual attractiveness

Rules:
- first slide remains clear and readable
- product remains the main focus

Allowed:
- more interesting compositions
- light storytelling
- emotional elements
- visual accents

Restrictions:
- do not lose product clarity
- do not overload the frame
"""

MODE_CREATIVE = """
MODE: CREATIVE

Priority:
- strong visual differentiation
- high CTR
- нестандартная подача

Allowed:
- unconventional compositions
- storytelling
- contrasts
- before/after scenes
- нестандартные сцены

Rules:
- product must remain understandable
- do not fully hide the product

Goal:
- grab attention
- stand out in marketplace feed
"""


def handle_callback_query(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    callback_data = callback["data"]
    logger.info("Handling callback for chat_id=%s data=%s", chat_id, callback_data)

    answer_callback_query(callback_id)

    if callback_data == "tz_lite":
        user_modes[chat_id] = "tz_lite_wait_photo"
        user_data[chat_id] = {}

        send_message(
            chat_id,
            "Режим ТЗ Lite активирован.\n\n"
            "Отправь 1 фото товара.\n"
            "Лучше всего отправлять как файл без сжатия.",
            reply_markup=get_tz_back_menu()
        )

    elif callback_data == "tz_pro":
        user_modes[chat_id] = "tz_pro_wait_photos"
        user_data[chat_id] = {
            "photos": []
        }

        send_message(
            chat_id,
            "Режим ТЗ Pro активирован.\n\n"
            "Шаг 1: отправь от 1 до 3 фото товара.\n"
            "Лучше всего отправлять как файл без сжатия.\n\n"
            "Когда закончишь загрузку, нажми «Готово».",
            reply_markup=get_tz_pro_upload_menu()
        )

    elif callback_data == "tz_pro_done":
        photos = user_data.get(chat_id, {}).get("photos", [])

        if len(photos) == 0:
            send_message(
                chat_id,
                "Ты ещё не отправил ни одного фото.\n\n"
                "Сначала отправь от 1 до 3 фото товара, потом нажми «Готово».",
                reply_markup=get_tz_pro_upload_menu()
            )
        else:
            send_message(
                chat_id,
                "Фото получены.\n\n"
                "Генерирую вопросы для ТЗ Pro. Это может занять до 20–40 секунд."
            )

            try:
                questions_result = generate_tz_pro_questions(photos)
                questions = questions_result.get("questions", [])

                if len(questions) != 6:
                    send_message(
                        chat_id,
                        "Не удалось корректно сформировать 6 вопросов. Попробуй ещё раз.",
                        reply_markup=get_tz_back_menu()
                    )
                else:
                    user_modes[chat_id] = "tz_pro_questions"
                    user_data[chat_id]["questions"] = questions
                    user_data[chat_id]["answers"] = []
                    user_data[chat_id]["current_question_index"] = 0

                    first_question = questions[0]

                    send_message(
                        chat_id,
                        format_pro_question(first_question, 1),
                        reply_markup=get_pro_question_menu()
                    )

            except Exception as e:
                send_message(
                    chat_id,
                    f"Ошибка при генерации вопросов:\n{str(e)}",
                    reply_markup=get_tz_back_menu()
                )

    elif callback_data.startswith("pro_answer_"):
        if user_modes.get(chat_id) != "tz_pro_questions":
            return {"ok": True}

        answer = callback_data.split("_")[-1]

        user_data[chat_id]["answers"].append(answer)
        user_data[chat_id]["current_question_index"] += 1

        current_index = user_data[chat_id]["current_question_index"]
        questions = user_data[chat_id]["questions"]

        if current_index < 6:
            next_question = questions[current_index]

            send_message(
                chat_id,
                format_pro_question(next_question, current_index + 1),
                reply_markup=get_pro_question_menu()
            )
        else:
            user_modes[chat_id] = "tz_pro_mode_choice"

            send_message(
                chat_id,
                "Отлично. Все ответы получены.\n\nВыбери формат ТЗ:",
                reply_markup={
                    "inline_keyboard": [
                        [
                            {"text": "Стандарт", "callback_data": "tz_pro_mode_standard"},
                            {"text": "Баланс", "callback_data": "tz_pro_mode_balance"},
                            {"text": "Креатив", "callback_data": "tz_pro_mode_creative"}
                        ],
                        [
                            {"text": "Назад к выбору ТЗ", "callback_data": "back_to_tz_choice"}
                        ]
                    ]
                }
            )

    elif callback_data in ["tz_pro_mode_standard", "tz_pro_mode_balance", "tz_pro_mode_creative"]:
        if user_modes.get(chat_id) != "tz_pro_mode_choice":
            return {"ok": True}

        if callback_data == "tz_pro_mode_standard":
            selected_mode = "standard"
            mode_prompt = MODE_STANDARD
        elif callback_data == "tz_pro_mode_balance":
            selected_mode = "balance"
            mode_prompt = MODE_BALANCE
        else:
            selected_mode = "creative"
            mode_prompt = MODE_CREATIVE

        user_data[chat_id]["selected_tz_mode"] = selected_mode

        send_message(
            chat_id,
            "Генерирую финальное ТЗ Pro. Это может занять до 30–60 секунд."
        )

        try:
            questions = user_data[chat_id]["questions"]
            raw_answers = user_data[chat_id]["answers"]
            image_urls = user_data[chat_id]["photos"]

            structured_answers = []

            for i, answer_letter in enumerate(raw_answers):
                question_item = questions[i]
                structured_answers.append({
                    "question": question_item["question"],
                    "selected_option": answer_letter,
                    "selected_text": question_item["options"][answer_letter]
                })

            result_text = generate_tz_pro_result(
                image_urls=image_urls,
                answers=structured_answers,
                mode=selected_mode,
                base_prompt=BASE_PROMPT_PRO,
                mode_prompt=mode_prompt
            )

            user_modes[chat_id] = None

            send_message(
                chat_id,
                result_text,
                reply_markup=get_main_menu()
            )

        except Exception as e:
            send_message(
                chat_id,
                f"Ошибка при генерации финального ТЗ Pro:\n{str(e)}",
                reply_markup=get_main_menu()
            )

    elif callback_data == "back_to_tz_choice":
        user_modes[chat_id] = None
        user_data[chat_id] = {}

        send_message(
            chat_id,
            "Выбери формат ТЗ:",
            reply_markup=get_tz_choice_menu()
        )

    elif callback_data == "back_to_main":
        user_modes[chat_id] = None
        user_data[chat_id] = {}

        send_message(
            chat_id,
            "Возвращаю в главное меню.",
            reply_markup=get_main_menu()
        )

    return {"ok": True}
