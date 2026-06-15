# Architecture, Generateur de Spin Content

## Modules

```text
spin_generator.py
  -> UI Streamlit, modes simple/CSV/multi, exports, session_state

template_engine.py
  -> parseur recursif, AST, rendu deterministe avec Random

csv_service.py
  -> lecture CSV, detection encodage/separateur, normalisation colonnes

automation_seo_theme.py
  -> design system Automation SEO
```

## Flux mode simple

```text
template texte
  -> parse_template(allow_variables=False)
  -> rendu N fois
  -> preview limitee
  -> export CSV
```

## Flux mode CSV

```text
upload CSV
  -> load_csv_bytes
  -> selection colonnes
  -> parse_template(allow_variables=True)
  -> find_unknown_variables
  -> rendu par ligne
  -> export CSV
```

## Flux multi-champs

```text
upload CSV
  -> champs nommes en session_state
  -> import/export config JSON
  -> validation noms
  -> rendu champ par champ
  -> export tableau enrichi
```

## Tests

Les tests couvrent :

- parseur et erreurs de syntaxe ;
- variables inconnues ;
- chargement CSV ;
- detection separateur/encodage.

Commande :

```bash
python3 -m pytest tests
```

## Design system live

L'app live doit conserver :

- `apply_automation_seo_theme()` ;
- `logo-sidebar-cream.png` ;
- `.tool-hero` ;
- `data-app-build` ;
- absence de `#2BAF9C`, `DR SEO`, `Dr. SEO`, `base = "light"`.

## Points de vigilance

- Ne pas rendre le parseur dependant de Streamlit.
- Ne pas stocker les fichiers clients en dur.
- Ne pas augmenter les limites de generation sans garde memoire.
- Ne pas commit `venv/`, meme s'il existe historiquement dans le repo.
