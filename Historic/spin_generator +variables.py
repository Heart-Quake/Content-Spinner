import streamlit as st
import random
import re
import pandas as pd
import csv
import io

def generate_variation(text, variables):
    """Génère une variation du texte en remplaçant les spins et les variables."""
    result = text
    for var_name, var_value in variables.items():
        result = result.replace(f"{{{var_name}}}", str(var_value))
    
    def replace_spin(match):
        options = match.group(1).split('|')
        return random.choice(options)
    
    result = re.sub(r'\[(.*?)\]', replace_spin, result)
    return result

def generate_csv_download(variations):
    """Génère un fichier CSV à partir des variations."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Variation'])
    for var in variations:
        writer.writerow([var])
    return output.getvalue()

# Configuration de la page
st.set_page_config(
    page_title="Spin Generator MVP",
    page_icon="🔄",
    layout="wide"
)

# Titre principal
st.title("🔄 Générateur de Spin")

# Upload CSV pour les variables
st.subheader("1. Chargez votre fichier CSV (optionnel)")
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

# Variables dynamiques à partir du CSV
available_variables = {}
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';')  # Ajustez le séparateur selon votre CSV
    columns = df.columns.tolist()
    st.success(f"{len(columns)} colonnes trouvées dans le CSV")
    
    # Afficher les colonnes disponibles
    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à utiliser comme variables",
        columns,
        default=columns[:5] if len(columns) > 5 else columns
    )
    
    # Créer un exemple avec la première ligne
    for col in selected_columns:
        available_variables[col] = str(df[col].iloc[0])

# Zone de texte pour le spin
st.subheader("2. Entrez votre Master Spin")
spin_help = """
Variables disponibles : """ + ", ".join([f"{{{var}}}" for var in available_variables.keys()])
spin_text = st.text_area(
    "Texte avec spins",
    help=spin_help if available_variables else "Utilisez [option1|option2] pour les variations et {variable} pour les variables",
    height=200
)

# Nombre de variations
st.subheader("3. Générez vos variations")
num_variations = st.number_input("Nombre de variations souhaitées", min_value=1, max_value=100, value=10)

# Génération des variations
if st.button(f"🔄 Générer {num_variations} variations"):
    if spin_text:
        variations = []
        for _ in range(num_variations):
            variation = generate_variation(spin_text, available_variables)
            variations.append(variation)
            
        # Afficher les variations
        st.subheader("Variations générées")
        for i, var in enumerate(variations, 1):
            with st.expander(f"Variation {i}", expanded=i==1):
                st.text_area(f"Variation {i}", value=var, height=100)
        
        # Bouton de téléchargement CSV
        csv_data = generate_csv_download(variations)
        st.download_button(
            label="📥 Télécharger les variations (CSV)",
            data=csv_data,
            file_name="variations.csv",
            mime="text/csv"
        )
    else:
        st.warning("Veuillez entrer un texte avec des spins")

# Guide d'utilisation dans la sidebar
with st.sidebar:
    st.header("📖 Guide d'utilisation")
    st.markdown("""
    ### Comment utiliser l'outil

    1. **Chargez votre CSV** (optionnel)
       - Les noms des colonnes deviennent des variables

    2. **Écrivez votre Master Spin**
       - Utilisez `[option1|option2]` pour les variations
       - Utilisez `{variable}` pour les variables du CSV

    3. **Générez vos variations**
       - Choisissez le nombre
       - Téléchargez le résultat en CSV
    """)