import streamlit as st
import random
import re
import pandas as pd
import csv
import io

# Constantes
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'csv'}  # Non utilisée car Streamlit gère déjà les extensions

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

@st.cache_data
def validate_and_convert_csv(uploaded_file):
    """Vérifie et convertit le fichier CSV avec mise en cache."""
    try:
        # Vérification de la taille du fichier
        file_size = len(uploaded_file.getvalue())
        if file_size > MAX_FILE_SIZE:
            st.error(f"Le fichier est trop volumineux. Taille maximale : {MAX_FILE_SIZE/1024/1024:.1f}MB")
            return None
            
        # Premier essai en UTF-8
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Si UTF-8 échoue, on essaie en latin1
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
        
        # Validation basique du contenu
        if df.empty:
            st.error("Le fichier CSV est vide")
            return None
            
        if len(df.columns) < 1:
            st.error("Le fichier CSV doit contenir au moins une colonne")
            return None
        
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

def validate_spin_syntax(text):
    """Valide la syntaxe des spins dans le texte."""
    if not text:
        return False, "Le texte est vide"
        
    # Vérifie l'équilibre des crochets
    if text.count('[') != text.count(']'):
        return False, "Les crochets [] ne sont pas équilibrés"
        
    # Vérifie que chaque spin a au moins une option
    spin_pattern = r'\[(.*?)\]'
    for match in re.finditer(spin_pattern, text):
        options = match.group(1).split('|')
        if not options or all(not opt.strip() for opt in options):
            return False, "Un spin ne contient aucune option valide"
            
    return True, "Syntaxe valide"

def generate_simple_variation(text):
    """Génère une variation du texte sans variables."""
    def replace_spin(match):
        options = match.group(1).split('|')
        return random.choice(options)
    
    return re.sub(r'\[(.*?)\]', replace_spin, text)

