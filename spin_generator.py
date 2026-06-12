from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import uuid

import streamlit as st

from automation_seo_theme import apply_automation_seo_theme
from csv_service import CSV_SEPARATOR, EXPORT_ENCODING, MAX_FILE_SIZE, CsvLoadError, load_csv_bytes
from template_engine import (
    TemplateDefinition,
    TemplateSyntaxError,
    UnknownVariableError,
    find_unknown_variables,
    parse_template,
)


APP_TITLE = "Générateur de Spin"
MAX_PREVIEW_ROWS = 50
MAX_SIMPLE_GENERATIONS = 10_000
DEFAULT_SIMPLE_COUNT = 10
DEFAULT_SIMPLE_PREVIEW = 10
DEFAULT_ADVANCED_PREVIEW = 10
DEFAULT_MULTI_PREVIEW = 5
SIMPLE_RESULT_KEY = "simple_result"
ADVANCED_RESULT_KEY = "advanced_result"
MULTI_RESULT_KEY = "multi_result"
MULTI_FIELD_IDS_KEY = "multi_field_ids"
MULTI_FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_automation_seo_theme()


@st.cache_data(show_spinner=False)
def load_cached_dataset(file_bytes: bytes):
    """Charge le CSV une seule fois par contenu de fichier."""
    dataset = load_csv_bytes(file_bytes)
    return dataset.dataframe, dataset.encoding


def set_mode(mode: str) -> None:
    """Bascule entre les deux parcours de génération."""
    st.session_state.mode = mode


def clear_stale_widget_state() -> None:
    """Supprime les clés internes Streamlit devenues invalides après un refactor d’UI."""
    stale_keys = [
        key
        for key in st.session_state.keys()
        if isinstance(key, str) and key.startswith("$$WIDGET_ID")
    ]
    for key in stale_keys:
        del st.session_state[key]


def hash_file_content(file_bytes: bytes) -> str:
    """Fabrique une signature stable pour invalider les résultats obsolètes."""
    return hashlib.sha1(file_bytes).hexdigest()


def build_simple_signature(template_text: str, total_count: int, preview_count: int) -> tuple[str, str, int, int]:
    """Construit la signature des paramètres du mode simple."""
    return ("simple", template_text.strip(), total_count, preview_count)


def build_advanced_signature(
    file_hash: str,
    selected_columns: list[str],
    template_text: str,
    preview_count: int,
) -> tuple[str, str, tuple[str, ...], str, int]:
    """Construit la signature des paramètres du mode CSV."""
    return ("advanced", file_hash, tuple(selected_columns), template_text.strip(), preview_count)


def build_multi_signature(
    file_hash: str,
    selected_columns: list[str],
    fields: list[dict[str, str]],
    preview_count: int,
) -> tuple:
    """Construit la signature du mode multi-champs."""
    frozen_fields = tuple((field["name"], field["text"].strip()) for field in fields)
    return ("multi", file_hash, tuple(selected_columns), frozen_fields, preview_count)


def _multi_name_key(field_id: str) -> str:
    return f"multi_name_{field_id}"


def _multi_text_key(field_id: str) -> str:
    return f"multi_text_{field_id}"


def _new_multi_field_id() -> str:
    return uuid.uuid4().hex


def ensure_multi_fields_initialized() -> None:
    """Initialise la liste des champs multi avec une première entrée vide."""
    if MULTI_FIELD_IDS_KEY not in st.session_state:
        st.session_state[MULTI_FIELD_IDS_KEY] = [_new_multi_field_id()]


def add_multi_field() -> None:
    """Ajoute un nouveau champ à générer."""
    st.session_state[MULTI_FIELD_IDS_KEY].append(_new_multi_field_id())


def remove_multi_field(field_id: str) -> None:
    """Supprime un champ et nettoie l’état des widgets associés."""
    ids = st.session_state.get(MULTI_FIELD_IDS_KEY, [])
    if len(ids) <= 1:
        return
    st.session_state[MULTI_FIELD_IDS_KEY] = [item_id for item_id in ids if item_id != field_id]
    st.session_state.pop(_multi_name_key(field_id), None)
    st.session_state.pop(_multi_text_key(field_id), None)


