from app.callbacks import (
    CB_BACK_TO_MAIN,
    CB_BACK_TO_TZ_CHOICE,
    CB_PRO_ANSWER_A,
    CB_PRO_ANSWER_B,
    CB_PRO_ANSWER_C,
    CB_PRO_ANSWER_D,
    CB_TZ_LITE,
    CB_TZ_PRO,
    CB_TZ_PRO_DONE,
    CB_TZ_PRO_MODE_BALANCE,
    CB_TZ_PRO_MODE_CREATIVE,
    CB_TZ_PRO_MODE_STANDARD,
)
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
            [{"text": BUTTON_TZ_LITE, "callback_data": CB_TZ_LITE}],
            [{"text": BUTTON_TZ_PRO, "callback_data": CB_TZ_PRO}],
            [{"text": BUTTON_BACK, "callback_data": CB_BACK_TO_MAIN}],
        ]
    }


def get_tz_back_menu():
    return {
        "inline_keyboard": [
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": CB_BACK_TO_TZ_CHOICE}]
        ]
    }


def get_tz_pro_upload_menu():
    return {
        "inline_keyboard": [
            [{"text": BUTTON_DONE, "callback_data": CB_TZ_PRO_DONE}],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": CB_BACK_TO_TZ_CHOICE}],
        ]
    }


def get_pro_question_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "A", "callback_data": CB_PRO_ANSWER_A},
                {"text": "B", "callback_data": CB_PRO_ANSWER_B},
                {"text": "C", "callback_data": CB_PRO_ANSWER_C},
                {"text": "D", "callback_data": CB_PRO_ANSWER_D},
            ],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": CB_BACK_TO_TZ_CHOICE}],
        ]
    }


def get_tz_pro_mode_menu():
    return {
        "inline_keyboard": [
            [
                {"text": BUTTON_STANDARD, "callback_data": CB_TZ_PRO_MODE_STANDARD},
                {"text": BUTTON_BALANCE, "callback_data": CB_TZ_PRO_MODE_BALANCE},
                {"text": BUTTON_CREATIVE, "callback_data": CB_TZ_PRO_MODE_CREATIVE},
            ],
            [{"text": BUTTON_BACK_TO_TZ, "callback_data": CB_BACK_TO_TZ_CHOICE}],
        ]
    }
