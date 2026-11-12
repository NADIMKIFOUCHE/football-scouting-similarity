# Similarité de joueurs : un outil d'aide au recrutement

> Projet en cours. Les résultats et l'application seront ajoutés au fil des étapes.

## Le problème

Une cellule de recrutement cherche souvent un joueur « dans le profil de » : un remplaçant à un titulaire qui part, ou une alternative moins chère à une cible trop coûteuse. Cet outil décrit chaque joueur par ses statistiques et retrouve les profils les plus proches d'un joueur donné, à poste équivalent.

## Les données

[StatsBomb Open Data](https://github.com/statsbomb/open-data) : données d'événements de vrais matchs (passes, tirs, duels, pressions, avec leurs coordonnées), publiées gratuitement par StatsBomb et récupérées avec `statsbombpy`.

## La démarche

1. **Récupération** des événements des matchs d'une compétition.
2. **Agrégation par joueur**, ramenée à 90 minutes jouées, avec un temps de jeu minimum pour écarter les échantillons trop petits.
3. **Choix des statistiques par poste** : on ne juge pas un latéral et un avant-centre sur les mêmes critères.
4. **Similarité** : normalisation des statistiques, puis recherche des plus proches voisins (scikit-learn).
5. **Visualisation** : radars de comparaison et cartes d'actions sur terrain (mplsoccer).
6. **Application** Streamlit : on choisit un joueur et on obtient ses profils les plus proches.

## Résultats

À venir.

## Lancer le projet

Avec Docker :

```bash
docker build -t football .
docker run --rm -it -v "$PWD":/app -p 8501:8501 football
```

## Outils

Python, pandas, scikit-learn, statsbombpy, mplsoccer, Streamlit, Docker.

---

Données : StatsBomb Open Data.
