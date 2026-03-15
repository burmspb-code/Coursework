# json # requests # API # datetime # logging # pytest # pandas

"""Реализуйте набор функций и главную функцию, принимающую на вход строку с датой и второй необязательный параметр — диапазон данных.
По умолчанию диапазон равен одному месяцу (с начала месяца, на который выпадает дата, по саму дату).
Возможные значения второго необязательного параметра:
W
 — неделя, на которую приходится дата;
M
 — месяц, на который приходится дата;
Y
 — год, на который приходится дата;
ALL
 — все данные до указанной даты.
Возвращаемый JSON-ответ содержит следующие данные:
«Расходы»:
Общая сумма расходов.
Раздел «Основные», в котором траты по категориям отсортированы по убыванию. Данные предоставляются по 7 категориям с наибольшими тратами, траты по остальным категориям суммируются и попадают в категорию «Остальное».
Раздел «Переводы и наличные», в котором сумма по категориям «Наличные» и «Переводы» отсортирована по убыванию.
«Поступления»:
Общая сумма поступлений.
Раздел «Основные», в котором поступления по категориям отсортированы по убыванию.
Курс валют.
Стоимость акций из S&P 500.
"""
from datetime import datetime, timedelta

"""Курсовая работа для skypro"""

from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yfinance as yf
import logging

# Отключаем логирование для yfinance
yf_logger = logging.getLogger("yfinance")
yf_logger.setLevel(logging.CRITICAL)
yf_logger.addHandler(logging.NullHandler()) # Создаем пустой обработчик
yf_logger.propagate = False # Запрет распространения логов наверх


def load_xlsx(path_file: str | Path) -> pd.DataFrame:
    """Функция загрузки xlsx данных из указнанного файла"""

    try:
        if path_file:
            return pd.read_excel(path_file)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Ошибка загрузки файла: {e}")
        return pd.DataFrame()

def get_ExchangeRate(currency: str) -> dict[str, Any]:
    """Полуение курса валюты через API сайта ExchangeRate"""

    API_KEY = "05b5ef4495f3a491724965d7"
    URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{currency}"

    response = requests.get(URL)
    return response.json()

def get_stock_price(symbol: str) -> float:
    """Получение стоимости акции на текущую дату"""

    today = datetime.now().date()
    if today.weekday() == 5: # Если запрос попал на субботу
        trading_day = today - timedelta(days=1)
    elif today.weekday() == 6: # Если запрос попал на возскресенье
        trading_day = today - timedelta(days=2)
    else:
        trading_day = today

    end_day = trading_day + timedelta(days=1) # Прибавляем один день для диапазона поиска

    data = yf.download(symbol, start=trading_day, end=end_day, progress=False)

    if data.empty:
        print(f"Предупреждение: Данные для {symbol} не найдены")
        return 0.0
    try:
        price = data['Close'].iloc[0].item()
        return round(float(price), 2)
    except Exception as e:
        print(f"Ошибка обработки данных для {symbol} {e}")
        return 0.0


def get_operations(dataframe: pd.DataFrame, date: str, period: str = "M", expenditure: bool = True) -> pd.DataFrame:
    """Возвращает датафрейм из исходного за указанный период, где
      dataframe - исходный датафрейм,
      date - начальная дата для выборки,
      period - W | M | Y (неделя, месяц, год), либо конечная дата,
      expenditure - True/False (траты/попления)
      """

    # Сортируем входной датафрейм по колонке дата в порядке убывания
    dataframe = dataframe.sort_values('Дата операции', ascending=False)

    # Конвертируем входную строку даты в объект datetime
    start_date = pd.to_datetime(date, dayfirst=True)

    # Подготовка данных даты в datetime
    dataframe['Дата операции'] = pd.to_datetime(dataframe['Дата операции'], dayfirst=True)

    offset = {"W": {"weeks": 1}, "M": {"months": 1}, "Y": {"years": 1}}
    if period.upper() in offset:
        end_date = start_date + pd.DateOffset(**offset[period.upper()]) - pd.Timedelta(seconds=1)
    else:
        end_date = pd.to_datetime(period.upper(), dayfirst=True) + pd.DateOffset(days=1)

    # Заменяем запятую на точку и убираем лишние пробелы, чтобы конвертировать в float
    dataframe['Сумма платежа'] = (
        dataframe['Сумма платежа']
        .astype(str)
        .str.replace(',', '.')
        .str.replace(r'\s+', '', regex=True)  # убираем любые пробелы
        .astype(float)
    )

    # Фильтруем маску периода
    mask = (dataframe['Дата операции'] >= date) & (dataframe['Дата операции'] <= end_date)

    # Определяем логику по флагу expenditure
    if expenditure:
        expenses = dataframe.loc[mask & (dataframe['Сумма платежа'] < 0)].copy() # Формируем датафрейм с тратами
    else:
        expenses = dataframe.loc[mask & (dataframe['Сумма платежа'] > 0)].copy() # Формируем датафрейм с поступлениями

    return expenses


