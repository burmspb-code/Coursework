from pathlib import Path

import pandas as pd

from src.logger.config import setup_logger
from src.reports import spending_by_category
from src.services import analyze_cashback_profit
from src.views import get_summary_stats, load_xlsx

logger = setup_logger("main")


def run_views_analysis(df: pd.DataFrame, path_file: str | Path) -> None:
    """Проверка работы модуля views"""
    logger.info("Анализ статистики по категориям, получение курса валют и стоимости акций")
    if not df.empty:  # Если данные получены
        list_currency = ["USD", "EUR", "JPY", "GBP"]  # Список с валютами
        my_stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]  # Список с акциями
        date = "03.11.2021"
        period = "30.12.2021"
        json_data = get_summary_stats(df, list_currency, my_stocks, date, period)
        print(json_data)
        logger.info("Анализ завершен")
    else:
        logger.warning(f"Данные по указанному пути {path_file} отсутствуют")


def run_services_analysis(df: pd.DataFrame, path_file: str | Path) -> None:
    """Проверка работы модуля services"""
    logger.info("Анализ категории КЕШБЭК")
    if not df.empty:  # Если данные получены
        year = "2018"
        month = "10"
        json_data = analyze_cashback_profit(df, year, month)
        print(json_data)
        logger.info("Анализ завершен")
    else:
        logger.warning(f"Данные по указанному пути {path_file} отсутствуют")


def run_reports_analysis(df: pd.DataFrame, path_file: str | Path) -> None:
    """Проверка работы модуля reports"""
    logger.info("Анализ трат по категориям")
    if not df.empty:  # Если данные получены
        date = "01.01.2020"
        category = "Ж/д билеты"
        df_data = spending_by_category(df, category, date)
        print(df_data)
        logger.info("Анализ завершен")
    else:
        logger.warning(f"Данные по указанному пути {path_file} отсутствуют")


def run_reports_analysis_to_file(df: pd.DataFrame, path_file: str | Path) -> None:
    """Проверка работы декаратора для записи в файл"""
    logger.info("Анализ трат по категориям, запись в файл")
    if not df.empty:  # Если данные получены
        date = "01.01.2020"
        # Сохраняем с заданным именем файла
        spending_by_category(df, category="Аптеки", date=date, filename="pharmacies_report.xlsx")
        # Сохраняем с именем файла по умолчанию
        spending_by_category(df, category="Аптеки", date=date)
        logger.info("Анализ завершен")
    else:
        logger.warning(f"Данные по указанному пути {path_file} отсутствуют")


if __name__ == "__main__":

    # Загрузка данных с транзакциями
    transaction_data_path = "../data/operations.xlsx"  # Путь к файлу с данными
    try:
        dataframe = load_xlsx(transaction_data_path)
    except FileNotFoundError:
        logger.error(f"Файл не найден: {transaction_data_path}")
        dataframe = pd.DataFrame()

    # Проверка работы модуля views
    run_views_analysis(dataframe, transaction_data_path)

    # Проверка работы модуля services
    run_services_analysis(dataframe, transaction_data_path)

    # Проверка работы модуля reports
    run_reports_analysis(dataframe, transaction_data_path)

    # Проверка записи в файл для модуля reports
    run_reports_analysis_to_file(dataframe, transaction_data_path)
