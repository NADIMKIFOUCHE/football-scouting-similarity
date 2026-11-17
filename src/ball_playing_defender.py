import warnings
from math import pi
from pathlib import Path
import numpy as np

import pandas as pd
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

# Pas d'identifiants StatsBomb : normal, on utilise les données gratuites
warnings.filterwarnings("ignore", category=NoAuthWarning)

# Afficher tout, sans "..." quand pandas manque de place
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

CACHE = Path(__file__).resolve().parent.parent / "data" / "events"
SORTIES = CACHE.parent                  # data/ : les résultats (CSV)
SAISON_ID = 27
COMPETION_ID = 7
POSTES_CENTRAUX = ["Left Center Back", "Center Back", "Right Center Back"]
MINUTES_MIN = 900                       # au moins l'équivalent de 10 matchs complets au poste
"""Un defenseur central moderne doit selon moi
        - gagner des duels aeriens (ratio aeriens gagnes / aeriens joues + aeriens equipe  (poids faible mais poids quand meme))
        - gagner des duels au sol (ratio duels gagnes /duels joues avec un poids max duels joues)
        - faire des passes progressives (etre capable de faire avance le jeu, avec un poids sous pression)
        - perdre le moins de ballons possible
        - faire avancer le ballon par la conduite
        - intercepter des passes (ratio interceptions / passes adverses)
        

comment identifier une qualité de relance ? 

- la capacité à faire des passes dans une position basse (donc généralement sous pression) 
            dans des zones mediane voire haute. 
            S'il a une grande quantité de succès sur ces passes, en plus d'avoir un ratio très haut, 
            alors c'est un bon relanceur. Peu importe la quantité de passe car un très bon relanceur peut se trouver
            dans une équipe qui joue bas. -> Il sera alors un profil à ne pas manquer et à scouter (si on recherche ce profil).

- on peut parler du ratio passe réussis/passe raté pour juger de :
    - l'IQ du joueur
    - de sa concentration
    des valeurs basses sur ces deux points, peuvent être éliminatoire, même si l'age du joueur et son expérience 
    professionelle peuvent nous indiquer plutôt un gros potentiel, s'il a de grosses qualitées forte comme la relance 
    progressives sous haute pression.
             
"""

def getAllEvents(match_id):
    fichier = CACHE / f"{match_id}.parquet"
    if fichier.exists():                    # déjà en cache 
        return pd.read_parquet(fichier)
    events = sb.events(match_id=match_id)   
    CACHE.mkdir(parents=True, exist_ok=True)
    events.to_parquet(fichier)              # on garde une copie
    return events

def getMatches(competition_id, season_id):
    fichier = CACHE / f"matches_{competition_id}_{season_id}.parquet"
    if fichier.exists():                    # déjà en cache 
        return pd.read_parquet(fichier)
    matches = sb.matches(competition_id=competition_id, season_id=season_id).sort_values(by="match_date")
    CACHE.mkdir(parents=True, exist_ok=True)
    matches.to_parquet(fichier)              # on garde une copie
    return matches

def getLineup(match_id):
    fichier = CACHE / f"lineup_{match_id}.parquet"
    if fichier.exists():                    # déjà en cache 
        return pd.read_parquet(fichier)
    lineups = sb.lineups(match_id=match_id)
    joueurs = pd.concat(lineups, names=["team"]).reset_index(level=0)   # les 2 équipes dans un seul tableau
    CACHE.mkdir(parents=True, exist_ok=True)
    joueurs.to_parquet(fichier)
    return joueurs

def minutes(temps, event=None):
    # "67:48" -> 67.8 ; None (encore sur le terrain au coup de sifflet) -> fin du match
    if not temps:
        return (event["minute"] + event["second"] / 60).max()
    m, s = temps.split(":")
    return int(m) + int(s) / 60

