# Générateur de Spin Content

Application Streamlit pour générer des variations de texte à partir de spins imbriqués et, en mode avancé, de variables issues d’un fichier CSV.

## Points forts

- Moteur de template compilé avec validation stricte
- Support des spins imbriqués avec accolades `{option 1|option 2}`
- Variables CSV explicites avec crochets `[Nom de colonne]`
- Import CSV robuste avec UTF-8, UTF-8 BOM, CP1252 et Latin1
- Export CSV au format Excel FR : séparateur `;` et encodage `UTF-8 BOM`
- Prévisualisation plafonnée à 50 résultats pour préserver la fluidité
- Tests automatisés sur le parseur et le chargement CSV

## Stack

- Python 3.11+
- Streamlit
- Pandas

Choix de stack : Streamlit reste la solution la plus simple et la plus rapide pour conserver un outil local exploitable immédiatement, tout en fiabilisant le moteur métier côté Python.

## Structure du projet

```text
spin_tool/
├── csv_service.py
├── template_engine.py
├── spin_generator.py
├── tests/
│   ├── test_csv_service.py
│   └── test_template_engine.py
├── requirements.txt
├── requirements-dev.txt
├── run.sh
├── run.bat
├── exemple.csv
└── logo-sidebar-cream.png
```

## Installation

### macOS / Linux

1. Se placer dans le projet

```bash
cd /Users/vincentflaceliere/Github/spin_tool
```

2. Créer l’environnement virtuel

```bash
python3.11 -m venv venv
```

3. Activer l’environnement

```bash
source venv/bin/activate
```

4. Installer les dépendances d’exécution

```bash
python -m pip install -r requirements.txt
```

5. Lancer l’application

```bash
./run.sh
```

### Windows

1. Se placer dans le projet

```bat
cd \path\to\spin_tool
```

2. Créer l’environnement virtuel

```bat
py -3.11 -m venv venv
```

3. Activer l’environnement

```bat
venv\Scripts\activate
```

4. Installer les dépendances d’exécution

```bat
python -m pip install -r requirements.txt
```

5. Lancer l’application

```bat
run.bat
```

## Lancement manuel

Si tu veux bypasser les scripts :

```bash
cd /Users/vincentflaceliere/Github/spin_tool
./venv/bin/python -m streamlit run spin_generator.py --server.headless true --server.port 8501
```

L’application sera disponible sur [http://localhost:8501](http://localhost:8501).

## Utilisation

### Mode Simple

- Les spins utilisent uniquement les accolades
- Exemple :

```text
{Bonjour|Salut|Hello} {à tous|tout le monde}
```

- Le nombre total généré peut être supérieur au nombre prévisualisé
- L’export CSV contient l’intégralité du lot

### Mode Avancé (CSV)

- Le fichier CSV doit utiliser le séparateur `;`
- Les noms de colonnes sont appelés dans le template avec des crochets
- Les spins restent en accolades

Exemple de CSV :

```csv
Département;Population;Type
Ain;650000;département
Savoie;430000;département
```

Exemple de template :

```text
[Département] compte {de nombreuses|plusieurs} communes pour [Population] habitants.
```

## Tests

1. Installer les dépendances de test

```bash
cd /Users/vincentflaceliere/Github/spin_tool
./venv/bin/python -m pip install -r requirements-dev.txt
```

2. Lancer les tests

```bash
./venv/bin/python -m pytest tests -q
```

## Vérifications utiles

Compilation Python :

```bash
./venv/bin/python -m py_compile spin_generator.py template_engine.py csv_service.py
```

## Comportement fonctionnel

- Un spin doit contenir au moins deux options non vides
- Une variable manquante dans les colonnes sélectionnées bloque la génération
- Les résultats affichés sont invalidés dès que le template, le CSV ou les paramètres changent
- L’aperçu des résultats est volontairement borné pour ne pas ralentir l’interface

## Limites actuelles

- L’outil reste une application locale Streamlit, pas une application web SEO-first publique
- Les exports très massifs restent bornés par la mémoire du poste local

## Nettoyage Git recommandé

Le dépôt a historiquement suivi `venv/`. Pour remettre le repo au propre une fois pour toutes :

```bash
cd /Users/vincentflaceliere/Github/spin_tool
git rm -r --cached venv .DS_Store
```
