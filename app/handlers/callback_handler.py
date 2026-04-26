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
You are an expert in creating high-converting product image funnels for marketplaces.

You are given:
- product images
- user answers to key questions

Your task:
Create a detailed technical brief (ТЗ) for a designer.

---

1. USE USER ANSWERS

- User answers are PRIORITY
- They must directly influence structure, emphasis, and presentation

---

2. DETERMINE INTERNALLY (DO NOT OUTPUT)

- product type
- key selling points
- logic of presentation

---

3. DEFINE OVERALL VISUAL STYLE

Describe:

- color palette (2–3 main colors)
- background type (specific, not abstract)
- graphic style (minimalism / infographics / mixed)
- tone (premium / neutral / aggressive / emotional)

This style must be consistent across ALL slides.

---

4. CRITICAL RULES

- first slide: product must occupy 60–80% of the frame
- no split screens
- one slide = one idea
- short text only
- no abstract or meaningless backgrounds

---

5. TECH LOGIC (IMPORTANT)

If product is technical:

- include a characteristics slide
- use numbers where appropriate

If data is missing:

- define a logical structure without inventing facts

---

6. SLIDES STRUCTURE

Total: 6–9 slides

Format:

Slide X — meaning

Сюжет:
Фон:
Композиция:
Текст:
Графика:
Цель:

---

7. LOGIC

Build structure depending on product type:

- clothing → fit / look / details / size
- tech → specs / usage / compatibility / safety
- utility → problem / solution / process / result
- furniture → visual / function / dimensions / trust
- consumer goods → aesthetics / atmosphere / packaging

---

8. STRICT PROHIBITIONS

- do NOT invent characteristics
- do NOT repeat slide meanings
- do NOT use шаблонные структуры
- do NOT write theory

---

9. QUALITY CHECK BEFORE OUTPUT

- remove weak phrases
- remove vague statements
- ensure each slide has a unique role
- ensure no duplicated смысл

---

IMPORTANT OUTPUT RULES:

- Final answer MUST be written in Russian
- Do NOT use markdown formatting
- Do NOT use symbols like #, ##, ###, **, *, or backticks
- Do NOT use decorative formatting
- Use clean plain text only

Telegram formatting rules:
- separate blocks with empty lines
- keep structure readable
- avoid visual noise

The structure must remain detailed, but visually clean.

---

Result:
A complete, ready-to-use technical brief for a designer.
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
