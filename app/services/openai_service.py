from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_tz_lite(image_url):
    prompt = """
Ты — эксперт по маркетплейсам и продающей инфографике.

На основе изображения товара создай ТЗ для дизайнера карточки товара.

Сделай ответ в структуре:

1. Что это за товар
2. Для кого он
3. Основные преимущества
4. Возможные боли клиента
5. УТП
6. Структура фотоворонки (5 слайдов)
7. Рекомендации по визуалу

Пиши чётко, конкретно, без воды.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_url}
                ]
            }
        ]
    )

    return response.output_text