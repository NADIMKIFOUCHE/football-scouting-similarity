import warnings

import pandas as pd
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

# Pas d'identifiants StatsBomb : normal, on utilise les données gratuites
warnings.filterwarnings("ignore", category=NoAuthWarning)

# Afficher tout, sans "..." quand pandas manque de place
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

competitions = sb.competitions()                              # toutes les compétitions dispo
matches_l1_2015_2016 = sb.matches(competition_id=7, season_id=27).sort_values(by="match_date")     # ton lien : matches/7/27.json
events_l1_2015_2016 = sb.events(match_id=matches_l1_2015_2016.match_id.iloc[0])                        # toutes les actions d'un match
#lineups_l1_2015_2016 = sb.lineups(match_id=...)                       # compositions
#print(matches_l1_2015_2016.iloc[1]["match_id"])
match_id = matches_l1_2015_2016.iloc[1]["match_id"]

# manipulation des données avec pandas
# 1er match du championnat de France 2015-2016 : OM - Caen
# Nettoyage des données : on supprime les colonnes vides

def getEvents(match_id):
    events = sb.events(match_id=match_id)
    for row, event in events.head(1).iterrows():
        print(event.dropna())
        pass
    return events

#getEvents(match_id)

# Compos du match
def getLineup(match_id):
    lineups = sb.lineups(match_id=match_id)
    list_players = []
    for equipe, joueurs in lineups.items():
        for i, joueur in joueurs.iterrows():
            if not joueur["positions"]:
                pass
            else:
                if joueur["positions"][0]["from"] == "00:00":
                    list_players.append((joueur["jersey_number"], joueur["player_name"], joueur["positions"][0]["position"]))
    return list_players

#getLineup(match_id)

def toStringLineup(lineup):
    goalkeeper = ["Goalkeeper"]
    defenders = ["Left Back", "Left Center Back", "Center Back", "Right Center Back", "Right Back"]
    defensive_midfielders_wingers = ["Left Wing Back", "Left Defensive Midfield", "Center Defensive Midfield",
                                         "Right Defensive Midfield", "Right Wing Back"]
    midfielders = ["Left Midfield", "Left Center Midfield", "Center Midfield", "Right Center Midfield", "Right Midfield"]
    midfielders_forwards = ["Left Wing", "Left Attacking Midfield", "Center Attacking Midfield",
                                "Right Attacking Midfield", "Right Wing"]
    nineandhalf = ["Secondary Striker"]
    forwards = ["Left Center Forward", "Center Forward", "Right Center Forward"]
    list_positions_reference = [goalkeeper, defenders, defensive_midfielders_wingers, midfielders, midfielders_forwards,
                      nineandhalf, forwards]
    list_positions1 = [area.copy() for area in list_positions_reference]
    list_positions2 = [area.copy() for area in list_positions_reference]
    team1 = lineup[0:11]
    team2 = lineup[11:22]
    for joueur in team1:
        joueur_position = joueur[2]
        for i, area in enumerate(list_positions1):
            for j, position in enumerate(area):
                if joueur_position == position:
                    list_positions1[i][j] = joueur[1]
    for joueur in team2:
        joueur_position = joueur[2]
        for i, area in enumerate(list_positions2):
            for j, position in enumerate(area):
                if joueur_position == position:
                    list_positions2[i][j] = joueur[1]

    def minus(liste):
        return [[position for position in area if position not in list_positions_reference[i]]
                for i, area in enumerate(liste)]

    lineup1 = minus(list_positions1)
    lineup2 = minus(list_positions2)

    def printLineup(lineup):
        for grp in lineup:
            count = 5
            string = ""
            for joueur in grp:
                count -= 1
                string += joueur + "\t"
            if string != "":
                print("\t"*(count//2) + string)
        print("")

    printLineup(lineup1)
    printLineup(lineup2)

#toStringLineup(getLineup(match_id))


        

    


                    
                    


        

