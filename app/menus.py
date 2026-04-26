from app.texts import (
    BUTTON_BACK,
    BUTTON_BACK_TO_TZ,
    BUTTON_BALANCE,
    BUTTON_CREATE_TZ,
    BUTTON_CREATIVE,
    BUTTON_DONE,
    BUTTON_GENERATE_COVERS,
    BUTTON_HELP,
    BUTTON_REMOVE_BG,
    BUTTON_STANDARD,
    BUTTON_TZ_LITE,
    BUTTON_TZ_PRO,
)


def get_main_menu():
    return {
        "keyboard": [
            [{"text": BUTTON_REMOVE_BG}, {"text": BUTTON_CREATE_TZ}],
            [{"text": BUTTON_GENERATE_COVERS}, {"text": BUTTON_HELP}],
        ],
        "resize_keyboard": True,
    }


def get_tz_choice_menu():
    return {
        "inline_keyboard": [
            [{"text": BUTTON_TZ_LITE, "callback_data": "tz_lite"}],
            [{"text": BUTTON_TZ_PRO, "callback_data": "tz_pro"}],
            [{"text": BUTTON_BACK, "callback_data": "back_to_main"}],
        ]
    }


def get_tz_back_menu():
    return {
        "inline_keyboard": [
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": "back_to_tz_choice"}]
        ]
    }


def get_tz_pro_upload_menu():
    return {
        "inline_keyboard": [
            [{"text": BUTTON_DONE, "callback_data": "tz_pro_done"}],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": "back_to_tz_choice"}],
        ]
    }


def get_pro_question_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "A", "callback_data": "pro_answer_A"},
                {"text": "B", "callback_data": "pro_answer_B"},
                {"text": "C", "callback_data": "pro_answer_C"},
                {"text": "D", "callback_data": "pro_answer_D"},
            ],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": "back_to_tz_choice"}],
        ]
    }


def get_tz_pro_mode_menu():
    return {
        "inline_keyboard": [
            [
                {"text": BUTTON_STANDARD, "callback_data": "tz_pro_mode_standard"},
                {"text": BUTTON_BALANCE, "callback_data": "tz_pro_mode_balance"},
                {"text": BUTTON_CREATIVE, "callback_data": "tz_pro_mode_creative"},
            ],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": "back_to_tz_choice"}],
        ]
    }
