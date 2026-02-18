import os
import json
import functions_framework
from bot import dp, bot
from aiogram.types import Update
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Это точка входа для Google Cloud Functions
@functions_framework.http
def webhook(request):
    """
    Обрабатывает HTTP запросы от Telegram
    """
    logger.info("Получен запрос от Telegram")
    
    # Только POST запросы
    if request.method != 'POST':
        logger.warning(f"Неправильный метод: {request.method}")
        return 'OK', 200
    
    try:
        # Получаем данные от Telegram
        request_json = request.get_json()
        logger.info(f"Получен update_id: {request_json.get('update_id') if request_json else 'None'}")
        
        if not request_json:
            logger.warning("Пустой JSON")
            return 'OK', 200
        
        # Преобразуем в Update и передаем боту
        update = Update(**request_json)
        
        # Запускаем обработку асинхронно
        # Для Cloud Functions нужно создать новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dp.process_update(update))
        loop.close()
        
        logger.info("Update обработан успешно")
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Ошибка при обработке: {e}", exc_info=True)
        return 'OK', 200  # Всегда возвращаем 200, чтобы Telegram не слал повторно