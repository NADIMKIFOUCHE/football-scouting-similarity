"""Application Streamlit : profil des défenseurs centraux de Ligue 1 2015/16.

Lancer depuis la racine du projet :
    streamlit run src/app_defenseurs.py
"""
import matplotlib

matplotlib.use("Agg")                   # dessine les graphiques sans ouvrir de fenêtre
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import Patch
from mplsoccer import PyPizza

from ball_playing_defender import MINUTES_MIN, SORTIES, profil_centraux

# Les 8 parts du graphique : (colonne de la note, libellé, groupe)
CRITERES = [
    ("note_passes", "Passes\nréussies", "Avec ballon"),
    ("note_danger", "Passes\nsous danger", "Avec ballon"),
    ("note_plus_value", "Passes\nplus-value", "Avec ballon"),
    ("note_longues", "Passes\nlongues", "Avec ballon"),
    ("note_conduites", "Conduites\nsans perte", "Avec ballon"),
    ("note_duels_sol", "Duels\nau sol", "Défense"),
    ("note_aeriens", "Duels\naériens", "Défense"),
    ("note_interceptions", "Interceptions", "Défense"),
]
NOTES = [note for note, _, _ in CRITERES]
GROUPES = ["Avec ballon", "Défense"]

# Couleurs du thème clair et du thème sombre
COULEURS = {
    "light": {"fond": "#fcfcfb", "page": "#ffffff", "texte": "#0b0b0b", "texte_2": "#52514e",
              "trait": "#e1e0d9", "Avec ballon": "#2a78d6", "Défense": "#eb6834"},
    "dark": {"fond": "#1a1a19", "page": "#0e1117", "texte": "#f0efec", "texte_2": "#c3c2b7",
             "trait": "#2c2c2a", "Avec ballon": "#3987e5", "Défense": "#d95926"},
}
# Bleu du plus clair au plus foncé, pour colorer les percentiles du classement
RAMPE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]

LEGENDE = (
    "<b>Percentile</b> : 80 = meilleur que 80 % des centraux · <b>1er</b> = meilleur des 64 · "
    "<b>Note</b> : réussite lissée (10 tentatives fictives au taux moyen), avec un léger bonus au volume "
    "en défense · <b>Sous danger</b> : sous pression, ou à moins de 18 m de son but · "
    "<b>Plus-value</b> : au moins 9 m gagnés vers l'avant, ou changement de jeu · "
    "<b>Longue</b> : plus de 27 m vers l'avant · "
    "<b>Conduites sans perte</b> : conduites progressives / (conduites progressives + pertes de balle) · "
    "<b>Score relance</b> : moyenne des percentiles en passes réussies, sous danger et plus-value · "
    "<b>Score défense</b> : moyenne des percentiles en duels au sol, duels aériens et interceptions · "
    "<b>Défenseur relanceur</b> : moyenne harmonique des deux, qui reste basse si l'un des deux est faible · "
    "<b>Notes de pied</b> : réussite lissée du pied × son utilisation"
)


FICHIER = SORTIES / "profils_centraux.csv"


@st.cache_data                          # chargé une seule fois, pas à chaque clic
def charger_profils(date_du_fichier):
    # date_du_fichier : quand le CSV est recalculé, le cache se renouvelle tout seul
    return pd.read_csv(FICHIER, index_col="player")


def rang_texte(rang):
    return "1er" if rang == 1 else f"{rang}e"


def style_page(c):
    # Page fixe (pas de défilement), graphique à la hauteur de l'écran, légende collée en bas
    st.markdown(f"""<style>
        html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            overflow: hidden !important; }}
        .block-container {{ padding-top: 2.5rem; padding-bottom: 0; }}
        [data-testid="stImage"] img {{ max-height: calc(100vh - 270px); width: auto !important;
            max-width: 100%; margin: 0 auto; display: block; }}
        .legende {{ position: fixed; left: 0; right: 0; bottom: 0; z-index: 100;
            padding: 0.6rem 2rem; font-size: 0.78rem; line-height: 1.5;
            background: {c["page"]}; color: {c["texte_2"]}; border-top: 1px solid {c["trait"]}; }}
    </style>""", unsafe_allow_html=True)


def pizza(percentiles, rangs, c):
    couleurs_parts = [c[groupe] for _, _, groupe in CRITERES]
    # Sur chaque part : le percentile, ou "1er" si le joueur est le meilleur des centraux
    textes = ["1er" if rang == 1 else str(p) for p, rang in zip(percentiles, rangs)]
    baker = PyPizza(
        params=[libelle for _, libelle, _ in CRITERES],
        background_color=c["page"],
        straight_line_color=c["page"], straight_line_lw=1,
        last_circle_lw=0, other_circle_lw=0,
        inner_circle_size=20,
    )
    fig, ax = baker.make_pizza(
        percentiles,
        alt_text_values=textes,
        figsize=(8, 8),
        param_location=117,             # noms des critères plus loin, pour ne pas toucher les valeurs à 100
        slice_colors=couleurs_parts,
        value_colors=["#ffffff"] * len(percentiles),
        value_bck_colors=couleurs_parts,
        color_blank_space="same", blank_alpha=0.2,     # le reste de la part, en clair
        kwargs_slices=dict(edgecolor=c["page"], zorder=2, linewidth=2),
        kwargs_params=dict(color=c["texte_2"], fontsize=13, va="center"),
        kwargs_values=dict(fontsize=13, zorder=3,
                           bbox=dict(edgecolor=c["page"], boxstyle="round,pad=0.25", lw=1)),
    )
    for texte in baker.get_value_texts():               # petite valeur : sortie du cercle central
        angle, rayon = texte.get_position()
        texte.set_position((angle, max(rayon, 32)))
    legende = [Patch(color=c[groupe], label=groupe) for groupe in GROUPES]
    fig.legend(handles=legende, loc="upper center", ncol=2, frameon=False,
               fontsize=14, labelcolor=c["texte"], bbox_to_anchor=(0.5, 0.02))   # sous le graphique
    return fig