def collect_multi_fields() -> list[dict[str, str]]:
    """Lit les champs courants depuis session_state en préservant l’ordre d’affichage."""
    fields: list[dict[str, str]] = []
    for field_id in st.session_state.get(MULTI_FIELD_IDS_KEY, []):
        fields.append(
            {
                "id": field_id,
                "name": st.session_state.get(_multi_name_key(field_id), "").strip(),
                "text": st.session_state.get(_multi_text_key(field_id), ""),
            }
        )
    return fields


def serialize_multi_fields_config(field_ids: list[str]) -> str:
    """Sérialise les champs en dict plat {nom: template} quand les noms sont propres.

    Retombe sur le format liste [{name, text}] si un nom est vide ou dupliqué
    (typiquement pendant une édition en cours), afin de ne pas perdre de données.
    """
    pairs = [
        (
            st.session_state.get(_multi_name_key(field_id), ""),
            st.session_state.get(_multi_text_key(field_id), ""),
        )
        for field_id in field_ids
    ]
    names = [name for name, _ in pairs]
    has_empty = any(not name.strip() for name in names)
    has_duplicates = len(set(names)) != len(names)

    if has_empty or has_duplicates:
        payload = [{"name": name, "text": text} for name, text in pairs]
    else:
        payload = {name: text for name, text in pairs}

    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_multi_fields_payload(payload) -> list[tuple[str, str]]:
    """Accepte deux formats : dict plat {nom: template} ou liste [{name, text}]."""
    if isinstance(payload, dict):
        if not payload:
            raise ValueError("Le JSON est vide.")
        entries: list[tuple[str, str]] = []
        for name, text in payload.items():
            if not isinstance(text, str):
                raise ValueError(f"Champ « {name} » : la valeur doit être une chaîne de caractères.")
            entries.append((str(name), text))
        return entries

    if isinstance(payload, list):
        if not payload:
            raise ValueError("La liste de champs est vide.")
        entries = []
        for index, entry in enumerate(payload, start=1):
            if not isinstance(entry, dict) or "name" not in entry or "text" not in entry:
                raise ValueError(f"Entrée #{index} : chaque champ doit contenir les clés 'name' et 'text'.")
            entries.append((str(entry["name"]), str(entry["text"])))
        return entries

    raise ValueError("Le JSON doit être soit un objet {nom: template}, soit une liste [{name, text}].")


def load_multi_fields_from_json(raw_json: str) -> None:
    """Remplace les champs courants par ceux d’un fichier JSON importé."""
    payload = json.loads(raw_json)
    entries = parse_multi_fields_payload(payload)

    for old_id in list(st.session_state.get(MULTI_FIELD_IDS_KEY, [])):
        st.session_state.pop(_multi_name_key(old_id), None)
        st.session_state.pop(_multi_text_key(old_id), None)

    new_ids: list[str] = []
    for name, text in entries:
        field_id = _new_multi_field_id()
        new_ids.append(field_id)
        st.session_state[_multi_name_key(field_id)] = name
        st.session_state[_multi_text_key(field_id)] = text

    st.session_state[MULTI_FIELD_IDS_KEY] = new_ids


