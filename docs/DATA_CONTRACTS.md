# Contrats de donnees, Generateur de Spin Content

## Modes

L'application expose trois parcours :

- mode simple : spins sans CSV ;
- mode CSV : template avec variables de colonnes ;
- mode multi-champs : plusieurs templates nommes sur un meme CSV.

## Syntaxe spin

Les spins utilisent les accolades :

```text
{option 1|option 2}
```

Regles :

- au moins deux options ;
- aucune option vide ;
- spins imbriques autorises ;
- accolades non fermees interdites.

Le parseur est `template_engine.parse_template`.

## Variables CSV

Les variables utilisent les crochets :

```text
[Nom de colonne]
```

Regles :

- variables autorisees uniquement en mode CSV ;
- nom non vide ;
- toute variable inconnue bloque la generation via `UnknownVariableError`.

## CSV

`csv_service.load_csv_bytes` accepte :

- encodages `utf-8-sig`, `utf-8`, `cp1252`, `latin1` ;
- separateurs `;`, `,`, tabulation ;
- taille maximale `MAX_FILE_SIZE`.

Les colonnes sont normalisees :

- trim ;
- espaces multiples reduits ;
- noms non vides ;
- noms uniques apres nettoyage.

## Sorties

Exports :

- CSV avec separateur `;` ;
- encodage `utf-8-sig` ;
- toutes les generations, meme si l'aperçu UI est borne.

## Fichiers runtime interdits Git

- exports generes ;
- CSV clients ;
- `venv/` ;
- `.DS_Store` ;
- caches Python.

## Limites

- Les generations massives sont bornees par la memoire.
- Le mode simple plafonne la generation a `MAX_SIMPLE_GENERATIONS`.
- L'aperçu est volontairement limite a `MAX_PREVIEW_ROWS`.
