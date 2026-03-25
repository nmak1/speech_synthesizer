# src/utils/logger.py
"""
Модуль для настройки логирования
"""
import logging
import os
from datetime import datetime


def setup_logger(name: str = "VoiceSynthesizer") -> logging.Logger:
    """Настройка и возврат логгера"""
    # Создаем папку для логов
    log_dir = os.path.join(
        os.path.expanduser("~"),
        ".voicesynthesizer",
        "logs"
    )
    os.makedirs(log_dir, exist_ok=True)

    # Имя файла лога с датой
    log_file = os.path.join(
        log_dir,
        f"voicesynthesizer_{datetime.now().strftime('%Y%m%d')}.log"
    )

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Очищаем существующие хендлеры
    if logger.handlers:
        logger.handlers.clear()

    # Форматирование
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый хендлер
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "VoiceSynthesizer") -> logging.Logger:
    """Получение логгера"""
    return logging.getLogger(name)