# Configuration de la page avec thème personnalisé
st.set_page_config(
    page_title="Générateur de Spin", 
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style personnalisé avec ajout du style pour les boutons de mode et les titres
st.markdown("""
    <style>
    .main > div {
        padding: 2rem 3rem;
    }
    .stRadio > div {  # Non utilisé
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
    }
    .mode-container {  # Non utilisé
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .mode-button {     # Non utilisé
        flex: 1;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        background-color: white;
        cursor: pointer;
        text-align: center;
        transition: all 0.3s ease;
    }
    .mode-button:hover {  # Non utilisé
        border-color: #2BAF9C;
        background-color: #f8f9fa;
    }
    .mode-button.selected {  # Non utilisé
        border-color: #2BAF9C;
        background-color: #e8f0fe;
    }
    .mode-title {  # Non utilisé
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .mode-description {  # Non utilisé
        font-size: 0.9rem;
        color: #666;
    }
    /* Style amélioré pour les boutons de mode */
    .stButton button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        transform: scale(1);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton button:active {
        transform: scale(0.98);
    }
    
    .stButton button[kind="primary"] {
        background-color: #2BAF9C;
        border-color: #2BAF9C;
    }
    
    .stButton button[kind="secondary"] {
        border: 1px solid #2BAF9C;
        color: #2BAF9C;
        background-color: transparent;
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: rgba(43, 175, 156, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal avec emoji corrigé
st.title("🔄 Générateur de Spin")

# Création des boutons de mode personnalisés
st.markdown("### 📋 Mode de fonctionnement")

# Initialisation du mode par défaut si non défini
if "mode" not in st.session_state:
    st.session_state.mode = "simple"

def switch_to_simple():
    st.session_state.mode = "simple"

def switch_to_advanced():
    st.session_state.mode = "advanced"

col1, col2 = st.columns(2)

with col1:
    st.button(
        "✨ Mode Simple",
        help="Générez des variations sans variables",
        on_click=switch_to_simple,
        type="primary" if st.session_state.mode == "simple" else "secondary",
        use_container_width=True
    )

with col2:
    st.button(
        "🔧 Mode Avancé (CSV)",
        help="Utilisez un fichier CSV pour les variables",
        on_click=switch_to_advanced,
        type="primary" if st.session_state.mode == "advanced" else "secondary",
        use_container_width=True
    )

# Séparateur visuel
st.markdown("---")

# Affichage du contenu en fonction du mode
if st.session_state.mode == "simple":
    # Zone de texte pour le spin avec meilleure présentation
    st.subheader("✏️ Entrez votre texte avec spins")
    spin_text = st.text_area(
        "Texte avec spins",
        height=150,
        placeholder="Exemple : [Bonjour|Salut|Hey] tout le monde ! Comment [allez-vous|vas-tu] ?",
        help="Utilisez les crochets [] pour créer des variations. Séparez les options par des |"
    )
    
    # Validation de la syntaxe du spin
    is_valid = True
    if spin_text:
        is_valid, message = validate_spin_syntax(spin_text)
        if not is_valid:
            st.warning(message)
    
    # Nombre de variations à générer (toujours visible, sans limite)
    nb_variations = st.number_input(
        "Nombre de variations à générer",
        min_value=1,
        value=10  # Valeur par défaut de 10 pour le mode simple
    )
    
    # Bouton de génération (toujours visible)
    if st.button("🔄 Générer les variations"):
        if not spin_text:
            st.warning("Veuillez entrer un texte avec spins")
        elif not is_valid:
            st.warning("Veuillez corriger la syntaxe du texte")
        else:
            variations = []
            for i in range(nb_variations):
                variation = generate_simple_variation(spin_text)
                variations.append(variation)
            
            # Affichage des variations
            st.subheader(f"Variations générées ({len(variations)})")
            for i, variation in enumerate(variations, 1):
                with st.expander(f"Variation {i}", expanded=i==1):
                    st.text_area(
                        "Texte généré",
                        value=variation,
                        height=400 if i <= 10 else 100,  # 400px ≈ 20 lignes
                        key=f"var_{i}"
                    )
            
            # Export CSV
            if variations:
                df_export = pd.DataFrame(variations, columns=['Texte généré'])
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger les variations (CSV)",
                    data=csv,
                    file_name="variations_simples.csv",
                    mime="text/csv"
                )

else:
    # Mode avancé avec CSV
    st.subheader("📁 1. Chargez votre fichier CSV")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CSV (séparateur : point-virgule)",
        type="csv",
        help="Format accepté : CSV avec séparateur point-virgule (;)"
    )

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
            
            # Validation de la syntaxe du spin
            is_valid = True
            if spin_text:
                is_valid, message = validate_spin_syntax(spin_text)
                if not is_valid:
                    st.warning(message)

            # Nombre de prévisualisations (toujours visible)
            preview_limit = st.number_input(
                "Nombre de prévisualisations souhaitées",
                min_value=1,
                value=len(df)  # Par défaut : nombre total de lignes du CSV
            )

            # Bouton de génération (toujours visible)
            if st.button("🔄 Générer les variations"):
                if not spin_text:
                    st.warning("Veuillez entrer un texte avec spins")
                elif not is_valid:
                    st.warning("Veuillez corriger la syntaxe du texte")
                else:
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
                    
                    # Sauvegarder les variations dans session_state
                    st.session_state.variations_data = variations_data
                    st.session_state.preview_limit = preview_limit

            # Affichage des variations si elles existent dans session_state
            if hasattr(st.session_state, 'variations_data') and st.session_state.variations_data:
                variations_data = st.session_state.variations_data
                current_preview_limit = getattr(st.session_state, 'preview_limit', len(variations_data))
                
                st.subheader(f"Variations générées ({len(variations_data)})")
                
                # Utilisation du preview_limit sauvegardé
                for i, var_data in enumerate(variations_data[:current_preview_limit], 1):
                    with st.expander(f"Variation {i}", expanded=i==1):
                        # Affichage des variables utilisées
                        variables_items = list(var_data['variables'].items())
                        
                        if variables_items:
                            # Initialiser l'état du toggle dans session_state
                            toggle_key = f"show_vars_{i}"
                            if toggle_key not in st.session_state:
                                st.session_state[toggle_key] = False
                            
                            # Affichage en une seule ligne avec résumé et toggle
                            if len(variables_items) > 1:
                                # Créer un résumé des variables
                                first_var = variables_items[0]
                                remaining_count = len(variables_items) - 1
                                
                                # Affichage condensé avec bouton toggle intégré
                                if st.session_state[toggle_key]:
                                    # Mode détaillé : toutes les variables avec fond coloré
                                    st.markdown("**📋 Variables utilisées :**")
                                    
                                    # Affichage en colonnes pour un meilleur layout
                                    nb_vars = len(variables_items)
                                    nb_cols = min(3, max(2, nb_vars // 2))
                                    cols = st.columns(nb_cols)
                                    
                                    for idx, (k, v) in enumerate(variables_items):
                                        with cols[idx % nb_cols]:
                                            st.markdown(f"• **{k}** : `{v}`")
                                    
                                    # Bouton masquer plus discret
                                    if st.button("🔼 Masquer", key=f"hide_vars_{i}", help="Revenir au mode résumé", use_container_width=False):
                                        st.session_state[toggle_key] = False
                                        st.rerun()
                                else:
                                    # Mode résumé : affichage compact et élégant
                                    col1, col2 = st.columns([5, 1])
                                    with col1:
                                        st.markdown(f"📋 **{first_var[0]}** : `{first_var[1]}` ・ :gray[+{remaining_count} autres variables]")
                                    with col2:
                                        if st.button("👁️ Voir", key=f"show_vars_btn_{i}", help=f"Afficher les {remaining_count} autres variables", use_container_width=True):
                                            st.session_state[toggle_key] = True
                                            st.rerun()
                            else:
                                # Si une seule variable, affichage simple et élégant
                                var = variables_items[0]
                                st.markdown(f"📋 **{var[0]}** : `{var[1]}`")
                        
                        st.text_area(
                            "Texte généré",
                            value=var_data['text'],
                            height=400 if i <= 10 else 100,  # 400px ≈ 20 lignes
                            key=f"var_text_{i}"
                        )
                
                # Export CSV
                csv_data = generate_csv_download(variations_data)
                st.download_button(
                    label=f"📥 Télécharger les {len(variations_data)} variations (CSV)",
                    data=csv_data,
                    file_name="variations_completes.csv",
                    mime="text/csv"
                )

# Guide d'utilisation amélioré dans la sidebar avec focus contextuel
with st.sidebar:
    # Ajout du logo avec le paramètre correct
    st.image("DR SEO Header.svg", use_container_width=True)
    
    st.header("📖 Guide d'utilisation")
    
    # Affichage conditionnel du guide selon le mode actif
    if st.session_state.mode == "simple":
        st.markdown("""
        ### ✨ Mode Simple
        
        1. **✏️ Écrivez votre texte**
           - Utilisez les crochets `[]` pour créer des variations
           - Séparez les options par des `|`
           - Exemple : `[Bonjour|Salut|Hey] tout le monde !`
        
        2. **🔢 Nombre de variations**
           - Choisissez entre 1 et 100 variations
           - Chaque variation sera générée aléatoirement
        
        3. **👀 Prévisualisation**
           - Visualisez chaque variation générée
           - La première variation est automatiquement dépliée
        
        4. **💾 Export**
           - Téléchargez toutes les variations en CSV
           - Format simple avec une colonne 'Texte généré'
        """)
        
        # Bouton pour voir le mode avancé
        if st.button("🔧 Voir le mode avancé", type="secondary"):
            st.session_state.mode = "advanced"
            st.rerun()
            
    else:
        st.markdown("""
        ### 🔧 Mode Avancé (CSV)
        
        1. **📁 Fichier CSV**
           - Utilisez un séparateur point-virgule (;)
           - Encodage UTF-8 ou Latin1
           - En-têtes obligatoires pour les variables
        
        2. **🔠 Variables**
           - Format : `{nom_colonne}`
           - Les noms doivent correspondre aux en-têtes
           - Exemple : `{ville}, {population} habitants`
        
        3. **✨ Spins**
           - Combinez variables et spins
           - Exemple : `[La belle|La grande] ville de {ville}`
           - Chaque ligne du CSV génère une variation
        
        4. **📊 Export**
           - CSV avec toutes les variables
           - Une colonne pour le texte généré
           - Prévisualisation limitée à 50 variations
        """)
        
        # Bouton pour voir le mode simple
        if st.button("✨ Voir le mode simple", type="secondary"):
            st.session_state.mode = "simple"
            st.rerun()
    
    # Astuces communes aux deux modes
    st.divider()
    st.markdown("""
        ### 💡 Astuces
        - Les variations sont toujours aléatoires
        - Vérifiez la syntaxe avant de générer
        - Prévisualisez avant d'exporter
    """)