def getTempsDeJeu_poste(match_id, postes, events=None):
    # Minutes jouées par chaque joueur, en ne comptant que le temps passé à l'un des postes
    if events is None:
        events = getAllEvents(match_id)
    lignes = []
    for i, joueur in getLineup(match_id).iterrows():
        for position in joueur["positions"]:          # chaque morceau de match joué à un poste
            if position["position"] in postes:
                temps = minutes(position["to"], event=events) - minutes(position["from"])
                lignes.append({"player": joueur["player_name"], "temps_de_jeu": temps})
    if not lignes:
        return pd.Series(dtype=float, name="temps_de_jeu")
    return pd.DataFrame(lignes).groupby("player")["temps_de_jeu"].sum()

def getTempsDeJeu():
    fichier = CACHE / f"temps_de_jeu.parquet"
    if fichier.exists():                    # déjà en cache
        return pd.read_parquet(fichier)

    lignes = []
    for match_id in getMatches(COMPETION_ID, SAISON_ID)["match_id"]:
        events = getAllEvents(match_id)                  # une seule lecture par match
        lineups = sb.lineups(match_id=match_id)
        for equipe, joueurs in lineups.items():       # d'abord les équipes…
            for i, joueur in joueurs.iterrows():      # …puis les joueurs
                temps = 0
                for position in joueur["positions"]:  # un joueur peut changer de poste
                    temps += minutes(position["to"], event=events) - minutes(position["from"])
                if temps > 10:                         # remplaçant pas entré : ignoré
                    lignes.append({"player": joueur["player_name"], "minutes": temps})
    table = pd.DataFrame(lignes)
    CACHE.mkdir(parents=True, exist_ok=True)
    table.to_parquet(fichier)
    return table.groupby("player")["minutes"].sum().sort_values(ascending=False)

#events_l1_2015_2016 = sb.events(match_id=getMatches(7, 27).match_id.iloc[0])                        # toutes les actions d'un match
#match_id = getMatches(COMPETION_ID, SAISON_ID).iloc[1]["match_id"]
#Comptons le nombre de pass de chaque joueur dans un match
#print(getMatches(7, 27))
#print(events_l1_2015_2016)

def getPasses_from_match(match_id):
    events = getAllEvents(match_id)
    passes_of_the_match = events[events["type"] == "Pass"]
    passes_count = passes_of_the_match.groupby("player").size().sort_values(ascending=False)
    return passes_count

#print(getPasses_from_match(match_id))

def getPasses_from_match_center_back_only(match_id):
    list_center_backs = ["Left Center Back", "Center Back", "Right Center Back"]
    events = getAllEvents(match_id)
    passes_of_the_match = events[events["type"] == "Pass"]
    passes_of_the_match_center_backs = passes_of_the_match[passes_of_the_match["position"].isin(list_center_backs)]
    passes_of_the_match_center_backs_reussis = passes_of_the_match_center_backs[passes_of_the_match_center_backs["pass_outcome"].isna()]
    passes_of_the_match_center_backs_raté = passes_of_the_match_center_backs[passes_of_the_match_center_backs["pass_outcome"].notna()]

    table = pd.DataFrame({
        "passes": passes_of_the_match_center_backs.groupby("player").size(),
        "reussies": passes_of_the_match_center_backs_reussis.groupby("player").size(),
        "ratees": passes_of_the_match_center_backs_raté.groupby("player").size(),
    })
    table = table.fillna(0).astype(int)
    
    return table.sort_values("passes", ascending=False)

#print(getPasses_from_match_center_back_only(match_id))
def passes_reussis(competition_id, season_id):
    table = table = pd.DataFrame({
        "passes": [],
        "reussies": [],
        "ratees": [],
        "temps_de_jeu": [],
    })
    list_center_backs = ["Left Center Back", "Center Back", "Right Center Back"]
    for match_id in getMatches(competition_id, season_id)["match_id"]:
        passes = getPasses_from_match_center_back_only(match_id)
        temps = getTempsDeJeu_poste(match_id, list_center_backs)
        table = pd.concat([table, pd.concat([passes, temps], axis=1)])   # côte à côte, puis sous les autres matchs
    table = table.groupby(level=0).sum()
    table = table.fillna(0).astype(int)
    table = table[table["passes"] >= 200]
    table["pourcentage"] = (table["reussies"] / table["passes"] * 100).round(1)

    return table.sort_values("passes", ascending=False)

#print(passes_reussis(COMPETION_ID, SAISON_ID))

