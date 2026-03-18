import logging
import os
from logging import Logger

# Путь к файлу с логами
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")


def setup_logger(name: str) -> Logger:
    """Настрока логера"""

    # Создаем папку, если её еще нет
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(name)  # Создаем объект логера
    logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования

    # Предотвращаем дублирование логов
    if not logger.handlers:
        # Настраиваем file_handler
        log_file = os.path.join(LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")

        # Настраиваем file_formatter
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s")

        # Устанавливаем форматер и добавляем handler
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
