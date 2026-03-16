"""Траты по категориям"""

import functools
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Callable

import pandas as pd
from dateutil.relativedelta import relativedelta  # Умеет работать с месяцами по разному количеству дней

from src.logger.config import setup_logger

logger = setup_logger("reports")


def report_to_excel(filename_default: Optional[Union[str, Callable]] = None):
    """Декоратор для записи результата DataFrame в Excel файл."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # Извлекаем filename, чтобы он не ушел в саму функцию
            filename = kwargs.pop("filename", None)
            result = func(*args, **kwargs)

            # Если в вызове нет имени, берем то, что указано в @report_to_excel("...")
            if not filename:
                filename = filename_default if isinstance(filename_default, str) else None

            # Определяем имя файла
            if callable(filename) or filename is None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_name = f"report_{func.__name__}_{timestamp}.xlsx"
            else:
                file_name = filename

            # Поднимаемся на уровень выше от текущей папки и создаем там 'reports'
            data_dir = Path.cwd().parent / "reports"
            data_dir.mkdir(exist_ok=True)

            # Полный путь к файлу внутри папки data
            save_path = data_dir / Path(file_name)

            # Сохраняем результат
            if isinstance(result, pd.DataFrame):
                df_to_save: pd.DataFrame = result  # type: ignore
                df_to_save.to_excel(save_path, index=False, engine='openpyxl')
                logger.info(f"Отчет успешно сохранен: {save_path}")
            else:
                logger.warning("Результат функции не является DataFrame, пропуск записи.")

            return result

        return wrapper

    # Если вызвано как @report_to_excel (без скобок)
    if callable(filename_default):
        return decorator(filename_default)

    return decorator


@report_to_excel
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние три месяца от переданной даты"""

    # Создаем локальную копию, чтобы не портить исходный DataFrame
    df = transactions.copy()

    logger.info(f"Анализ трат по категории {category}")

    if date is None:
        # Фильтруем по категории
        mask = (df["Категория"] == category)
        return df.loc[mask]
    else:
        try:
            # Формируем начальную дату
            # Заменяем точки, слэши и пробелы на тире
            clean_date = re.sub(r'[./ ]', '-', date)
            start_date = datetime.strptime(clean_date, "%d-%m-%Y")

            # Приводим колонку с датами в DF к формату datetime для сравнения
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

            # Формируем конечную дату - прибавляем три месяца
            end_date = start_date + relativedelta(months=3)

            # Фильтруем: категория + интервал в 3 месяца
            mask = (df["Категория"] == category) & \
                   (df["Дата операции"] >= start_date) & \
                   (df["Дата операции"] < end_date)

            return df.loc[mask]

        except Exception as e:
            logger.error(f"Ошибка формирования данных: {e}")
            return pd.DataFrame()