def evenements_centraux(competition_id, season_id):
    # Toutes les actions faites au poste de défenseur central sur la saison,
    # et les minutes jouées à ce poste par chaque joueur
    actions, temps = [], []
    for match_id in getMatches(competition_id, season_id)["match_id"]:
        events = getAllEvents(match_id)               # une seule lecture par match
        actions.append(events[events["position"].isin(POSTES_CENTRAUX)])
        temps.append(getTempsDeJeu_poste(match_id, POSTES_CENTRAUX, events=events))
    return pd.concat(actions), pd.concat(temps).groupby(level=0).sum()


def analyse_passes(actions):
    """ Donnéees accessibles j'ai la taille, l'angle, j'ai la hauteur, depart et arrivée,
    miscommunication(annule event), le pied, switch, passe type ->NAN, recovery et interception uniquement(pas cf etc),
    outcome

    miscommunication -> eliminer

    categories de passes reussis rate
    passes en grand danger  | passes sans danger
    passe est sous pressions -> passes en grand danger
    passe est basse et angle suffisant 45deg a peu pres(symetrie) -> passes en grand danger


    passe qui fait avancer le jeu reussis/rate
            passe plus valus value | passe de conservation, laterale sans plus value
            angle 45 -> passe plus value
            hauteur -> longue ou semi longue -> plus value
            passe d'une certaine taille (a definir) -> plus value
            switch -> plus value


    ratio passe  pied
    droite gauche
    reussis rate reussis rate
    """
    passes = actions[actions["type"] == "Pass"].copy()
    # Jeu courant uniquement : pass_type vide, Recovery ou Interception (pas de coups de pied arrêtés)
    passes = passes[passes["pass_type"].isna() | passes["pass_type"].isin(["Recovery", "Interception"])]
    # Miscommunication : action annulée -> éliminée
    passes = passes[passes["pass_miscommunication"].isna()]

    passes["reussie"] = passes["pass_outcome"].isna()        # StatsBomb : passe réussie = pass_outcome vide
    passes["x"] = passes["location"].str[0]
    passes["y"] = passes["location"].str[1]
    passes["x_fin"] = passes["pass_end_location"].str[0]
    passes["y_fin"] = passes["pass_end_location"].str[1]
    passes["gain"] = passes["x_fin"] - passes["x"]            # terrain gagné vers le but adverse (yards)
    angle = passes["pass_angle"].abs()                        # 0 = vers l'avant, pi = vers l'arrière (symétrie)

    # Passes en grand danger : sous pression, ou latérale / vers l'arrière près de son but (toute la largeur)
    pres_de_son_but = passes["x"] < 20
    passes["danger"] = (passes["under_pressure"].eq(True) | pres_de_son_but)

    # Passes à plus-value : font gagner au moins 10 yards (angle + longueur), ou changement de jeu 
    # il faut verifier que l'adjacent de la passe soit > 10
    passes["plus_value"] = (passes["gain"] >= 10) | passes["pass_switch"].eq(True)

    # Passe longue : plus de 30 yards, vers l'avant
    passes["longue"] = (passes["pass_length"] > 30) & (passes["gain"] > 0)

    passes["pied_gauche"] = passes["pass_body_part"] == "Left Foot"
    passes["pied_droit"] = passes["pass_body_part"] == "Right Foot"

    # Pour chaque catégorie : passes tentées et réussies, par joueur
    table = pd.DataFrame({
        "passes": passes.groupby("player").size(),
        "reussies": passes.groupby("player")["reussie"].sum(),
    })
    for categorie in ["danger", "plus_value", "longue", "pied_gauche", "pied_droit"]:
        sous_ensemble = passes[passes[categorie]]
        table[f"{categorie}_tentees"] = sous_ensemble.groupby("player").size()
        table[f"{categorie}_reussies"] = sous_ensemble.groupby("player")["reussie"].sum()
    return table.fillna(0).astype(int)