def render_styles() -> None:
    """Allège la feuille de style et supprime les sélecteurs morts."""
    st.markdown(
        """
        <style>
        .main > div {
            padding: 2rem 2.5rem 2.5rem;
        }

        .block-container {
            max-width: 1400px;
        }

        .stButton button {
            transition: all 0.2s ease;
            transform: translateY(0);
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
        }

        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
        }

        .stButton button[kind="primary"] {
            background-color: #0f766e;
            border-color: #0f766e;
        }

        .stButton button[kind="secondary"] {
            border: 1px solid #0f766e;
            color: #0f766e;
            background-color: transparent;
        }

        .stButton button[kind="secondary"]:hover {
            background-color: rgba(15, 118, 110, 0.08);
        }

        .stDownloadButton button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_result_mismatch(result_key: str, current_signature: tuple) -> None:
    """Évite d’afficher des résultats devenus faux après modification des entrées."""
    stored_result = st.session_state.get(result_key)
    if stored_result and stored_result.get("signature") != current_signature:
        st.info("Les résultats affichés ne correspondent plus aux entrées courantes. Relancez la génération.")


def inspect_template(
    template_text: str,
    *,
    allow_variables: bool,
    selected_columns: list[str] | None = None,
) -> TemplateDefinition | None:
    """Valide le template et remonte les erreurs de manière explicite."""
    stripped_text = template_text.strip()
    if not stripped_text:
        return None

    try:
        template = parse_template(stripped_text, allow_variables=allow_variables)
    except TemplateSyntaxError as error:
        st.error(str(error))
        return None

    if allow_variables:
        available_columns = selected_columns or []
        unknown_variables = find_unknown_variables(template, available_columns)
        if unknown_variables:
            missing_list = ", ".join(f"[{name}]" for name in unknown_variables)
            st.error(f"Variables introuvables dans les colonnes sélectionnées : {missing_list}")
            return None

        if template.variable_names:
            detected_list = ", ".join(f"[{name}]" for name in template.variable_names)
            st.caption(f"Variables détectées dans le template : {detected_list}")
        else:
            st.caption("Aucune variable CSV détectée. Le texte généré sera identique pour chaque ligne hors spins.")

    return template


def create_csv_buffer(headers: list[str]) -> tuple[io.StringIO, csv.writer]:
    """Prépare un export CSV compatible Excel FR (terminateur CRLF conforme RFC 4180)."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=CSV_SEPARATOR, lineterminator="\r\n")
    writer.writerow(headers)
    return buffer, writer


def finalize_csv_buffer(buffer: io.StringIO) -> bytes:
    """Encode le CSV avec BOM UTF-8 pour améliorer l’ouverture dans Excel."""
    return buffer.getvalue().encode(EXPORT_ENCODING)


def generate_simple_result(template: TemplateDefinition, total_count: int, preview_count: int) -> dict[str, object]:
    """Génère le lot simple sans stocker tout l’aperçu dans l’interface."""
    preview_rows: list[str] = []
    buffer, writer = create_csv_buffer(["Texte généré"])
    progress_bar = st.progress(0.0, text="Préparation de la génération...")
    update_every = max(1, total_count // 100)

    for index in range(total_count):
        generated_text = template.render()
        writer.writerow([generated_text])

        if index < preview_count:
            preview_rows.append(generated_text)

        processed_count = index + 1
        if processed_count == 1 or processed_count % update_every == 0 or processed_count == total_count:
            progress_bar.progress(processed_count / total_count, text=f"Génération {processed_count}/{total_count}")

    progress_bar.empty()

    return {
        "preview_rows": preview_rows,
        "download_bytes": finalize_csv_buffer(buffer),
        "total_count": total_count,
    }


def generate_advanced_result(
    template: TemplateDefinition,
    dataframe,
    selected_columns: list[str],
    preview_count: int,
) -> dict[str, object]:
    """Génère les variations CSV avec un aperçu limité pour garder l’UI fluide."""
    preview_rows: list[dict[str, object]] = []
    headers = list(selected_columns) + ["Texte généré"]
    buffer, writer = create_csv_buffer(headers)
    total_count = len(dataframe)
    progress_bar = st.progress(0.0, text="Préparation des lignes CSV...")
    update_every = max(1, total_count // 100)

    for index, row_values in enumerate(dataframe[selected_columns].itertuples(index=False, name=None), start=1):
        variables = {column: value for column, value in zip(selected_columns, row_values)}

        try:
            generated_text = template.render(variables)
        except UnknownVariableError as error:
            raise RuntimeError(str(error)) from error

        writer.writerow([variables[column] for column in selected_columns] + [generated_text])

        if len(preview_rows) < preview_count:
            preview_rows.append({"variables": variables, "text": generated_text})

        if index == 1 or index % update_every == 0 or index == total_count:
            progress_bar.progress(index / total_count, text=f"Traitement {index}/{total_count}")

    progress_bar.empty()

    return {
        "preview_rows": preview_rows,
        "download_bytes": finalize_csv_buffer(buffer),
        "total_count": total_count,
        "selected_columns": selected_columns,
    }


def render_simple_results(result: dict[str, object]) -> None:
    """Affiche uniquement un aperçu borné pour préserver la réactivité."""
    preview_rows = result["preview_rows"]
    total_count = result["total_count"]

    st.subheader(f"Variations générées ({total_count})")
    st.caption(f"Aperçu limité à {len(preview_rows)} variations pour garder l’interface rapide.")

    for index, generated_text in enumerate(preview_rows, start=1):
        with st.expander(f"Variation {index}", expanded=index == 1):
            st.text_area(
                "Texte généré",
                value=generated_text,
                height=220,
                key=f"simple_preview_{index}",
            )

    st.download_button(
        label=f"📥 Télécharger les {total_count} variations (CSV)",
        data=result["download_bytes"],
        file_name="variations_simples.csv",
        mime="text/csv",
    )


def render_advanced_results(result: dict[str, object]) -> None:
    """Affiche les lignes générées avec un résumé compact des variables."""
    preview_rows = result["preview_rows"]
    total_count = result["total_count"]

    st.subheader(f"Variations générées ({total_count})")
    st.caption(f"Aperçu limité à {len(preview_rows)} lignes sur {total_count} pour garder l’interface fluide.")

    for index, row_data in enumerate(preview_rows, start=1):
        with st.expander(f"Ligne {index}", expanded=index == 1):
            variables_summary = " · ".join(
                f"{column}: {value}" for column, value in row_data["variables"].items()
            )
            st.markdown("**Variables utilisées**")
            st.caption(variables_summary or "Aucune variable")
            st.text_area(
                "Texte généré",
                value=row_data["text"],
                height=220,
                key=f"advanced_preview_{index}",
            )

    st.download_button(
        label=f"📥 Télécharger les {total_count} variations (CSV)",
        data=result["download_bytes"],
        file_name="variations_completes.csv",
        mime="text/csv",
    )


def render_sidebar() -> None:
    """Affiche l’aide contextuelle et les garde-fous de saisie."""
    with st.sidebar:
        st.header("📖 Guide d'utilisation")

        if st.session_state.mode == "simple":
            st.markdown(
                """
                ### ✨ Mode Simple
                1. Utilisez uniquement les accolades `{...}` pour les spins
                2. Les spins imbriqués sont autorisés
                3. La prévisualisation est limitée à 50 résultats pour garder l’outil réactif
                4. L’export CSV contient l’intégralité du lot généré
                """
            )
        elif st.session_state.mode == "advanced":
            st.markdown(
                f"""
                ### 🔧 Mode Avancé (CSV)
                1. Le séparateur est auto-détecté (`;`, `,` ou tabulation — compatible Google Sheets et Excel)
                2. Les variables s’écrivent avec des crochets `[Nom de colonne]`
                3. Les spins s’écrivent avec des accolades `{{option 1|option 2}}`
                4. La taille du fichier est limitée à {MAX_FILE_SIZE / 1024 / 1024:.0f} MB
                5. La prévisualisation est limitée à 50 lignes pour garder l’interface fluide
                """
            )
        else:
            st.markdown(
                f"""
                ### 🧩 Mode Multi-champs
                1. Définissez un master spin par champ (topSeoTextTitle, topSeoText, faqQ1…)
                2. Chaque champ devient une **colonne** dans le CSV exporté
                3. Les variables `[Nom de colonne]` et les spins `{{option 1|option 2}}` fonctionnent comme en mode avancé
                4. Exportez / importez votre config en **JSON** pour la réutiliser plus tard
                5. Taille max du CSV : {MAX_FILE_SIZE / 1024 / 1024:.0f} MB
                """
            )

        st.divider()
        st.markdown(
            """
            ### 💡 Bonnes pratiques
            - Validez votre template avant de lancer un gros lot
            - Gardez des noms de colonnes clairs et stables
            - Prévisualisez quelques lignes avant de télécharger l’export complet
            """
        )


def render_simple_mode() -> None:
    """Pilote le parcours de génération sans CSV."""
    st.subheader("✏️ Entrez votre texte avec spins")
    template_text = st.text_area(
        "Texte avec spins",
        key="simple_template_text",
        height=180,
        placeholder="Exemple : {Bonjour|Salut|Hello} à tous. {Bienvenue|Ravi de vous voir} !",
        help="Utilisez uniquement les accolades { } pour définir les spins.",
    )

    template = inspect_template(template_text, allow_variables=False)

    total_count = int(
        st.number_input(
            "Nombre total de variations à générer",
            key="simple_total_count",
            min_value=1,
            max_value=MAX_SIMPLE_GENERATIONS,
            value=DEFAULT_SIMPLE_COUNT,
        )
    )
    preview_max = min(total_count, MAX_PREVIEW_ROWS)
    preview_default = min(preview_max, DEFAULT_SIMPLE_PREVIEW)
    preview_count = int(
        st.number_input(
            "Nombre de variations à prévisualiser",
            key="simple_preview_count",
            min_value=1,
            max_value=preview_max,
            value=preview_default,
        )
    )

    current_signature = build_simple_signature(template_text, total_count, preview_count)
    show_result_mismatch(SIMPLE_RESULT_KEY, current_signature)

    if st.button("🔄 Générer les variations", key="simple_generate_button", type="primary"):
        if not template_text.strip():
            st.warning("Veuillez entrer un template avec spins.")
        elif template is None:
            st.warning("Corrigez le template avant de lancer la génération.")
        else:
            generated_result = generate_simple_result(template, total_count, preview_count)
            generated_result["signature"] = current_signature
            st.session_state[SIMPLE_RESULT_KEY] = generated_result

    stored_result = st.session_state.get(SIMPLE_RESULT_KEY)
    if stored_result and stored_result.get("signature") == current_signature:
        render_simple_results(stored_result)


def render_advanced_mode() -> None:
    """Pilote le parcours de génération à partir d’un CSV."""
    st.subheader("📁 1. Chargez votre fichier CSV")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CSV (séparateur auto-détecté : ; , ou tabulation)",
        type="csv",
        key="advanced_uploaded_file",
        help="Le CSV doit contenir des en-têtes. Séparateur auto-détecté (compatible exports Google Sheets et Excel).",
    )

    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()

    try:
        dataframe, detected_encoding = load_cached_dataset(file_bytes)
    except CsvLoadError as error:
        st.error(str(error))
        return

    file_hash = hash_file_content(file_bytes)
    st.success(
        f"CSV chargé avec succès : {len(dataframe)} lignes, {len(dataframe.columns)} colonnes, encodage {detected_encoding}"
    )

    st.subheader("Aperçu des données")
    st.dataframe(dataframe.head(20), use_container_width=True, hide_index=True)
    if len(dataframe) > 20:
        st.caption("Aperçu limité aux 20 premières lignes.")

    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à utiliser comme variables",
        options=dataframe.columns.tolist(),
        default=dataframe.columns.tolist(),
        key="advanced_selected_columns",
    )

    st.subheader("✏️ 2. Entrez votre Master Spin")
    variables_help = ", ".join(f"[{column}]" for column in selected_columns) or "Aucune colonne sélectionnée"
    template_text = st.text_area(
        "Texte avec spins et variables",
        key="advanced_template_text",
        height=220,
        placeholder="Exemple : [Département] compte {de nombreuses|plusieurs} communes pour [Population] habitants.",
        help=f"Variables disponibles : {variables_help}",
    )

    preview_max = min(len(dataframe), MAX_PREVIEW_ROWS)
    preview_default = min(preview_max, DEFAULT_ADVANCED_PREVIEW)
    preview_count = int(
        st.number_input(
            "Nombre de lignes à prévisualiser",
            key="advanced_preview_count",
            min_value=1,
            max_value=preview_max,
            value=preview_default,
        )
    )

    template = inspect_template(
        template_text,
        allow_variables=True,
        selected_columns=selected_columns,
    )

    current_signature = build_advanced_signature(file_hash, selected_columns, template_text, preview_count)
    show_result_mismatch(ADVANCED_RESULT_KEY, current_signature)

    if st.button("🔄 Générer les variations", key="advanced_generate_button", type="primary"):
        if not selected_columns:
            st.warning("Sélectionnez au moins une colonne pour le mode avancé.")
        elif not template_text.strip():
            st.warning("Veuillez entrer un template avec variables et spins.")
        elif template is None:
            st.warning("Corrigez le template avant de lancer la génération.")
        else:
            try:
                generated_result = generate_advanced_result(template, dataframe, selected_columns, preview_count)
            except RuntimeError as error:
                st.error(str(error))
            else:
                generated_result["signature"] = current_signature
                st.session_state[ADVANCED_RESULT_KEY] = generated_result

    stored_result = st.session_state.get(ADVANCED_RESULT_KEY)
    if stored_result and stored_result.get("signature") == current_signature:
        render_advanced_results(stored_result)


def validate_multi_fields(
    fields: list[dict[str, str]],
    selected_columns: list[str],
    source_columns: list[str],
) -> tuple[list[tuple[str, TemplateDefinition]], list[str]]:
    """Valide chaque champ multi et collecte les erreurs remontées à l’utilisateur."""
    errors: list[str] = []
    parsed_fields: list[tuple[str, TemplateDefinition]] = []
    seen_names: set[str] = set()
    reserved_names = {column for column in source_columns}

    for index, field in enumerate(fields, start=1):
        name = field["name"].strip()
        text = field["text"].strip()
        label = name or f"champ #{index}"

        if not name:
            errors.append(f"Champ #{index} : le nom de colonne est requis.")
        elif not MULTI_FIELD_NAME_PATTERN.match(name):
            errors.append(
                f"Champ « {name} » : le nom doit commencer par une lettre et ne contenir que lettres, chiffres ou _."
            )
        elif name in reserved_names:
            errors.append(f"Champ « {name} » : le nom entre en conflit avec une colonne du CSV source.")
        elif name in seen_names:
            errors.append(f"Champ « {name} » : ce nom est utilisé par un autre champ.")
        else:
            seen_names.add(name)

        if not text:
            errors.append(f"Champ « {label} » : le master spin est vide.")
            continue

        try:
            template = parse_template(text, allow_variables=True)
        except TemplateSyntaxError as error:
            errors.append(f"Champ « {label} » : {error}")
            continue

        unknown_variables = find_unknown_variables(template, selected_columns)
        if unknown_variables:
            missing_list = ", ".join(f"[{variable}]" for variable in unknown_variables)
            errors.append(f"Champ « {label} » : variables introuvables ({missing_list}).")
            continue

        parsed_fields.append((name, template))

    return parsed_fields, errors


def generate_multi_result(
    parsed_fields: list[tuple[str, TemplateDefinition]],
    dataframe,
    selected_columns: list[str],
    preview_count: int,
) -> dict[str, object]:
    """Génère une colonne par champ en parcourant le CSV une seule fois."""
    field_names = [name for name, _ in parsed_fields]
    headers = list(selected_columns) + field_names
    preview_rows: list[dict[str, object]] = []
    buffer, writer = create_csv_buffer(headers)
    total_count = len(dataframe)
    progress_bar = st.progress(0.0, text="Préparation des lignes CSV...")
    update_every = max(1, total_count // 100)

    for index, row_values in enumerate(dataframe[selected_columns].itertuples(index=False, name=None), start=1):
        variables = {column: value for column, value in zip(selected_columns, row_values)}
        generated_texts: dict[str, str] = {}

        for name, template in parsed_fields:
            try:
                generated_texts[name] = template.render(variables)
            except UnknownVariableError as error:
                raise RuntimeError(str(error)) from error

        writer.writerow(
            [variables[column] for column in selected_columns]
            + [generated_texts[name] for name in field_names]
        )

        if len(preview_rows) < preview_count:
            preview_rows.append({"variables": variables, "texts": generated_texts})

        if index == 1 or index % update_every == 0 or index == total_count:
            progress_bar.progress(index / total_count, text=f"Traitement {index}/{total_count}")

    progress_bar.empty()

    return {
        "preview_rows": preview_rows,
        "download_bytes": finalize_csv_buffer(buffer),
        "total_count": total_count,
        "field_names": field_names,
        "selected_columns": selected_columns,
    }


def render_multi_results(result: dict[str, object]) -> None:
    """Affiche un aperçu par ligne avec un onglet par champ généré."""
    preview_rows = result["preview_rows"]
    total_count = result["total_count"]
    field_names: list[str] = result["field_names"]

    st.subheader(f"Variations générées ({total_count} lignes × {len(field_names)} champs)")
    st.caption(f"Aperçu limité à {len(preview_rows)} lignes pour garder l’interface fluide.")

    for index, row_data in enumerate(preview_rows, start=1):
        with st.expander(f"Ligne {index}", expanded=index == 1):
            variables_summary = " · ".join(
                f"{column}: {value}" for column, value in row_data["variables"].items()
            )
            st.markdown("**Variables utilisées**")
            st.caption(variables_summary or "Aucune variable")

            tabs = st.tabs(field_names)
            for tab, name in zip(tabs, field_names):
                with tab:
                    st.text_area(
                        name,
                        value=row_data["texts"].get(name, ""),
                        height=200,
                        key=f"multi_preview_{index}_{name}",
                        label_visibility="collapsed",
                    )

    st.download_button(
        label=f"📥 Télécharger les {total_count} lignes (CSV)",
        data=result["download_bytes"],
        file_name="variations_multi_champs.csv",
        mime="text/csv",
    )


def render_multi_fields_editor(selected_columns: list[str]) -> list[dict[str, str]]:
    """Affiche la liste dynamique des champs à générer."""
    st.markdown("**Champs à générer**")
    st.caption(
        "Chaque champ devient une colonne dans le CSV exporté. "
        "Le nom doit être un identifiant (lettres, chiffres, _)."
    )

    variables_hint = (
        ", ".join(f"[{column}]" for column in selected_columns)
        if selected_columns
        else "Sélectionnez au moins une colonne plus haut"
    )

    field_ids = list(st.session_state[MULTI_FIELD_IDS_KEY])
    allow_remove = len(field_ids) > 1

    for index, field_id in enumerate(field_ids, start=1):
        with st.container(border=True):
            header_cols = st.columns([4, 1])
            with header_cols[0]:
                st.text_input(
                    f"Nom du champ #{index}",
                    key=_multi_name_key(field_id),
                    placeholder="ex. topSeoTextTitle",
                )
            with header_cols[1]:
                st.button(
                    "🗑️ Supprimer",
                    key=f"multi_remove_{field_id}",
                    on_click=remove_multi_field,
                    args=(field_id,),
                    disabled=not allow_remove,
                    use_container_width=True,
                )
            st.text_area(
                f"Master spin #{index}",
                key=_multi_text_key(field_id),
                height=160,
                placeholder="Exemple : {Pourquoi choisir|Découvrez} une [Marque] neuve...",
                help=f"Variables disponibles : {variables_hint}",
            )

    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        st.button(
            "➕ Ajouter un champ",
            key="multi_add_field",
            on_click=add_multi_field,
            use_container_width=True,
        )
    with action_cols[1]:
        st.download_button(
            label="💾 Exporter la config (JSON)",
            data=serialize_multi_fields_config(field_ids).encode("utf-8"),
            file_name="multi_fields_config.json",
            mime="application/json",
            use_container_width=True,
            key="multi_export_config",
        )

    uploaded_config = st.file_uploader(
        "Importer une config JSON (remplace les champs actuels)",
        type="json",
        key="multi_import_config",
        help=(
            "Deux formats acceptés : "
            "objet plat `{\"topSeoTextTitle\": \"...\", \"topSeoText\": \"...\"}` "
            "ou liste `[{\"name\": \"...\", \"text\": \"...\"}]`."
        ),
    )
    if uploaded_config is not None:
        config_bytes = uploaded_config.getvalue()
        config_hash = hashlib.sha1(config_bytes).hexdigest()
        if st.session_state.get("multi_import_last_hash") != config_hash:
            try:
                load_multi_fields_from_json(config_bytes.decode("utf-8"))
            except (json.JSONDecodeError, ValueError) as error:
                st.error(f"Import JSON impossible : {error}")
            else:
                st.session_state["multi_import_last_hash"] = config_hash
                st.success("Config importée. Les champs ci-dessus ont été remplacés.")
                st.rerun()

    return collect_multi_fields()


def render_multi_mode() -> None:
    """Pilote le parcours multi-champs à partir d’un CSV."""
    ensure_multi_fields_initialized()

    st.subheader("📁 1. Chargez votre fichier CSV")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CSV (séparateur auto-détecté : ; , ou tabulation)",
        type="csv",
        key="multi_uploaded_file",
        help="Le CSV doit contenir des en-têtes. Séparateur auto-détecté (compatible Google Sheets et Excel).",
    )

    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()

    try:
        dataframe, detected_encoding = load_cached_dataset(file_bytes)
    except CsvLoadError as error:
        st.error(str(error))
        return

    file_hash = hash_file_content(file_bytes)
    st.success(
        f"CSV chargé : {len(dataframe)} lignes, {len(dataframe.columns)} colonnes, encodage {detected_encoding}"
    )

    st.subheader("Aperçu des données")
    st.dataframe(dataframe.head(10), use_container_width=True, hide_index=True)
    if len(dataframe) > 10:
        st.caption("Aperçu limité aux 10 premières lignes.")

    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à utiliser comme variables",
        options=dataframe.columns.tolist(),
        default=dataframe.columns.tolist(),
        key="multi_selected_columns",
    )

    st.subheader("✏️ 2. Définissez vos champs à générer")
    fields = render_multi_fields_editor(selected_columns)

    preview_max = min(len(dataframe), MAX_PREVIEW_ROWS)
    preview_default = min(preview_max, DEFAULT_MULTI_PREVIEW)
    preview_count = int(
        st.number_input(
            "Nombre de lignes à prévisualiser",
            key="multi_preview_count",
            min_value=1,
            max_value=preview_max,
            value=preview_default,
        )
    )

    current_signature = build_multi_signature(file_hash, selected_columns, fields, preview_count)
    show_result_mismatch(MULTI_RESULT_KEY, current_signature)

    if st.button("🔄 Générer les variations", key="multi_generate_button", type="primary"):
        if not selected_columns:
            st.warning("Sélectionnez au moins une colonne.")
        else:
            parsed_fields, errors = validate_multi_fields(
                fields, selected_columns, dataframe.columns.tolist()
            )
            if errors:
                for message in errors:
                    st.error(message)
            elif not parsed_fields:
                st.warning("Ajoutez au moins un champ à générer.")
            else:
                try:
                    generated_result = generate_multi_result(
                        parsed_fields, dataframe, selected_columns, preview_count
                    )
                except RuntimeError as error:
                    st.error(str(error))
                else:
                    generated_result["signature"] = current_signature
                    st.session_state[MULTI_RESULT_KEY] = generated_result

    stored_result = st.session_state.get(MULTI_RESULT_KEY)
    if stored_result and stored_result.get("signature") == current_signature:
        render_multi_results(stored_result)


