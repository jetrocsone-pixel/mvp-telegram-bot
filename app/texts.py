BUTTON_REMOVE_BG = "Удалить фон"
BUTTON_CREATE_TZ = "Создать ТЗ"
BUTTON_GENERATE_COVERS = "Сгенерировать обложки"
BUTTON_HELP = "Помощь"
BUTTON_TZ_LITE = "ТЗ Lite"
BUTTON_TZ_PRO = "ТЗ Pro"
BUTTON_BACK = "Назад"
BUTTON_BACK_TO_TZ = "Назад к выбору ТЗ"
BUTTON_DONE = "Готово"
BUTTON_STANDARD = "Стандарт"
BUTTON_BALANCE = "Баланс"
BUTTON_CREATIVE = "Креатив"

MSG_WELCOME = "Добро пожаловать.\n\nВыбери нужное действие в меню ниже."
MSG_SEND_PRODUCT_PHOTO = "Отправь фото товара.\nЛучше всего отправлять как файл без сжатия."
MSG_TZ_CHOICE = "Выбери формат ТЗ:"
MSG_COVERS_STUB = "Режим генерации обложек подключим следующим этапом."
MSG_HELP = (
    "Я умею:\n"
    "1. Удалять фон у товара\n"
    "2. Готовить ТЗ для фотоворонки\n"
    "3. Генерировать обложки\n\n"
    "Сейчас полностью работает функция удаления фона."
)
MSG_CHOOSE_MENU_ACTION = "Выбери действие в меню ниже."

MSG_TZ_LITE_ACTIVATED = (
    "Режим ТЗ Lite активирован.\n\n"
    "Отправь 1 фото товара.\n"
    "Лучше всего отправлять как файл без сжатия."
)
MSG_TZ_PRO_ACTIVATED = (
    "Режим ТЗ Pro активирован.\n\n"
    "Шаг 1: отправь от 1 до 3 фото товара.\n"
    "Лучше всего отправлять как файл без сжатия.\n\n"
    "Когда закончишь загрузку, нажми «Готово»."
)
MSG_TZ_PRO_NO_PHOTOS = (
    "Ты ещё не отправил ни одного фото.\n\n"
    "Сначала отправь от 1 до 3 фото товара, потом нажми «Готово»."
)
MSG_TZ_PRO_GENERATING_QUESTIONS = (
    "Фото получены.\n\n"
    "Генерирую вопросы для ТЗ Pro. Это может занять до 20-40 секунд."
)
MSG_TZ_PRO_INVALID_QUESTIONS = "Не удалось корректно сформировать 6 вопросов. Попробуй ещё раз."
MSG_TZ_PRO_ALL_ANSWERS = "Отлично. Все ответы получены.\n\nВыбери формат ТЗ:"
MSG_TZ_PRO_GENERATING_RESULT = "Генерирую финальное ТЗ Pro. Это может занять до 30-60 секунд."
MSG_RETURN_TO_MAIN = "Возвращаю в главное меню."

MSG_TZ_PHOTO_RECEIVED = (
    "Фото для ТЗ получено.\n"
    "Следующим шагом подключим сбор описания товара и генерацию ТЗ."
)
MSG_TZ_FILE_RECEIVED = (
    "Файл изображения для ТЗ получен.\n"
    "Следующим шагом подключим сбор описания товара и генерацию ТЗ."
)
MSG_ONLY_IMAGE_FOR_TZ = "Для ТЗ нужен файл-изображение. Отправь фото товара."
MSG_ONLY_IMAGE_FOR_TZ_LITE = "Для ТЗ Lite нужен файл-изображение.\nОтправь фото товара."
MSG_ONLY_IMAGE_FOR_TZ_PRO = "Для ТЗ Pro нужен файл-изображение.\nОтправь фото товара."

MSG_TELEGRAM_PHOTO_UNAVAILABLE = "Не удалось получить фото от Telegram. Попробуй отправить его ещё раз."
MSG_FILE_PATH_UNAVAILABLE = "Не удалось получить путь к фото."
MSG_ONLY_IMAGES = "Я принимаю только изображения. Отправь фото товара как фото или как файл-изображение."

MSG_MAX_3_PHOTOS = "Можно загрузить максимум 3 фото.\n\nНажми «Готово», чтобы перейти дальше."
MSG_PHOTO_RECEIVED_TEMPLATE = "Фото {count} из 3 получено.\nМожешь отправить ещё фото или нажать «Готово»."

MSG_GENERATING_TZ_LITE = "Генерирую ТЗ Lite. Это может занять до 20-40 секунд."
MSG_GENERATING_REMOVE_BG_PHOTO = "Фото получено. Удаляю фон, это может занять до 20-40 секунд."
MSG_GENERATING_REMOVE_BG_FILE = "Файл изображения получен. Удаляю фон, это может занять до 20-40 секунд."

MSG_REMOVE_BG_ERROR = "Не удалось удалить фон.\nКод ошибки: {status_code}\nОтвет сервиса: {error_text}"
MSG_TZ_GENERATION_ERROR = "Ошибка генерации ТЗ:\n{error}"
MSG_TZ_PRO_QUESTIONS_ERROR = "Ошибка при генерации вопросов:\n{error}"
MSG_TZ_PRO_RESULT_ERROR = "Ошибка при генерации финального ТЗ Pro:\n{error}"


def format_pro_question(question_data, question_number):
    return (
        f"Вопрос {question_number} из 6\n\n"
        f"{question_data['question']}\n\n"
        f"A. {question_data['options']['A']}\n"
        f"B. {question_data['options']['B']}\n"
        f"C. {question_data['options']['C']}\n"
        f"D. {question_data['options']['D']}"
    )
