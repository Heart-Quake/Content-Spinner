import streamlit as st
import random
import re
import pandas as pd
import csv
import io

def fix_encoding(text):
    """Corrige l'encodage des caractères et formate les nombres."""
    if not isinstance(text, str):
        text = str(text)
    
    # Si le texte est un nombre avec décimale .0, le convertir en entier
    try:
        # Vérifie si c'est un nombre avec décimale
        if '.' in text:
            number = float(text)
            # Si c'est un nombre entier (ex: 123.0), enlever la décimale
            if number.is_integer():
                return str(int(number))
        # Si c'est un nombre sans décimale, le retourner tel quel
        if text.isdigit():
            return text
    except ValueError:
        # Si ce n'est pas un nombre, continuer avec le traitement normal
        pass
    
    # Dictionnaire de conversion pour les caractères mal encodés
    fixes = {
        'Ã¨': 'è',
        'Ã©': 'é',
        'Ã': 'à',
        'Ã´': 'ô',
        'Ã®': 'î',
        'Ã¯': 'ï',
        'Ã¢': 'â',
        'Ã»': 'û',
        'Ã¹': 'ù',
        'Ã§': 'ç',
        'É': 'É',
        'è': 'è',
        'é': 'é',
        'à': 'à',
        'ù': 'ù',
        'â': 'â',
        'ê': 'ê',
        'î': 'î',
        'ï': 'ï',
        'ç': 'ç',
        'û': 'û',
        'ô': 'ô',
        'ö': 'ö',
        'ü': 'ü'
    }
    
    # Application des corrections
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)
    
    return text

def validate_and_convert_csv(uploaded_file):
    """Vérifie et convertit le fichier CSV."""
    try:
        # Premier essai en UTF-8
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Si UTF-8 échoue, on essaie en latin1
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
        
        # Conversion des colonnes en string et nettoyage
        for col in df.columns:
            df[col] = df[col].astype(str).apply(fix_encoding)
        
        # Correction de l'encodage des noms de colonnes
        df.columns = [fix_encoding(col) for col in df.columns]
        
        st.success(f"CSV chargé avec succès : {len(df)} lignes, {len(df.columns)} colonnes")
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la lecture du CSV : {str(e)}")
        return None

def generate_variation(text, variables):
    """Génère une variation du texte."""
    result = text
    for var_name, var_value in variables.items():
        result = result.replace(f"{{{var_name}}}", str(var_value))
    
    def replace_spin(match):
        options = match.group(1).split('|')
        return random.choice(options)
    
    result = re.sub(r'\[(.*?)\]', replace_spin, result)
    return result

def generate_csv_download(variations_data):
    """Génère le fichier CSV de sortie."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if variations_data and len(variations_data) > 0:
        headers = list(variations_data[0]['variables'].keys()) + ['Texte généré']
        writer.writerow(headers)
        for row in variations_data:
            writer.writerow(
                [row['variables'][col] for col in row['variables'].keys()] + 
                [row['text']]
            )
    return output.getvalue()

# Configuration de la page
st.set_page_config(page_title="Générateur de Spin", page_icon="🔄", layout="wide")

# Titre principal
st.title("🔄 Générateur de Spin par CSV")

# Upload CSV
st.subheader("1. Chargez votre fichier CSV")
uploaded_file = st.file_uploader("Choisissez un fichier CSV (séparateur : point-virgule)", type="csv")

if uploaded_file is not None:
    # Validation et conversion du CSV
    df = validate_and_convert_csv(uploaded_file)
    
    if df is not None:
        # Aperçu des données
        st.subheader("Aperçu des données")
        st.dataframe(df)
        
        # Sélection des colonnes
        selected_columns = st.multiselect(
            "Sélectionnez les colonnes à utiliser comme variables",
            df.columns.tolist(),
            default=df.columns.tolist()
        )
        
        # Zone de texte pour le spin
        st.subheader("2. Entrez votre Master Spin")
        spin_help = "Variables disponibles : " + ", ".join([f"{{{col}}}" for col in selected_columns])
        spin_text = st.text_area(
            "Texte avec spins",
            help=spin_help,
            height=200,
            placeholder="Exemple : Le département {Département} compte {Nombre de villes} [villes|communes] pour une population de {Population totale} habitants."
        )
        
        # Génération des variations
        if st.button("🔄 Générer les variations"):
            if spin_text:
                variations_data = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, row in df.iterrows():
                    progress = (index + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Traitement de la ligne {index + 1}/{len(df)}")
                    
                    variables = {col: str(row[col]) for col in selected_columns}
                    variation = generate_variation(spin_text, variables)
                    variations_data.append({
                        'variables': variables,
                        'text': variation
                    })
                
                progress_bar.empty()
                status_text.empty()
                
                # Affichage des variations
                st.subheader(f"Variations générées ({len(variations_data)})")
                preview_limit = st.slider(
                    "Nombre de prévisualisations",
                    min_value=1,
                    max_value=min(len(variations_data), 50),
                    value=min(10, len(variations_data))
                )
                
                for i, var_data in enumerate(variations_data[:preview_limit], 1):
                    with st.expander(f"Variation {i}", expanded=i==1):
                        st.text_area(
                            "Variables utilisées",
                            value="\n".join([f"{k} = {v}" for k,v in var_data['variables'].items()]),
                            height=100
                        )
                        st.text_area(
                            "Texte généré",
                            value=var_data['text'],
                            height=100
                        )
                
                # Export CSV
                csv_data = generate_csv_download(variations_data)
                st.download_button(
                    label=f"📥 Télécharger les {len(variations_data)} variations (CSV)",
                    data=csv_data,
                    file_name="variations_completes.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Veuillez entrer un texte avec des spins")

# Guide d'utilisation
with st.sidebar:
    st.header("📖 Guide d'utilisation")
    st.markdown("""
    ### Format du CSV
    - Séparateur : point-virgule (;)
    - Encodage : UTF-8 ou Latin1
    - En-têtes obligatoires
    
    ### Utilisation
    1. **Chargez votre CSV**
       - Le fichier sera automatiquement validé
       - Les caractères spéciaux seront corrigés
    
    2. **Sélectionnez vos colonnes**
       - Choisissez les variables à utiliser
       - Format : {nom_colonne}
    
    3. **Écrivez votre Master Spin**
       - [option1|option2] pour les variations
       - {variable} pour les données
    
    4. **Générez et exportez**
       - Prévisualisez les résultats
       - Exportez en CSV
    """)