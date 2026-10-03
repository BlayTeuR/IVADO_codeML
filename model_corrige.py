"""Defi EquiAlgo - modele corrige.

Idee : le comite applique la meme regle partout (cote R, revenu, heures de
travail), plus une penalite fixe pour les regions eloignees. On modelise cette
regle en isolant explicitement la penalite dans un terme `eloignee` (derive de
`region_administrative`), puis on predit en mettant ce terme a 0 pour tout le
monde (decision contrefactuelle "comme si le dossier venait d'un grand
centre"). L'avantage accorde aux revenus eleves est neutralise de la meme
facon. On accorde ensuite la bourse aux 40 % de scores les plus eleves pour
respecter l'enveloppe.

Les proxys (code postal, distance) ne sont pas donnes au modele : a l'interieur
d'un groupe ils n'ont aucun effet sur la decision, ils ne servent qu'a
reconstruire la region.

Usage : python model_corrige.py [taux_octroi]
"""
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer, StandardScaler

ELOIGNEES = ['Bas-Saint-Laurent', 'Cote-Nord', 'Gaspesie-Iles-de-la-Madeleine']
TAUX_OCTROI = float(sys.argv[1]) if len(sys.argv) > 1 else 0.40


def preparer(df):
    df = df.copy()
    df['log_revenu'] = np.log(df['revenu_familial_estime'])
    df['eloignee'] = df['region_administrative'].isin(ELOIGNEES).astype(int)
    return df


def modele_comite():
    """Regression logistique avec splines : flexible mais lisible."""
    pre = ColumnTransformer([
        ('lin', StandardScaler(), ['cote_r_equivalent', 'eloignee', 'premiere_generation_universitaire']),
        ('spl', SplineTransformer(n_knots=5, degree=3), ['log_revenu', 'heures_travail_semaine']),
        ('cat', OneHotEncoder(drop='first'), ['programme_etudes']),
    ])
    return make_pipeline(pre, LogisticRegression(C=10, max_iter=5000))


def score_sans_biais(modele, df, revenu_reference):
    """Score du comite avec la penalite regionale et l'avantage de revenu neutralises.

    Le comite favorise aussi les familles aisees, ce qui avantage les centres
    (revenu moyen ~76 k$ contre ~56 k$). On donne a tout le monde le meme revenu
    pour que celui-ci ne change plus le classement.
    """
    contrefactuel = df.copy()
    contrefactuel['eloignee'] = 0
    contrefactuel['log_revenu'] = revenu_reference
    return modele.decision_function(contrefactuel)


def octroyer(score, taux):
    return (score >= np.quantile(score, 1 - taux)).astype(int)


if __name__ == '__main__':
    demandes = preparer(pd.read_csv('data/donnees_demandes.csv'))
    candidats = preparer(pd.read_csv('data/candidats_evaluation.csv'))

    modele = modele_comite().fit(demandes, demandes['decision_octroi'])
    revenu_reference = demandes['log_revenu'].median()
    decisions = octroyer(score_sans_biais(modele, candidats, revenu_reference), TAUX_OCTROI)

    soumission = pd.DataFrame({'id_candidat': candidats['id_candidat'], 'decision_octroi': decisions})
    soumission.to_csv('predictions.csv', index=False)

    taux = decisions.mean()
    print(f'{len(soumission)} lignes ecrites dans predictions.csv')
    print(f"Taux d'octroi : {taux:.1%}", '- OK' if 0.36 <= taux <= 0.44 else '- HORS BUDGET')
    print(soumission.assign(eloignee=candidats['eloignee']).groupby('eloignee')['decision_octroi'].mean().round(3))
