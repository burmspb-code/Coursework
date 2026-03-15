"""Выгодные категории повышенного кешбэка"""

import json
import logging
from datetime import datetime, timedelta

import pandas as pd

from src.logger.config import setup_logger
from src.views import get_operations

logger = setup_logger("services")


def analyze_cashback_profit(dataframe: pd.DataFrame, year: str, month: str) -> str:
    """Анализ категории КЭШБЭК, где
    dataframe - данные с транзакциями в формате pd.DataFrame,
    year - год, за который проводится анализ,
    month - месяц, за который проводится анализ.
    """
    logger.info("Анализ категорий кэшбэк")

    try:
        # Формируем начальную дату - первый день месяца нужного года
        start_date_cash = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").strftime("%d/%m/%Y")

        # Формируем конечную дату - последний день месяца нужного года
        # Находим первый день следующего месяца
        if int(month) == 12:
            next_month = datetime(int(year) + 1, month=1, day=1)
        else:
            next_month = datetime(int(year), int(month) + 1, 1)

        # Вычитаем один день, чтобы получить последний день текущего месяца
        last_day_obj = next_month - timedelta(days=1)

        end_date_cash = last_day_obj.strftime("%d/%m/%Y")  # Переводим в строку

    except (ValueError, TypeError) as e:
        logger.error(f"Ошибка при формировании дат: {e}")
        return json.dumps({}, ensure_ascii=False)

    dataframe_for_period = get_operations(dataframe, start_date_cash,
                                          end_date_cash)  # Получение данных за нужный период

    try:
        if dataframe.empty:
            return json.dumps({}, ensure_ascii=False)

        # Фильтруем по кешбэку
        cashback_df = dataframe_for_period[(dataframe_for_period["Кэшбэк"].notna())]

        # Группируем по категориям
        cashback_categories = (
            cashback_df.groupby("Категория")["Бонусы (включая кэшбэк)"]
            .sum()
            .sort_index()  # По алфавиту
        )

        # Превращаем результат группировки в словарь Python
        cashback_dict = cashback_categories.to_dict()

        # Превращаем словарь в JSON-строку
        json_data = json.dumps(
            cashback_dict,
            ensure_ascii=False,  # Для русского текста
            indent=4  # Для отступов
        )
        return json_data

    except Exception as e:
        logging.error(f"Ошибка обработки данных {e}")
        return json.dumps({}, ensure_ascii=False)