def aller_vers(vue):
    st.session_state.vue = vue


def page_joueur(profil, percentiles, rangs, c):
    titre, choix, bouton = st.columns([2, 3, 1], vertical_alignment="bottom")
    titre.markdown("#### Défenseurs centraux — Ligue 1 2015/16")
    joueur = choix.selectbox("Joueur", sorted(profil.index), key="joueur",   # valeur gardée dans st.session_state
                             format_func=lambda j: f"{j} — {profil.loc[j, 'equipe']}",
                             placeholder="Rechercher un joueur…")
    bouton.button("Voir le classement", on_click=aller_vers, args=("classement",), width="stretch")

    rang = profil["score_global"].rank(ascending=False, method="min").astype(int)[joueur]
    resume, graphique = st.columns([1, 2], gap="large")
    with resume:
        st.markdown(f"## {joueur}")
        st.markdown(f"{profil.loc[joueur, 'equipe']}  \n{profil.loc[joueur, 'nationalite']}  \n"
                    f"{profil.loc[joueur, 'minutes']} minutes au poste")
        score, classement = st.columns(2)
        score.metric("Défenseur relanceur", f"{profil.loc[joueur, 'score_global']} / 100")
        classement.metric("Rang", f"{rang_texte(rang)} sur {len(profil)}")
        relance, defense = st.columns(2)
        relance.metric("Relance", f"{profil.loc[joueur, 'score_relance']} / 100")
        defense.metric("Défense", f"{profil.loc[joueur, 'score_defense']} / 100")
        pied_droit, pied_gauche = st.columns(2)
        pied_droit.metric("Pied droit", f"{profil.loc[joueur, 'note_pied_droit']} / 100")
        pied_gauche.metric("Pied gauche", f"{profil.loc[joueur, 'note_pied_gauche']} / 100")
    with graphique:
        fig = pizza(percentiles.loc[joueur].tolist(), rangs.loc[joueur].tolist(), c)
        st.pyplot(fig, alt=f"Percentiles de {joueur} sur {len(CRITERES)} critères")
        plt.close(fig)                  # libère la mémoire


def couleur_percentile(p):
    i = min(int(p / 100 * len(RAMPE)), len(RAMPE) - 1)
    texte = "#0b0b0b" if i < 4 else "#ffffff"
    return f"background-color: {RAMPE[i]}; color: {texte}"


def page_classement(profil, percentiles):
    retour, titre = st.columns([1, 6], vertical_alignment="center")
    retour.button("← Retour", on_click=aller_vers, args=("joueur",), width="stretch")
    titre.markdown(f"#### Classement des {len(profil)} défenseurs centraux · "
                   "percentiles (100 = meilleur) · clique sur un en-tête pour trier")
    colonnes_criteres = {note: libelle.replace("\n", " ") for note, libelle, _ in CRITERES}
    tableau = pd.concat([
        profil[["equipe", "nationalite", "minutes", "score_global", "score_relance", "score_defense"]],
        percentiles,
        profil[["note_pied_droit", "note_pied_gauche"]],
    ], axis=1).rename(columns={
        "equipe": "Équipe", "nationalite": "Nationalité", "minutes": "Minutes",
        "score_global": "Défenseur relanceur", "score_relance": "Relance", "score_defense": "Défense",
        "note_pied_droit": "Pied droit", "note_pied_gauche": "Pied gauche",
        **colonnes_criteres,
    })
    tableau.index.name = "Joueur"
    st.dataframe(
        tableau.style.map(couleur_percentile, subset=list(colonnes_criteres.values())),
        height=560,
        column_config={"Défenseur relanceur": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%d")},
    )


st.set_page_config(page_title="Défenseurs centraux relanceurs", layout="wide")
c = COULEURS["dark" if st.context.theme.type == "dark" else "light"]
style_page(c)

if not FICHIER.exists():                # première fois : calcul sur toute la saison
    profil_centraux().to_csv(FICHIER)
profil = charger_profils(FICHIER.stat().st_mtime)
percentiles = (profil[NOTES].rank(pct=True) * 100).round().astype(int)   # le 1er a 100
rangs = profil[NOTES].rank(ascending=False, method="min").astype(int)     # 1 = meilleur

# Joueur choisi : le 1er au départ. La réaffectation empêche Streamlit de l'oublier
# quand la liste n'est pas affichée (page classement)
if "joueur" not in st.session_state:
    st.session_state.joueur = profil["score_global"].idxmax()
st.session_state.joueur = st.session_state.joueur

if st.session_state.get("vue") == "classement":
    page_classement(profil, percentiles)
else:
    page_joueur(profil, percentiles, rangs, c)

st.markdown(f'<div class="legende">{LEGENDE}</div>', unsafe_allow_html=True)
