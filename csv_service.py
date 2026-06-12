from __future__ import annotations

import csv
import io
from dataclasses import dataclass

import pandas as pd


MAX_FILE_SIZE = 10 * 1024 * 1024
CSV_SEPARATOR = ";"
SUPPORTED_SEPARATORS = (";", ",", "\t")
EXPORT_ENCODING = "utf-8-sig"
SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin1")


class CsvLoadError(ValueError):
    """Erreur métier remontée lorsqu’un CSV n’est pas exploitable."""


@dataclass(frozen=True)
class CsvDataset:
    """Contient le DataFrame prêt à l’emploi et l’encodage détecté."""

    dataframe: pd.DataFrame
    encoding: str


def load_csv_bytes(file_bytes: bytes) -> CsvDataset:
    """Charge et normalise un CSV à partir de son contenu brut."""
    if not file_bytes:
        raise CsvLoadError("Le fichier CSV est vide.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise CsvLoadError(f"Le fichier est trop volumineux. Taille maximale : {MAX_FILE_SIZE / 1024 / 1024:.1f} MB")

    detected_encoding: str | None = None
    dataframe: pd.DataFrame | None = None
    last_error: Exception | None = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            decoded_text = file_bytes.decode(encoding)
        except UnicodeDecodeError as error:
            last_error = error
            continue

        separator = detect_separator(decoded_text)

        try:
            dataframe = pd.read_csv(
                io.StringIO(decoded_text),
                sep=separator,
                keep_default_na=False,
            )
        except pd.errors.ParserError as error:
            raise CsvLoadError(
                f"Le fichier CSV est invalide (séparateur détecté : '{separator}')."
            ) from error

        detected_encoding = encoding
        break

    if dataframe is None or detected_encoding is None:
        raise CsvLoadError("Impossible de lire le fichier CSV avec les encodages pris en charge.") from last_error

    normalized_dataframe = normalize_dataframe(dataframe)

    if normalized_dataframe.empty:
        raise CsvLoadError("Le fichier CSV ne contient aucune ligne exploitable.")

    return CsvDataset(dataframe=normalized_dataframe, encoding=detected_encoding)


def detect_separator(sample_text: str) -> str:
    """Détecte le séparateur en comparant la cohérence des colonnes sur les premières lignes."""
    sample_lines = [line for line in sample_text.splitlines() if line.strip()][:20]
    if not sample_lines:
        return CSV_SEPARATOR

    best_separator = CSV_SEPARATOR
    best_score = -1

    for candidate in SUPPORTED_SEPARATORS:
        try:
            reader = csv.reader(io.StringIO("\n".join(sample_lines)), delimiter=candidate)
            column_counts = [len(row) for row in reader]
        except csv.Error:
            continue

        if not column_counts or column_counts[0] < 2:
            continue

        consistent_rows = sum(1 for count in column_counts if count == column_counts[0])
        score = column_counts[0] * 100 + consistent_rows
        if score > best_score:
            best_score = score
            best_separator = candidate

    return best_separator


def normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les en-têtes et homogénéise les valeurs en chaînes."""
    if len(dataframe.columns) < 1:
        raise CsvLoadError("Le fichier CSV doit contenir au moins une colonne.")

    normalized_headers = [normalize_header_name(str(column)) for column in dataframe.columns]
    if any(not header for header in normalized_headers):
        raise CsvLoadError("Chaque colonne du CSV doit avoir un nom non vide.")

    if len(set(normalized_headers)) != len(normalized_headers):
        raise CsvLoadError("Les noms de colonnes doivent être uniques après nettoyage.")

    cleaned_dataframe = dataframe.copy()
    cleaned_dataframe.columns = normalized_headers

    for column in cleaned_dataframe.columns:
        cleaned_dataframe[column] = cleaned_dataframe[column].map(format_cell_value)

    return cleaned_dataframe


def normalize_header_name(header_name: str) -> str:
    """Supprime les espaces parasites dans les noms de colonnes."""
    return " ".join(header_name.strip().split())


def format_cell_value(value) -> str:
    """Formate les cellules pour éviter les suffixes .0 et les NaN visibles."""
    if pd.isna(value):
        return ""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)
