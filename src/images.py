import os
from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

# Для инициализации теперь нужен только приватный ключ
imagekit = ImageKit(
    private_key=os.getenv("IMAGE_PRIVATE_KEY")
)

# Экспортируем URL_ENDPOINT отдельно, так как он пригодится для генерации ссылок (например, в feed)
URL_ENDPOINT = os.getenv("IMAGEKIT_URL")