def get_summary_stats(dataframe: pd.DataFrame, date: str, period: str = "M") -> dict[str, Any]:
    """Принимает на вход датафрейи, дату и период,
      формат даты - dd/mm/YYYY, разделить любой,
      period - W, M, Y, либо дата
      возвращает json-ответ:
        expenses - траты по категориям,
        income - поступления,
        currency_rates - курсы валют,
        stock_prices - стоимость акций
      """
    # РАСХОДЫ

    # Формируем датафрейм за нужный период c тратами
    df_expenses_period = get_operations(dataframe, date, period)

    # Список категорий-исключений
    transfer_categories = ["Переводы", "Наличные"]

    # Фильтруем категории
    mask = (df_expenses_period["Сумма операции"] < 0) & (~df_expenses_period["Категория"].isin(transfer_categories))
    expenses_df = df_expenses_period[mask]

    # Группируем по категориям
    expenses_categories = (
            expenses_df.groupby('Категория')['Сумма операции']
            .sum()
            .abs()  # делаем суммы положительными для наглядности
            .sort_values(ascending=False)  # Сортировка по убыванию
    )

    # Формируем ТОП-7 категорий
    top_7_expenses_categories = expenses_categories.head(7)
    # Подсчитываем сумму остальных категорий
    others_sum = float(expenses_categories.iloc[7:].sum())

    # Формируем основной список
    main_expenses_list = []

    # Формируем раздел ОСНОВНЫЕ
    for cat, amn in top_7_expenses_categories.items():
        main_expenses_list.append({"category: ": cat, "amount: ": round(amn)})

    # Формируем раздел ПЕРЕВОДЫ/НАЛИЧНЫЕ
    transfers_data = (
        df_expenses_period[
            (df_expenses_period['Сумма операции'] < 0) &
            (df_expenses_period['Категория'].isin(transfer_categories))  # Берем ТОЛЬКО нужные
            ]
        .groupby('Категория')['Сумма операции']
        .sum()
        .abs()
    )
    transfer_list = []
    for cat, amn in transfers_data.items():
        transfer_list.append({"category: ": cat, "amount: ": round(amn)})

    # Формируем раздел ОСТАЛЬНОЕ
    if others_sum > 0:
        main_expenses_list.append({"category: ": "Остальное", "amount": round(others_sum)})

    # Подсчет итоговой суммы
    total_expenses_amn = round(float(abs(expenses_df['Сумма операции'].sum())))

    # ПОСТУПЛЕНИЯ

    # Формируем датафрейм за нужный период c поступлениями
    df_income_period = get_operations(dataframe, date, period, False)

    # Группируем по категориям
    income_categories = (
        df_income_period.groupby('Категория')['Сумма операции']
        .sum()
        .abs()  # делаем суммы положительными для наглядности
        .sort_values(ascending=False)  # Сортировка по убыванию
    )

    # Формируем основной список
    main_income_list = []

    # Формируем раздел ОСНОВНЫЕ
    for cat, amn in income_categories.items():
        main_income_list.append({"category: ": cat, "amount: ": round(amn)})

    # Подсчет итоговой суммы
    total_income_amn = round(float(abs(df_income_period['Сумма операции'].sum())))

    # КУРСЫ ВАЛЮТ
    base_code = "RUB" # Базовая валюта
    current_rates = get_ExchangeRate(base_code) # Загружаем курсы

    # Список валют
    list_currency = ["USD", "EUR"]

    # Формируем список курсов валют
    list_rate = []

    for item in list_currency:
        rate = current_rates["conversion_rates"].get(item)
        if rate:
            # Рассчитываем обратный курс
            price_in_rub = round(1 / rate, 2)
            list_rate.append({"currency": item, "rate": price_in_rub})



    # СТОИМОСТЬ АКЦИЙ
    my_stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "BRK.B", "JPM", "WMT"]

    # Формируем список стоимости акций
    stock_prices_list = []

    for stock in my_stocks:
        stock_prices_list.append({"stock": stock, "price": get_stock_price(stock)})



    # Сборка финальной структуры
    result = {
        "expenses": {
            "total_amount": total_expenses_amn,
            "main": main_expenses_list,
            "transfers_and_cash": transfer_list
        },
        "income": {
            "total_amount": total_income_amn,
            "main": main_income_list
        },
        "currency_rates": list_rate,
        "stock_prices": stock_prices_list
    }



    print(result)


path_file_xlsx = "../data/operations.xlsx"
df = load_xlsx(path_file_xlsx)
start_d = input("Введите начальную дату: ")
period_in = input("Введите период: ")
get_summary_stats(df, start_d, period_in)
#print(get_stock_price(["NVDA"]))
#print(get_stock_price("MSFT"))

