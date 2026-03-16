import os
from pathlib import Path

from src.reports import spending_by_category


def test_spending_by_category_filtering(sample_data):
    """Проверка логики фильтрации по категории и датам."""
    # Тест 1: Фильтрация только по категории (без даты)
    res = spending_by_category(sample_data, category="Продукты")
    assert len(res) == 3

    # Тест 2: Фильтрация с датой (интервал +3 месяца)
    # 01.01.2024 + 3 месяца = до 01.04.2024. Должны попасть 2 записи "Продукты"
    res_dated = spending_by_category(sample_data, category="Продукты", date="01.01.2024")
    assert len(res_dated) == 2
    assert all(res_dated["Сумма"].isin([100, 200]))


def test_decorator_saves_file(sample_data, tmp_path):
    """Проверка, что декоратор создает файл в папке reports."""
    # Переходим во временную директорию pytest, чтобы не мусорить в проекте
    os.chdir(tmp_path)

    # Вызываем функцию (декоратор сработает автоматически)
    spending_by_category(sample_data, category="Аптеки")

    # Проверяем создание папки и файла
    report_dir = Path("..") / "reports"
    assert report_dir.exists()

    files = list(report_dir.glob("report_spending_by_category_*.xlsx"))
    assert len(files) == 1


def test_decorator_custom_filename(sample_data, tmp_path):
    """Проверка сохранения с кастомным именем файла через kwargs."""
    os.chdir(tmp_path)
    custom_name = "my_custom_report.xlsx"

    spending_by_category(sample_data, category="Аптеки", filename=custom_name)

    expected_path = Path("..") / "reports" / custom_name
    assert expected_path.exists()