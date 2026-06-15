# Runbook, Generateur de Spin Content

## Source live

| Element | Valeur |
|---|---|
| Live URL | https://content-spinner.streamlit.app/ |
| Repository | `Heart-Quake/Content-Spinner` |
| Branche | `main` |
| Entrypoint | `spin_generator.py` |
| Build marker attendu | `Content-Spinner:<commit>` ou equivalent `data-app-build` |

## Commandes locales

```bash
cd /Users/vincentflaceliere/Github/spin_tool
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run spin_generator.py
```

Verification :

```bash
python3 -m py_compile spin_generator.py template_engine.py csv_service.py automation_seo_theme.py
python3 -m pytest tests
```

## Smoke test live

Verifier :

- `.tool-hero` present ;
- `.sidebar-logo img` present ;
- `data-app-build` present ;
- mode simple genere un aperçu ;
- mode CSV accepte `exemple.csv` ou fixture equivalente ;
- export CSV telechargeable ;
- pas de traceback.

## Erreur template

Symptomes :

- accolade non fermee ;
- option vide ;
- variable inconnue.

Actions :

- reproduire dans `template_engine.parse_template` ;
- ajouter un test dans `tests/test_template_engine.py` si le cas est recurrent ;
- ne pas masquer l'erreur dans l'UI, elle doit rester actionnable.

## CSV invalide

Symptomes :

- encodage non supporte ;
- colonnes dupliquees apres nettoyage ;
- fichier vide ;
- separateur mal detecte.

Actions :

- verifier `csv_service.detect_separator` ;
- tester avec `python3 -m pytest tests/test_csv_service.py` ;
- demander un export CSV propre en `;` si le fichier client est ambigu.

## Dette Git connue

Le repo contient historiquement un `venv/` suivi et beaucoup de fichiers modifies hors scope.

Regle :

- ne pas commit `venv/` ;
- ne pas revert les changements existants sans demande explicite ;
- pour un futur lot hygiene, retirer `venv/` de Git dans une PR dediee.
