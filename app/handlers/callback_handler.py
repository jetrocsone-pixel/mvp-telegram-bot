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
Ты — эксперт по созданию продающих фотоворонок для маркетплейсов.

У тебя есть:

* изображения товара
* ответы пользователя

Задача: создать ТЗ для дизайнера.

---

1. УЧТИ ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ

* ответы приоритетны
* влияют на структуру и подачу

---

2. ОПРЕДЕЛИ (внутри)

* тип товара
* ключевые смыслы
* логику подачи

---

3. ОБЩАЯ СТИЛИСТИКА

* цвета
* фон (конкретный)
* стиль графики
* тон

---

4. КРИТИЧНЫЕ ПРАВИЛА

* товар на первом слайде 60–80%
* без split
* каждый слайд = 1 смысл
* короткий текст
* без абстрактных фонов

---

5. ТЕХНИКА (ОБЯЗАТЕЛЬНО)

Если техника:

* добавить слайд характеристик
* использовать цифры

если нет данных:

* задать структуру

---

6. СЛАЙДЫ

6–9 слайдов

Формат:

Слайд X — смысл

Сюжет:
Фон:
Композиция:
Текст:
Графика:
Цель:

---

7. ЛОГИКА

строить под тип товара

---

8. ЗАПРЕТЫ

* не добавлять лишнее
* не менять структуру
* не писать теорию

---

Результат — готовое ТЗ
"""

MODE_STANDARD = """
MODE — STANDARD

Приоритет:

* читаемость товара
* корректная работа алгоритмов
* минимальный риск

Правила:

* первый слайд простой и чистый

* товар — главный объект

* без split-экранов

* без перегруза

* структура понятная и продающая

* без экспериментов, которые мешают восприятию
"""

MODE_BALANCE = """
MODE — BALANCED

Приоритет:

* сочетание продающей логики и визуальной выразительности

Правила:

* первый слайд остаётся читаемым и понятным
* товар должен быть главным объектом

Допускается:

* более интересные композиции
* лёгкий сторителлинг
* эмоциональные сцены
* визуальные акценты

Ограничения:

* нельзя терять читаемость товара
* нельзя перегружать кадр
* нельзя усложнять главный слайд

Цель:

* выделиться среди конкурентов
* сохранить безопасность
"""

MODE_CREATIVE = """
MODE — CREATIVE

Приоритет:

* максимальное визуальное выделение
* высокий CTR
* нестандартная подача

Допускается:

* нестандартные композиции
* сторителлинг
* контрасты
* до/после
* нестандартные сцены

Можно:

* отходить от классической структуры
* усиливать эмоцию
* использовать неожиданные визуальные решения

Ограничения:

* товар должен оставаться понятным
* нельзя полностью терять объект

Цель:

* привлечь внимание
* выбиться из потока карточек
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