def main() -> None:
    """Assemble l’interface principale."""
    clear_stale_widget_state()
    render_styles()

    if "mode" not in st.session_state:
        st.session_state.mode = "simple"

    st.title("🔄 Générateur de Spin")
    st.markdown("### 📋 Mode de fonctionnement")

    mode_col_1, mode_col_2, mode_col_3 = st.columns(3)

    with mode_col_1:
        st.button(
            "✨ Mode Simple",
            on_click=set_mode,
            args=("simple",),
            type="primary" if st.session_state.mode == "simple" else "secondary",
            use_container_width=True,
        )

    with mode_col_2:
        st.button(
            "🔧 Mode Avancé (CSV)",
            on_click=set_mode,
            args=("advanced",),
            type="primary" if st.session_state.mode == "advanced" else "secondary",
            use_container_width=True,
        )

    with mode_col_3:
        st.button(
            "🧩 Mode Multi-champs",
            on_click=set_mode,
            args=("multi",),
            type="primary" if st.session_state.mode == "multi" else "secondary",
            use_container_width=True,
        )

    st.markdown("---")

    if st.session_state.mode == "simple":
        render_simple_mode()
    elif st.session_state.mode == "advanced":
        render_advanced_mode()
    else:
        render_multi_mode()

    render_sidebar()


if __name__ == "__main__":
    main()
