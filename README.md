# 🚀 Générateur de Spin Content

Une application Streamlit puissante et intuitive pour générer automatiquement des variations de texte à partir de templates avec spins et variables CSV.

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)

## 📋 Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Modes de fonctionnement](#modes-de-fonctionnement)
- [Format des fichiers](#format-des-fichiers)
- [Exemples](#exemples)
- [Structure du projet](#structure-du-projet)
- [Contribution](#contribution)

## 🎯 Aperçu

Le Générateur de Spin Content est un outil professionnel conçu pour les créateurs de contenu, marketeurs et SEO specialists qui ont besoin de générer rapidement de nombreuses variations d'un même texte.

L'application propose deux modes :
- **Mode Simple** : Génération rapide avec syntaxe de spin uniquement
- **Mode Avancé** : Intégration de variables depuis un fichier CSV

## ✨ Fonctionnalités

### 🔧 Fonctionnalités principales
- **Deux modes de génération** : Simple et Avancé (CSV)
- **Syntaxe de spin intuitive** : `[option1|option2|option3]` ou `{option1|option2|option3}`
- **Spins imbriqués illimités** : `[très [bon|excellent]|fantastique]`, `{plus de {100|cent} ans|un siècle}`
- **Variables CSV dynamiques** : `{nom_colonne}`
- **Interface utilisateur moderne** avec Streamlit
- **Validation en temps réel** de la syntaxe
- **Export CSV** des variations générées
- **Prévisualisation interactive** des résultats

### 🎨 Interface utilisateur
- **Design moderne** avec logo intégré
- **Navigation par boutons** entre les modes
- **Affichage optimisé** des variables utilisées
- **Gestion d'état persistante** pendant la session
- **Animations CSS fluides**

### 🛡️ Robustesse
- **Gestion des encodages** (UTF-8, Latin1)
- **Validation des fichiers CSV**
- **Gestion d'erreurs complète**
- **Messages d'aide contextuels**

## 🚀 Installation

### Prérequis
- Python 3.11 ou supérieur
- pip (gestionnaire de packages Python)

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone <url-du-repository>
cd spin_tool
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**

**Option A : Script automatique (recommandé)**
```bash
# Sur macOS/Linux
./run.sh

# Sur Windows
run.bat
```

**Option B : Commande manuelle**
```bash
streamlit run spin_generator.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

## 💡 Utilisation

### Mode Simple

1. Sélectionnez le **Mode Simple**
2. Entrez votre texte avec la syntaxe de spin : `[option1|option2]`
3. Choisissez le nombre de variations souhaitées (1-100)
4. Cliquez sur **"🔄 Générer les variations"**
5. Prévisualisez et téléchargez les résultats

### Mode Avancé (CSV)

1. Sélectionnez le **Mode Avancé (CSV)**
2. Uploadez votre fichier CSV (séparateur point-virgule)
3. Sélectionnez les colonnes à utiliser comme variables
4. Entrez votre texte avec spins et variables : `{colonne} [option1|option2]`
5. Cliquez sur **"🔄 Générer les variations"**
6. Prévisualisez et téléchargez les résultats

## 🔄 Modes de fonctionnement

### 📝 Mode Simple
Parfait pour :
- Génération rapide de variations
- Tests de syntaxe de spin
- Projets sans données externes

**Syntaxe supportée :**
- Spins simples : `[bonjour|salut|hey]` ou `{bonjour|salut|hey}`
- Spins imbriqués illimités : `[très [bon|excellent]|fantastique]`, `{plus de {100|cent} ans|un siècle}`

### 🗃️ Mode Avancé (CSV)
Idéal pour :
- Campagnes de contenu personnalisées
- Intégration de bases de données
- Génération en masse

**Syntaxe supportée :**
- Variables CSV : `{nom_colonne}`
- Combinaison : `{ville} est une [belle|magnifique] {type_ville}`
- Spins imbriqués crochets/accolades : `{plus de {100|cent} ans|un siècle}`

## 📁 Format des fichiers

### CSV (Mode Avancé)
- **Séparateur** : Point-virgule (`;`)
- **Encodage** : UTF-8 ou Latin1 (détection automatique)
- **En-têtes** : Obligatoires (première ligne)

**Exemple :**
```csv
Département;Population;Type
Ain;650000;département
Savoie;430000;département
Haute-Savoie;810000;département
```

### Export
Les variations générées sont exportées au format CSV avec les colonnes :
- Variables utilisées (une colonne par variable)
- Texte généré

## 📚 Exemples

### Exemple Mode Simple
**Entrée :**
```
{Découvrez|Explorez|Profitez de|Faites connaissance avec} {l’univers|le monde|l’histoire|la gamme} {unique|exceptionnelle|incomparable|emblématique} de {Peugeot|la marque Peugeot|la célèbre marque Peugeot}.

Depuis {plus de {100|cent} ans|des décennies|des générations|un siècle}, {Peugeot|la maison Peugeot|cette marque iconique} {propose|offre|développe} des {véhicules|modèles|automobiles} {innovants|performants|élégants|à la pointe de la technologie}.

Parmi ses {modèles phares|véhicules emblématiques|créations iconiques}, on retrouve :
- La {Peugeot {208|308}|gamme {compacte|urbaine}} idéale pour {la ville|les trajets urbains|les citadins exigeants},
- Le SUV {3008|5008}, {parfait|idéal} pour {les familles|les aventuriers|ceux qui aiment les grands espaces},
- Les {utilitaires|véhicules professionnels} tels que le {Peugeot Partner|Expert|Boxer}, conçus pour {les professionnels|les artisans|les entreprises}.

Avec {son design soigné|son style audacieux|ses lignes dynamiques}, {Peugeot|la marque Peugeot} {séduit|attire|conquiert} {les conducteurs|les passionnés d’automobile|les automobilistes} en quête de {performance|confort|technologie avancée}.

{Choisir|Adopter|Opter pour} un véhicule Peugeot, c’est {faire confiance|s’assurer} d’un {savoir-faire reconnu|héritage automobile|engagement envers l’innovation} et d’une {qualité irréprochable|fiabilité remarquable}.

{Découvrez dès maintenant|Ne perdez plus de temps, découvrez|Faites un tour dans} l’univers Peugeot et {trouvez|sélectionnez|dénichez} {le modèle qui vous correspond|votre future voiture|l’automobile de vos rêves} !
```

**Sortie (3 variations) :**
```
Découvrez l’univers unique de Peugeot.
Depuis plus de 100 ans, Peugeot propose des véhicules innovants.
Parmi ses modèles phares, on retrouve :
- La Peugeot 208 idéale pour la ville,
- Le SUV 3008, parfait pour les familles,
- Les utilitaires tels que le Peugeot Partner, conçus pour les professionnels.
Avec son design soigné, Peugeot séduit les conducteurs en quête de performance.
Choisir un véhicule Peugeot, c’est faire confiance d’un savoir-faire reconnu et d’une qualité irréprochable.
Découvrez dès maintenant l’univers Peugeot et trouvez le modèle qui vous correspond !

Explorez le monde exceptionnel de la marque Peugeot.
Depuis un siècle, la maison Peugeot développe des modèles élégants.
Parmi ses créations iconiques, on retrouve :
- La gamme compacte idéale pour les citadins exigeants,
- Le SUV 5008, idéal pour les aventuriers,
- Les véhicules professionnels tels que le Expert, conçus pour les entreprises.
Avec ses lignes dynamiques, la marque Peugeot conquiert les passionnés d’automobile en quête de technologie avancée.
Opter pour un véhicule Peugeot, c’est s’assurer d’un engagement envers l’innovation et d’une fiabilité remarquable.
Faites un tour dans l’univers Peugeot et dénichez l’automobile de vos rêves !
```

### Exemple Mode Avancé
**CSV :**
```csv
Ville;Population;Région
Paris;2200000;Île-de-France
Lyon;520000;Auvergne-Rhône-Alpes
```

**Template :**
```
{Ville} est une [grande|importante] ville de {Population} habitants en {Région}.
```

**Sortie :**
```
Paris est une grande ville de 2200000 habitants en Île-de-France.
Lyon est une importante ville de 520000 habitants en Auvergne-Rhône-Alpes.
```

## 🏗️ Structure du projet

```
spin_tool/
├── spin_generator.py      # Application principale Streamlit
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
├── .gitignore           # Fichiers à ignorer par Git
├── run.sh               # Script de lancement (macOS/Linux)
├── run.bat              # Script de lancement (Windows)
├── exemple.csv          # Fichier CSV d'exemple
├── logo-sidebar-cream.png  # Logo Yuri & Neil optimise pour la sidebar
└── venv/               # Environnement virtuel (ignoré par Git)
```

### Fonctions principales

- `generate_variation()` : Génère une variation à partir d'un template
- `validate_spin_syntax()` : Valide la syntaxe des spins
- `validate_and_convert_csv()` : Traite et valide les fichiers CSV
- `generate_csv_download()` : Prépare l'export CSV
- `fix_encoding()` : Corrige les problèmes d'encodage

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche feature (`git checkout -b feature/amelioration`)
3. Commitez vos changements (`git commit -m 'Ajout d'une fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

### Standards de code
- Code en français (commentaires et variables)
- Style PEP 8 pour Python
- Documentation des fonctions avec docstrings
- Tests unitaires pour les nouvelles fonctionnalités

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
1. Consultez les [Issues](../../issues) existantes
2. Créez une nouvelle issue si nécessaire
3. Incluez les détails de votre environnement et les logs d'erreur

---

**Développé avec ❤️ pour la communauté du content marketing français**
