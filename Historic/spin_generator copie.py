import streamlit as st
import random
import re

def generate_variation(text, variables):
    """Génère une variation du texte en remplaçant les spins et les variables."""
    # Remplacer les variables
    result = text
    for var_name, var_value in variables.items():
        result = result.replace(f"{{{var_name}}}", str(var_value))
    
    # Traiter les spins [option1|option2|option3]
    def replace_spin(match):
        options = match.group(1).split('|')
        return random.choice(options)
    
    result = re.sub(r'\[(.*?)\]', replace_spin, result)
    return result

# Configuration de la page
st.set_page_config(
    page_title="Spin Generator",
    page_icon="🔄",
    layout="wide"
)

# Titre principal
st.title("🔄 Générateur de Spin")

# Création de deux colonnes principales
col_input, col_vars = st.columns([3, 1])

with col_input:
    # Zone de texte pour le spin
    default_spin = """[Les meilleurs garages à|Trouvez un garage à|Annuaire des garages à] {ville}

[Vous recherchez|À la recherche de|Besoin de trouver] un garage [fiable|professionnel|de confiance] à {ville} ? La Centrale vous [propose|présente|offre] les [meilleurs services|meilleures prestations|meilleurs garages]."""
    
    spin_text = st.text_area(
        "Texte avec spins",
        help="Utilisez [option1|option2] pour les variations et {variable} pour les variables",
        value=default_spin,
        height=200
    )

with col_vars:
    st.subheader("Variables")
    
    # Variables par défaut
    default_vars = {
        'ville': 'Lyon',
        'Code postal': '69001',
        'Département': 'Rhône',
        'Canton': 'Lyon-1',
        'Population totale': '516092'
    }
    
    # Création des champs de variables
    variables = {}
    for var_name, default_value in default_vars.items():
        variables[var_name] = st.text_input(var_name, value=default_value)

# Boutons de génération
col_buttons = st.columns(2)

with col_buttons[0]:
    if st.button("📱 Prévisualisation", type="primary", use_container_width=True):
        st.subheader("Prévisualisation")
        preview = generate_variation(spin_text, variables)
        st.text_area("Résultat", value=preview, height=150)

with col_buttons[1]:
    num_variations = st.number_input("Nombre de variations", min_value=1, max_value=10, value=3)
    if st.button(f"🔄 Générer {num_variations} variations", type="primary", use_container_width=True):
        st.subheader("Variations générées")
        for i in range(num_variations):
            variation = generate_variation(spin_text, variables)
            with st.expander(f"Variation {i+1}", expanded=True):
                st.text_area(f"Variation {i+1}", value=variation, height=150)

# Sidebar avec aide
with st.sidebar:
    st.header("📖 Guide d'utilisation")
    st.markdown("""
    ### Comment utiliser l'outil
    
    1. **Les Spins** : 
       - Utilisez les crochets `[]`
       - Séparez les options par `|`
       - Exemple : `[bonjour|salut|hey]`
    
    2. **Les Variables** :
       - Utilisez les accolades `{}`
       - Exemple : `{ville}`
    
    3. **Génération** :
       - Prévisualisez une version
       - Ou générez plusieurs variations
    """)