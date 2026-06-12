from __future__ import annotations

from codecs import BOM_UTF8

from csv_service import CsvLoadError, EXPORT_ENCODING, MAX_FILE_SIZE, format_cell_value, load_csv_bytes


def test_load_csv_bytes_reads_utf8_sig_file() -> None:
    file_bytes = "Ville;Population\nParis;2200000\n".encode(EXPORT_ENCODING)
    dataset = load_csv_bytes(file_bytes)
    assert list(dataset.dataframe.columns) == ["Ville", "Population"]
    assert dataset.dataframe.iloc[0].to_dict() == {"Ville": "Paris", "Population": "2200000"}


def test_load_csv_bytes_reads_cp1252_file() -> None:
    file_bytes = "Région;Ville\nÎle-de-France;Paris\n".encode("cp1252")
    dataset = load_csv_bytes(file_bytes)
    assert dataset.dataframe.iloc[0].to_dict() == {"Région": "Île-de-France", "Ville": "Paris"}


def test_load_csv_bytes_rejects_large_file() -> None:
    oversized_bytes = b"A" * (MAX_FILE_SIZE + 1)
    try:
        load_csv_bytes(oversized_bytes)
    except CsvLoadError as error:
        assert "trop volumineux" in str(error)
    else:
        raise AssertionError("Un fichier hors limite devrait être refusé.")


def test_format_cell_value_removes_integer_like_decimal_suffix() -> None:
    assert format_cell_value(123.0) == "123"


def test_export_encoding_keeps_excel_friendly_bom() -> None:
    assert "Texte généré".encode(EXPORT_ENCODING).startswith(BOM_UTF8)
