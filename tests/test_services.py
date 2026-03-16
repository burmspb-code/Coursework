import json

import pandas as pd

from src.services import analyze_cashback_profit


def test_analyze_cashback_profit_success(sample_df_services):  # Имя совпадает с фикстурой
    result_json = analyze_cashback_profit(sample_df_services, "2024", "03")
    result = json.loads(result_json)

    assert result["Аптеки"] == 50
    assert result["Супермаркеты"] == 100
    assert len(result) == 2


def test_analyze_cashback_empty_df():
    # Создаем пустой DF со всеми нужными колонками
    empty_df = pd.DataFrame(
        columns=["Дата операции", "Категория", "Кэшбэк", "Бонусы (включая кэшбэк)", "Сумма платежа"]
    )
    result = analyze_cashback_profit(empty_df, "2024", "03")
    assert result == "{}"


def test_analyze_cashback_invalid_date(sample_df_services):
    # Передаем некорректный месяц
    result = analyze_cashback_profit(sample_df_services, "2024", "13")
    assert result == "{}"


def test_analyze_cashback_december_transition():
    # Готовим данные именно за ДЕКАБРЬ 2023
    data = {
        "Дата операции": ["15/12/2023", "20/12/2023"],
        "Категория": ["Супермаркеты", "Аптеки"],
        "Кэшбэк": [100, 50],
        "Бонусы (включая кэшбэк)": [100, 50],
        "Сумма платежа": [1000, 500],
    }
    df = pd.DataFrame(data)

    # Вызываем функцию
    result_json = analyze_cashback_profit(df, "2023", "12")

    # Десериализуем JSON в словарь для проверки
    result_dict = json.loads(result_json)

    # Проверяем содержимое
    assert "Супермаркеты" in result_dict
    assert result_dict["Супермаркеты"] == 100
    assert result_dict["Аптеки"] == 50