def analyse_defense(actions):
    # Duels aériens, duels au sol, interceptions, pertes de balle, conduites progressives

    colonnes_aeriennes = ["pass_aerial_won", "clearance_aerial_won", "shot_aerial_won", "miscontrol_aerial_won"]
    tacle = (actions["type"] == "Duel") & (actions["duel_type"] == "Tackle")
    interception = actions["type"] == "Interception"
    gain_conduite = actions["carry_end_location"].str[0] - actions["location"].str[0]

    indicateurs = pd.DataFrame({
        "player": actions["player"],
        # Duel aérien gagné : noté sur l'action qui suit (passe, dégagement, tir…), perdu : Duel "Aerial Lost"
        "aeriens_gagnes": actions[colonnes_aeriennes].eq(True).any(axis=1),
        "aeriens_perdus": (actions["type"] == "Duel") & (actions["duel_type"] == "Aerial Lost"),
        # Duel au sol : tacle gagné ou perdu, et "Dribbled Past" = éliminé par un dribble
        "tacles": tacle,
        "tacles_gagnes": tacle & actions["duel_outcome"].isin(["Won", "Success In Play", "Success Out"]),
        "elimine": actions["type"] == "Dribbled Past",
        "interceptions": interception,
        "interceptions_gagnees": interception & actions["interception_outcome"].isin(["Won", "Success In Play", "Success Out"]),
        "pertes": actions["type"].isin(["Dispossessed", "Miscontrol"]),
        "conduites_progressives": (actions["type"] == "Carry") & (gain_conduite >= 10),
    })
    return indicateurs.groupby("player").sum().astype(int)


def nationalites(competition_id, season_id):
    # Nationalité de chaque joueur, lue dans les compositions d'équipe
    joueurs = pd.concat([getLineup(match_id) for match_id in getMatches(competition_id, season_id)["match_id"]])
    return joueurs.drop_duplicates("player_name").set_index("player_name")["country"]


