"""Defi EquiAlgo - indicateurs de surveillance d'une cohorte.

A executer apres chaque cohorte de decisions (voir plan_surveillance.md). Le
script compare la cohorte aux dossiers historiques et leve une alerte quand un
seuil du plan est franchi.

Usage : python surveillance.py [decisions.csv] [dossiers.csv]
        (par defaut : predictions.csv et data/candidats_evaluation.csv)
"""
import sys

import numpy as np
import pandas as pd

ELOIGNEES = ['Bas-Saint-Laurent', 'Cote-Nord', 'Gaspesie-Iles-de-la-Madeleine']
ENVELOPPE = (0.36, 0.44)
ECART_MAX = 0.05          # ecart de taux d'octroi centres - regions eloignees
ECART_REGION_MAX = 0.08   # ecart d'une region a la moyenne
RATIO_MIN = 0.80          # regle des 4/5
PSI_MAX = 0.20            # derive d'une variable
PART_REGIONS_MAX = 0.20   # variation relative de la part des regions eloignees
VARIABLES_SUIVIES = ['cote_r_equivalent', 'heures_travail_semaine',
                     'revenu_familial_estime', 'distance_domicile_campus_km']


def psi(reference, cohorte, n_classes=10):
    """Population Stability Index : 0 = meme distribution, > 0,2 = derive importante."""
    bornes = np.unique(np.quantile(reference, np.linspace(0, 1, n_classes + 1)))
    bornes[0], bornes[-1] = -np.inf, np.inf
    attendu = np.histogram(reference, bornes)[0] / len(reference)
    observe = np.histogram(cohorte, bornes)[0] / len(cohorte)
    attendu, observe = np.clip(attendu, 1e-4, None), np.clip(observe, 1e-4, None)
    return float(np.sum((observe - attendu) * np.log(observe / attendu)))


def rapport(decisions, dossiers, historique):
    cohorte = dossiers.merge(decisions, on='id_candidat', validate='one_to_one')
    eloignee = cohorte['region_administrative'].isin(ELOIGNEES)
    alertes = []

    taux = cohorte['decision_octroi'].mean()
    taux_centres = cohorte.loc[~eloignee, 'decision_octroi'].mean()
    taux_regions = cohorte.loc[eloignee, 'decision_octroi'].mean()
    ecart, ratio = taux_centres - taux_regions, taux_regions / taux_centres

    print(f"Cohorte : {len(cohorte)} dossiers, taux d'octroi {taux:.1%}")
    if not ENVELOPPE[0] <= taux <= ENVELOPPE[1]:
        alertes.append(f"taux d'octroi {taux:.1%} hors de l'enveloppe")

    par_region = cohorte.groupby('region_administrative')['decision_octroi'].agg(dossiers='size', taux='mean')
    print('\nTaux d\'octroi par region')
    print(par_region.round(3))
    for region, taux_region in par_region['taux'].items():
        if abs(taux_region - taux) > ECART_REGION_MAX:
            alertes.append(f'{region} : taux {taux_region:.1%} contre {taux:.1%} en moyenne')
    print(f'\nCentres {taux_centres:.1%} | regions eloignees {taux_regions:.1%} | '
          f'ecart {ecart:+.3f} | ratio des 4/5 {ratio:.2f}')
    if abs(ecart) > ECART_MAX:
        alertes.append(f'ecart de taux d\'octroi {ecart:+.3f} (seuil {ECART_MAX})')
    if min(ratio, 1 / ratio) < RATIO_MIN:
        alertes.append(f'ratio des 4/5 {ratio:.2f} (seuil {RATIO_MIN})')

    part_hist = historique['region_administrative'].isin(ELOIGNEES).mean()
    variation = eloignee.mean() / part_hist - 1
    print(f'\nPart des regions eloignees : {eloignee.mean():.1%} (historique {part_hist:.1%}, variation {variation:+.0%})')
    if abs(variation) > PART_REGIONS_MAX:
        alertes.append(f'part des regions eloignees en variation de {variation:+.0%}')

    print('\nDerive des variables (PSI)')
    for var in VARIABLES_SUIVIES:
        valeur = psi(historique[var].values, cohorte[var].values)
        print(f'  {var:<30} {valeur:.3f}')
        if valeur > PSI_MAX:
            alertes.append(f'derive de {var} (PSI {valeur:.2f})')

    print('\n' + ('ALERTES :\n  - ' + '\n  - '.join(alertes) if alertes else 'Aucune alerte.'))
    return alertes


if __name__ == '__main__':
    chemin_decisions = sys.argv[1] if len(sys.argv) > 1 else 'predictions.csv'
    chemin_dossiers = sys.argv[2] if len(sys.argv) > 2 else 'data/candidats_evaluation.csv'
    alertes = rapport(pd.read_csv(chemin_decisions), pd.read_csv(chemin_dossiers),
                      pd.read_csv('data/donnees_demandes.csv'))
    sys.exit(1 if alertes else 0)