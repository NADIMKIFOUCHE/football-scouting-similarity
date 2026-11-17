# Défenseur relanceur : trouver les centraux qui défendent et relancent

<!-- VIDÉO DE DÉMO : sur github.com, ouvrir README.md, crayon "Edit", glisser la vidéo à la place de ce commentaire. -->

Un outil d'aide au recrutement qui classe les défenseurs centraux de Ligue 1 2015/2016 selon une question simple : **qui sait à la fois défendre et relancer proprement ?**

## L'application

Une application Streamlit : on cherche un joueur, on voit son résumé (scores, rang, notes de pied) et son graphique en percentiles sur les 8 critères. Un bouton ouvre le classement complet.

## Le problème

Un défenseur central moderne doit gagner ses duels **et** sortir le ballon proprement sous la pression. Les classements habituels jugent l'un ou l'autre, et les statistiques de passe favorisent les centraux des équipes qui ont le ballon : un central du PSG fait deux fois plus de passes qu'un central de Troyes, sans forcément mieux relancer.

Les critères ont été pensés avec un regard d'ancien joueur : ce qui compte pour un central, c'est la passe réussie quand on est pressé près de son but, la passe qui fait avancer le jeu, et les duels gagnés.

## Les données

[StatsBomb Open Data](https://github.com/statsbomb/open-data), récupérées avec `statsbombpy` : Ligue 1 2015/2016, 377 matchs, 1,36 million d'événements (passes, duels, conduites… avec leurs coordonnées). On garde les **64 défenseurs centraux** ayant joué au moins 900 minutes à ce poste.

## La démarche

1. **Temps de jeu au poste.** Les compositions d'équipe donnent les minutes passées à chaque poste. Tout est ramené à 90 minutes jouées en défense centrale.
2. **Huit critères, en deux familles.**
   - *Avec ballon* : passes réussies, passes sous danger (sous pression, ou à moins de 18 m de son but), passes à plus-value (au moins 9 m gagnés vers l'avant, ou changement de jeu), passes longues (plus de 27 m vers l'avant), conduites progressives face aux pertes de balle.
   - *Défense* : duels au sol, duels aériens, interceptions.
3. **Des ratios plutôt que des volumes pour les passes.** Le nombre de passes par 90 minutes est corrélé à 0,93 avec la possession de l'équipe : il mesure l'équipe, pas le joueur. On juge donc la réussite, pas la quantité.
4. **Des notes lissées.** Chaque taux de réussite reçoit 10 tentatives fictives au taux moyen (moyenne bayésienne), pour qu'un joueur avec peu de tentatives ne soit pas noté sur un coup de chance. En défense, où le volume ne dépend pas de la possession (corrélation proche de 0), tenter beaucoup donne un léger bonus.
5. **Des percentiles** entre les 64 centraux : 80 = meilleur que 80 % d'entre eux.
6. **Trois scores.**
   - *Relance* : moyenne des percentiles en passes réussies, sous danger et à plus-value.
   - *Défense* : moyenne des percentiles en duels au sol, duels aériens et interceptions.
   - *Défenseur relanceur* : moyenne harmonique des deux, comme le F1-score. Elle reste basse si l'un des deux est faible. Les deux qualités sont presque indépendantes (corrélation de 0,19), d'où l'intérêt de les exiger ensemble.
7. **Pied faible.** Une note par pied, qui combine la réussite (lissée) et l'utilisation du pied.

## Résultats

| Rang | Joueur | Équipe | Relance | Défense | Défenseur relanceur |
|---|---|---|---|---|---|
| 1 | David Luiz | Paris Saint-Germain | 97 | 74 | **84** |
| 2 | Samuel Umtiti | Lyon | 81 | 79 | **80** |
| 3 | Thiago Silva | Paris Saint-Germain | 100 | 65 | **79** |
| 4 | Jérémy Sorbon | Guingamp | 77 | 81 | **79** |
| 5 | Marko Baša | Lille | 87 | 70 | **78** |

- **Umtiti**, le profil le plus équilibré, termine 2e. Le FC Barcelone l'a recruté à l'été 2016.
- **Thiago Silva** est le meilleur relanceur des 64, mais seulement 65 en défense : il est 3e.
- **Matthieu Saunier** (Troyes) a un vrai profil de jeu long (29 % de passes longues, 70 % de réussite), mais un 3e percentile dans les duels aériens le fait reculer à 67.

## Limites

- **Pas de position des adversaires.** StatsBomb ne fournit pas les données « 360 » pour cette saison : on ne peut pas savoir si une passe a cassé une ligne. Le gain de terrain sert d'approximation.
- **La pression est sous-estimée.** StatsBomb ne marque une passe « sous pression » que si un adversaire presse activement le porteur. D'où le critère de zone (moins de 18 m de son but) pour les passes en danger.
- **Les taux de réussite restent plus hauts dans les équipes qui dominent.** Une pondération par la possession de l'équipe est en cours.
- **Une seule saison**, et des centraux à 900 minutes minimum.

## Lancer le projet

Avec un environnement Python :

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/ball_playing_defender.py      # calcule les profils (le premier lancement télécharge la saison)
.venv/bin/streamlit run src/app_defenseurs.py      # puis ouvrir http://localhost:8501
```

Avec Docker :

```bash
docker build -t football .
docker run --rm -it -v "$PWD":/app -p 8501:8501 football
python src/ball_playing_defender.py
streamlit run src/app_defenseurs.py --server.address=0.0.0.0
```

## Organisation du code

- `src/ball_playing_defender.py` : téléchargement et cache des données, temps de jeu au poste, analyse des passes et des actions défensives, notes et scores. Écrit `data/profils_centraux.csv`.
- `src/app_defenseurs.py` : l'application Streamlit.
- `src/discovery.py` : exploration des données.

## Outils

Python, pandas, NumPy, statsbombpy, mplsoccer, Matplotlib, Streamlit, Docker.

---

Données : StatsBomb Open Data.
