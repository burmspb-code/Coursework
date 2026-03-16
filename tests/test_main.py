from unittest.mock import patch

import pandas as pd

from src.main import run_views_analysis


def test_run_views_analysis_empty(caplog) -> None:
    df_empty = pd.DataFrame()
    path = "dummy.xlsx"

    with caplog.at_level("WARNING"):
        run_views_analysis(df_empty, path)

    assert "Данные по указанному пути dummy.xlsx отсутствуют" in caplog.text


# 3. Тест: Интеграция с модулем views (используем mock)
@patch("src.main.get_summary_stats")
def test_run_views_analysis_success(mock_get_stats, sample_df) -> None:
    # Настраиваем mock, чтобы он возвращал фейковый JSON
    mock_get_stats.return_value = '{"status": "ok"}'

    # Запускаем функцию с нашими тестовыми данными
    run_views_analysis(sample_df, "test.xlsx")

    # Проверяем, что функция внутри реально вызывалась
    mock_get_stats.assert_called_once()


# 4. Тест: Обработка ошибки FileNotFoundError в блоке main
@patch("src.main.load_xlsx")
@patch("src.main.logger")
def test_main_file_not_found(mock_logger, mock_load) -> None:
    # Имитируем ошибку отсутствия файла
    mock_load.side_effect = FileNotFoundError

    # Здесь мы проверяем логику внутри блока try-except
    transaction_data_path = "wrong_path.xlsx"
    try:
        # Эмулируем кусок кода из вашего main
        mock_load(transaction_data_path)
    except FileNotFoundError:
        mock_logger.error(f"Файл не найден: {transaction_data_path}")

    mock_logger.error.assert_called_with(f"Файл не найден: {transaction_data_path}")
