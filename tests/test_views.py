from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

from src.views import get_ExchangeRate, get_operations, get_stock_price, get_summary_stats, load_xlsx


@patch("os.getenv")
@patch("requests.get")
def test_get_exchange_rate_success(mock_get, mock_getenv):
    """Тест успешного получения курса"""
    # Настраиваем моки
    mock_getenv.return_value = "fake_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"base": "USD", "rates": {"EUR": 0.92}}
    mock_get.return_value = mock_response

    result = get_ExchangeRate("USD")

    assert result["base"] == "USD"
    assert "EUR" in result["rates"]
    mock_get.assert_called_once_with("https://v6.exchangerate-api.com/v6/fake_key/latest/USD")


@patch("os.getenv")
def test_get_exchange_rate_no_api_key(mock_getenv):
    """Тест случая, когда API ключ не найден"""
    mock_getenv.return_value = None

    result = get_ExchangeRate("USD")

    assert result == {}


@patch("os.getenv")
@patch("requests.get")
def test_get_exchange_rate_error(mock_get, mock_getenv):
    """Тест обработки ошибки запроса (например, 404 или таймаут)"""
    mock_getenv.return_value = "fake_key"

    # Эмулируем исключение requests
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")

    result = get_ExchangeRate("USD")

    assert "error" in result
    assert result["error"] == "Connection error"


@patch("pandas.read_excel")
def test_load_xlsx_success(mock_read_excel):
    """Тест успешной загрузки данных из Excel"""
    # Создаем фейковый DataFrame, который якобы вернул pandas
    mock_df = pd.DataFrame({"column1": [1, 2], "column2": [3, 4]})
    mock_read_excel.return_value = mock_df

    result = load_xlsx("data/operations.xlsx")

    # Проверяем, что результат — это наш фейковый DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.shape == (2, 2)
    assert not result.empty
    mock_read_excel.assert_called_once_with("data/operations.xlsx")


def test_load_xlsx_no_path():
    """Тест случая, когда путь к файлу не передан"""
    result = load_xlsx("")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@patch("pandas.read_excel")
def test_load_xlsx_error(mock_read_excel):
    """Тест обработки исключения при чтении файла"""
    # Имитируем ошибку (например, файл не найден или формат неверный)
    mock_read_excel.side_effect = Exception("File not found")

    result = load_xlsx("invalid_path.xlsx")

    # Функция должна поймать ошибку и вернуть пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


@patch("src.views.yf.download")
@patch("src.views.datetime")
def test_get_stock_price_success(mock_datetime, mock_yf_download):
    """Тест успешного получения цены в будний день (Понедельник)"""
    # Фиксируем дату: 2023-10-23 (Понедельник)
    mock_datetime.now.return_value = datetime(2023, 10, 23)

    # Имитируем ответ от yfinance (DataFrame с колонкой Close)
    mock_df = pd.DataFrame({"Close": [150.1234]}, index=[datetime(2023, 10, 23)])
    mock_yf_download.return_value = mock_df

    result = get_stock_price("AAPL")

    assert result == 150.12
    # Проверяем, что скачивали за правильный период
    mock_yf_download.assert_called_once()
    args, kwargs = mock_yf_download.call_args
    assert kwargs["start"] == datetime(2023, 10, 23).date()


@patch("src.views.yf.download")
@patch("src.views.datetime")
def test_get_stock_price_weekend_adjustment(mock_datetime, mock_yf_download):
    """Тест корректировки даты, если сегодня Суббота"""
    # Фиксируем дату: 2023-10-21 (Суббота)
    mock_datetime.now.return_value = datetime(2023, 10, 21)

    mock_df = pd.DataFrame({"Close": [100.0]})
    mock_yf_download.return_value = mock_df

    get_stock_price("AAPL")

    # В субботу (5) trading_day должен стать пятницей (today - 1 день)
    # 2023-10-21 - 1 день = 2023-10-20
    args, kwargs = mock_yf_download.call_args
    assert kwargs["start"] == datetime(2023, 10, 20).date()


