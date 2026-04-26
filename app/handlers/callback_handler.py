import logging

from app.callbacks import (
    CB_BACK_TO_MAIN,
    CB_BACK_TO_TZ_CHOICE,
    CB_PRO_ANSWER_PREFIX,
    CB_TZ_LITE,
    CB_TZ_PRO,
    CB_TZ_PRO_DONE,
    CB_TZ_PRO_MODE_BALANCE,
    CB_TZ_PRO_MODE_CREATIVE,
    CB_TZ_PRO_MODE_STANDARD,
)
from app.menus import (
    get_main_menu,
    get_pro_question_menu,
    get_tz_back_menu,
    get_tz_choice_menu,
    get_tz_pro_mode_menu,
    get_tz_pro_upload_menu,
)
from app.services.openai_service import generate_tz_pro_questions, generate_tz_pro_result
from app.services.prompts import BASE_PROMPT_PRO, MODE_BALANCE, MODE_CREATIVE, MODE_STANDARD
from app.state import user_data, user_modes
from app.telegram_api import answer_callback_query, send_message
from app.texts import (
    MSG_RETURN_TO_MAIN,
    MSG_TZ_CHOICE,
    MSG_TZ_LITE_ACTIVATED,
    MSG_TZ_PRO_ACTIVATED,
    MSG_TZ_PRO_ALL_ANSWERS,
    MSG_TZ_PRO_GENERATING_QUESTIONS,
    MSG_TZ_PRO_GENERATING_RESULT,
    MSG_TZ_PRO_INVALID_QUESTIONS,
    MSG_TZ_PRO_NO_PHOTOS,
    MSG_TZ_PRO_QUESTIONS_ERROR,
    MSG_TZ_PRO_RESULT_ERROR,
    format_pro_question,
)

logger = logging.getLogger(__name__)


def _reset_user_state(chat_id):
    user_modes[chat_id] = None
    user_data[chat_id] = {}


def _build_structured_answers(questions, raw_answers):
    structured_answers = []

    for index, answer_letter in enumerate(raw_answers):
        question_item = questions[index]
        options = question_item["options"]
        if answer_letter not in options:
            raise ValueError(f"Некорректный вариант ответа: {answer_letter}")

        structured_answers.append(
            {
                "question": question_item["question"],
                "selected_option": answer_letter,
                "selected_text": options[answer_letter],
            }
        )

    return structured_answers


def _resolve_mode(callback_data):
    if callback_data == CB_TZ_PRO_MODE_STANDARD:
        return "standard", MODE_STANDARD
    if callback_data == CB_TZ_PRO_MODE_BALANCE:
        return "balance", MODE_BALANCE
    return "creative", MODE_CREATIVE


def handle_callback_query(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    callback_data = callback["data"]
    logger.info("Handling callback for chat_id=%s data=%s", chat_id, callback_data)

    answer_callback_query(callback_id)

    if callback_data == CB_TZ_LITE:
        user_modes[chat_id] = "tz_lite_wait_photo"
        user_data[chat_id] = {}
        send_message(chat_id, MSG_TZ_LITE_ACTIVATED, reply_markup=get_tz_back_menu())
        return {"ok": True}

    if callback_data == CB_TZ_PRO:
        user_modes[chat_id] = "tz_pro_wait_photos"
        user_data[chat_id] = {"photos": []}
        send_message(chat_id, MSG_TZ_PRO_ACTIVATED, reply_markup=get_tz_pro_upload_menu())
        return {"ok": True}

    if callback_data == CB_TZ_PRO_DONE:
        photos = user_data.get(chat_id, {}).get("photos", [])
        if not photos:
            send_message(chat_id, MSG_TZ_PRO_NO_PHOTOS, reply_markup=get_tz_pro_upload_menu())
            return {"ok": True}

        send_message(chat_id, MSG_TZ_PRO_GENERATING_QUESTIONS)

        try:
            questions_result = generate_tz_pro_questions(photos)
            questions = questions_result.get("questions", [])

            if len(questions) != 6:
                send_message(chat_id, MSG_TZ_PRO_INVALID_QUESTIONS, reply_markup=get_tz_back_menu())
                return {"ok": True}

            user_modes[chat_id] = "tz_pro_questions"
            user_data[chat_id]["questions"] = questions
            user_data[chat_id]["answers"] = []
            user_data[chat_id]["current_question_index"] = 0

            send_message(
                chat_id,
                format_pro_question(questions[0], 1),
                reply_markup=get_pro_question_menu(),
            )
        except Exception as exc:
            logger.exception("TZ Pro questions generation failed for chat_id=%s", chat_id)
            send_message(
                chat_id,
                MSG_TZ_PRO_QUESTIONS_ERROR.format(error=str(exc)),
                reply_markup=get_tz_back_menu(),
            )

        return {"ok": True}

    if callback_data.startswith(CB_PRO_ANSWER_PREFIX):
        if user_modes.get(chat_id) != "tz_pro_questions":
            return {"ok": True}

        answer = callback_data.split("_")[-1]
        state = user_data.get(chat_id, {})
        state.setdefault("answers", []).append(answer)
        state["current_question_index"] = state.get("current_question_index", 0) + 1

        current_index = state["current_question_index"]
        questions = state.get("questions", [])

        if current_index < 6:
            send_message(
                chat_id,
                format_pro_question(questions[current_index], current_index + 1),
                reply_markup=get_pro_question_menu(),
            )
        else:
            user_modes[chat_id] = "tz_pro_mode_choice"
            send_message(chat_id, MSG_TZ_PRO_ALL_ANSWERS, reply_markup=get_tz_pro_mode_menu())

        return {"ok": True}

    if callback_data in [CB_TZ_PRO_MODE_STANDARD, CB_TZ_PRO_MODE_BALANCE, CB_TZ_PRO_MODE_CREATIVE]:
        if user_modes.get(chat_id) != "tz_pro_mode_choice":
            return {"ok": True}

        selected_mode, mode_prompt = _resolve_mode(callback_data)
        state = user_data.get(chat_id, {})
        state["selected_tz_mode"] = selected_mode
        send_message(chat_id, MSG_TZ_PRO_GENERATING_RESULT)

        try:
            questions = state["questions"]
            raw_answers = state["answers"]
            image_urls = state["photos"]
            structured_answers = _build_structured_answers(questions, raw_answers)

            result_text = generate_tz_pro_result(
                image_urls=image_urls,
                answers=structured_answers,
                mode=selected_mode,
                base_prompt=BASE_PROMPT_PRO,
                mode_prompt=mode_prompt,
            )

            _reset_user_state(chat_id)
            send_message(chat_id, result_text, reply_markup=get_main_menu())
        except Exception as exc:
            logger.exception("TZ Pro result generation failed for chat_id=%s", chat_id)
            send_message(
                chat_id,
                MSG_TZ_PRO_RESULT_ERROR.format(error=str(exc)),
                reply_markup=get_main_menu(),
            )

        return {"ok": True}

    if callback_data == CB_BACK_TO_TZ_CHOICE:
        _reset_user_state(chat_id)
        send_message(chat_id, MSG_TZ_CHOICE, reply_markup=get_tz_choice_menu())
        return {"ok": True}

    if callback_data == CB_BACK_TO_MAIN:
        _reset_user_state(chat_id)
        send_message(chat_id, MSG_RETURN_TO_MAIN, reply_markup=get_main_menu())
        return {"ok": True}

    return {"ok": True}
