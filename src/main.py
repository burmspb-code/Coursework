from src.logger.config import setup_logger
from views import load_xlsx, get_ExchangeRate, get_stock_price, get_operations, get_summary_stats

logger = setup_logger("main")

if __name__ == '__main__':

    logger.info("Анализ статистики по категориям, получение курса валют и стоимости акций")

    # Инициализация вводных данных
    path_file = "../data/operations.xlsx" # Путь к файлу с данными
    dataframe = load_xlsx(path_file) # Загрузка данных в датафрейм
    if not dataframe.empty: # Если данные получены
        list_currency = ["USD", "EUR", "JPY", "GBP"]
        my_stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        date = "03.11.2021"
        period = "30.12.2021"

        json_data = get_summary_stats(dataframe, list_currency, my_stocks, date, period)
        print(json_data)
        logger.info("Анализ завершен")
    else:
        logger.warning(f"Данные по указанному пути {path_file} не получены")