@patch("src.views.yf.download")
def test_get_stock_price_empty_data(mock_yf_download):
    """Тест случая, когда данные по символу не найдены"""
    mock_yf_download.return_value = pd.DataFrame()  # Пустой DF

    result = get_stock_price("UNKNOWN")

    assert result == 0.0


@patch("src.views.yf.download")
def test_get_stock_price_exception(mock_yf_download):
    """Тест обработки ошибки (например, нет колонки Close)"""
    mock_yf_download.return_value = pd.DataFrame({"Open": [100.0]})  # Нет Close

    result = get_stock_price("AAPL")

    assert result == 0.0


def test_get_operations_filter_month_expenses(sample_df):
    """Тест: фильтрация расходов за месяц (Январь)"""
    result = get_operations(sample_df, "01.01.2023", period="M", expenditure=True)

    assert len(result) == 2
    # Так как сортировка ascending=False, первым будет 15.01 (-2000.0)
    assert result["Сумма платежа"].iloc[0] == -2000.0
    assert result["Сумма платежа"].iloc[1] == -1000.50


def test_get_operations_filter_income(sample_df):
    """Тест: фильтрация только доходов (expenditure=False)"""
    result = get_operations(sample_df, "01.01.2023", period="M", expenditure=False)

    # 500.00 и 1500.00
    assert len(result) == 2
    assert (result["Сумма платежа"] > 0).all()
    assert 1500.00 in result["Сумма платежа"].values


def test_get_operations_custom_date_period(sample_df):
    """Тест: передача конкретной конечной даты вместо W/M/Y"""
    # Период с 01.01 по 10.01
    result = get_operations(sample_df, "01.01.2023", period="10.01.2023", expenditure=True)
    # В этом диапазоне только -1000.50 и 500.00
    # Но так как expenditure=True (по умолчанию), останется только расход
    assert len(result) == 1
    assert result["Дата операции"].iloc[0].day == 1


def test_get_operations_sorting(sample_df):
    """Тест: проверка сортировки по дате (от новых к старым)"""
    result = get_operations(sample_df, "01.01.2023", period="M", expenditure=True)

    # 15.01 должно быть выше чем 01.01
    dates = result["Дата операции"].tolist()
    assert dates[0] > dates[1]


def test_get_operations_empty_result(sample_df):
    """Тест: пустой результат, если данных нет в периоде"""
    result = get_operations(sample_df, "01.01.2020", period="M")
    assert result.empty


@patch("src.views.get_stock_price")
@patch("src.views.get_ExchangeRate")
def test_get_summary_stats_success(mock_get_rate, mock_get_stock, complex_df):
    """Проверка итогового отчета с чистыми ключами"""

    # Мокаем внешние API
    mock_get_rate.return_value = {"conversion_rates": {"USD": 0.01}}  # 1/0.01 = 100 RUB
    mock_get_stock.return_value = 150.0

    result = get_summary_stats(
        dataframe=complex_df, list_currency=["USD"], my_stocks=["AAPL"], date="01.01.2023", period="M"
    )

    # 1. Проверяем расходы (Еда 100 + Транспорт 200 + Связь 50 = 350)
    # Категория 'Переводы' (500) должна быть отдельно
    assert result["expenses"]["total_amount"] == 350
    assert result["expenses"]["main"][0]["category"] == "Транспорт"  # Сортировка по убыванию
    assert result["expenses"]["main"][0]["amount"] == 200

    assert result["expenses"]["transfers_and_cash"][0]["category"] == "Переводы"
    assert result["expenses"]["transfers_and_cash"][0]["amount"] == 500

    # 2. Проверяем доходы (Зарплата 1000 + Бонус 200 = 1200)
    assert result["income"]["total_amount"] == 1200
    assert result["income"]["main"][0]["category"] == "Зарплата"
    assert result["income"]["main"][0]["amount"] == 1000

    # 3. Проверяем валюты и акции
    assert result["currency_rates"][0]["rate"] == 100.0
    assert result["stock_prices"][0]["price"] == 150.0
