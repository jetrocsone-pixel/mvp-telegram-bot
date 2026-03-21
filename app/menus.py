def get_main_menu():
    return {
        "keyboard": [
            [{"text": "Удалить фон"}, {"text": "Создать ТЗ"}],
            [{"text": "Сгенерировать обложки"}, {"text": "Помощь"}]
        ],
        "resize_keyboard": True
    }

def get_tz_choice_menu():
    return {
        "inline_keyboard": [
            [{"text": "ТЗ Lite", "callback_data": "tz_lite"}],
            [{"text": "ТЗ Pro", "callback_data": "tz_pro"}],
            [{"text": "Назад", "callback_data": "back_to_main"}]
        ]
    }

def get_tz_back_menu():
    return {
        "inline_keyboard": [
            [{"text": "Назад к выбору ТЗ", "callback_data": "back_to_tz_choice"}]
        ]
    }