def profil_centraux(competition_id=COMPETION_ID, season_id=SAISON_ID, minutes_min=MINUTES_MIN):
    actions, temps = evenements_centraux(competition_id, season_id)
    t = pd.concat([temps.rename("minutes"), analyse_passes(actions), analyse_defense(actions)], axis=1).fillna(0)
    t = t[t["minutes"] >= minutes_min]
    t["conduites_et_pertes"] = t["conduites_progressives"] + t["pertes"]
    t["aeriens"] = t["aeriens_gagnes"] + t["aeriens_perdus"]
    t["duels_sol"] = t["tacles"] + t["elimine"]

    profil = pd.DataFrame(index=t.index)
    profil["equipe"] = actions.groupby("player")["team"].agg(lambda equipes: equipes.mode()[0])
    profil["nationalite"] = nationalites(competition_id, season_id)
    profil["minutes"] = t["minutes"].round().astype(int)
    par90 = 90 / t["minutes"]

    def pourcentage(a, b):
        return (t[a] / t[b] * 100).round(1)

    # Passes : des ratios, pour ne pas dépendre du temps de possession de l'équipe
    profil["passes_90"] = (t["passes"] * par90).round(1)
    profil["reussite_passes"] = pourcentage("reussies", "passes")
    profil["part_danger"] = pourcentage("danger_tentees", "passes")
    profil["reussite_danger"] = pourcentage("danger_reussies", "danger_tentees")
    profil["part_plus_value"] = pourcentage("plus_value_tentees", "passes")         # ambition
    profil["reussite_plus_value"] = pourcentage("plus_value_reussies", "plus_value_tentees")
    profil["part_longues"] = pourcentage("longue_tentees", "passes")
    profil["reussite_longues"] = pourcentage("longue_reussies", "longue_tentees")

    # Balle au pied : conduites progressives face aux pertes de balle
    profil["conduites_prog_90"] = (t["conduites_progressives"] * par90).round(2)
    profil["pertes_90"] = (t["pertes"] * par90).round(2)
    profil["securite_balle"] = pourcentage("conduites_progressives", "conduites_et_pertes")

    # Défense : volumes par 90 minutes au poste, et taux de réussite
    profil["duels_sol_90"] = (t["duels_sol"] * par90).round(2)
    profil["reussite_duels_sol"] = pourcentage("tacles_gagnes", "duels_sol")
    profil["aeriens_90"] = (t["aeriens"] * par90).round(2)
    profil["reussite_aeriens"] = pourcentage("aeriens_gagnes", "aeriens")
    profil["interceptions_90"] = (t["interceptions"] * par90).round(2)
    profil["reussite_interceptions"] = pourcentage("interceptions_gagnees", "interceptions")

    # Pied faible : réussite lissée (K passes fictives au taux moyen) x utilisation du pied (poids W)
    K, W = 10, 0.3
    tentees_pieds = t["pied_gauche_tentees"] + t["pied_droit_tentees"]
    p0 = (t["pied_gauche_reussies"] + t["pied_droit_reussies"]).sum() / tentees_pieds.sum()   # réussite moyenne
    tentees_max = t[["pied_gauche_tentees", "pied_droit_tentees"]].max(axis=1)                # passes du pied fort

    def note_pied(pied):
        lisse = (t[f"{pied}_reussies"] + K * p0) / (t[f"{pied}_tentees"] + K)
        utilisation = t[f"{pied}_tentees"] / tentees_max                                      # 1 pour le pied fort
        return (100 * lisse * (1 - W + W * utilisation)).round().astype(int)

    profil["note_pied_gauche"] = note_pied("pied_gauche")
    profil["note_pied_droit"] = note_pied("pied_droit")

    # Notes des 8 critères du graphique : réussite lissée x bonus de volume
    #  - lissage : K tentatives fictives au taux moyen des centraux (peu de tentatives -> proche de la moyenne)
    #  - volume : +ALPHA quand le volume par 90 est multiplié par 10 (progressif, léger). Seulement là où
    #    le volume ne dépend pas de la possession de l'équipe : défense, moitié pour les conduites, rien pour les passes
    ALPHA = 0.075

    def note(reussies, tentees, alpha=0.0, volume=None):
        p0 = t[reussies].sum() / t[tentees].sum()                         # taux moyen des centraux
        lisse = (t[reussies] + K * p0) / (t[tentees] + K)
        volume_90 = t[volume or tentees] * par90
        return (100 * lisse * (1 + alpha * np.log10(1 + volume_90))).round(1)

    profil["note_passes"] = note("reussies", "passes")
    profil["note_danger"] = note("danger_reussies", "danger_tentees")
    profil["note_plus_value"] = note("plus_value_reussies", "plus_value_tentees")
    profil["note_longues"] = note("longue_reussies", "longue_tentees")
    profil["note_conduites"] = note("conduites_progressives", "conduites_et_pertes", ALPHA / 2,
                                    volume="conduites_progressives")
    profil["note_duels_sol"] = note("tacles_gagnes", "duels_sol", ALPHA)
    profil["note_aeriens"] = note("aeriens_gagnes", "aeriens", ALPHA)
    profil["note_interceptions"] = note("interceptions_gagnees", "interceptions", ALPHA)

    # Score de relanceur (0-100) : moyenne des percentiles des 3 critères de passe (poids égaux pour l'instant)
    criteres = ["note_passes", "note_danger", "note_plus_value"]
    profil["score_relance"] = (profil[criteres].rank(pct=True).mean(axis=1) * 100).round().astype(int)

    # Score défensif (0-100) : moyenne des percentiles des 3 critères défensifs
    criteres_defense = ["note_duels_sol", "note_aeriens", "note_interceptions"]
    profil["score_defense"] = (profil[criteres_defense].rank(pct=True).mean(axis=1) * 100).round().astype(int)

    # Score de défenseur relanceur : moyenne harmonique des deux scores (comme le F1-score).
    # Elle reste basse si l'un des deux est faible : il faut être bon dans les deux
    relance, defense = profil["score_relance"], profil["score_defense"]
    profil["score_global"] = (2 * relance * defense / (relance + defense)).round().astype(int)
    return profil.sort_values("score_global", ascending=False)


if __name__ == "__main__":
    profil = profil_centraux()
    profil.to_csv(SORTIES / "profils_centraux.csv")
    print(f"{len(profil)} défenseurs centraux avec au moins {MINUTES_MIN} minutes au poste\n")
    colonnes = ["equipe", "nationalite", "minutes", "score_global", "score_relance", "score_defense",
                "note_pied_gauche", "note_pied_droit"]
    print(profil[colonnes].head(15))
