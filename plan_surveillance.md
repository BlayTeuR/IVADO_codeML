# Plan de surveillance en production

Ce plan dit comment s'assurer, une fois le modèle corrigé en service, que le biais régional ne
revient pas. Il complète `audit_rapport.ipynb` (le diagnostic) et `model_corrige.ipynb` (la
correction).

## 1. Principes

1. **La région mesure, elle ne décide pas.** Le modèle neutralise la région au moment de décider.
   La région, le code postal et la distance ne servent qu'à mesurer l'équité. Leur accès est limité à
   l'équipe d'audit.
2. **Le modèle aide le comité, il ne le remplace pas.** Les dossiers proches du seuil sont revus par
   un humain, et tout refus peut être contesté.
3. **Pas de boucle de rétroaction.** On ne réentraîne jamais le modèle sur ses propres décisions :
   il apprendrait ses propres erreurs. Le réentraînement exige des étiquettes indépendantes (section 6).
4. **Égalité des chances comme métrique principale.** À mérite égal, chance égale, quelle que soit la
   région (justification : `audit_rapport.ipynb`, section 8).

## 2. Indicateurs

| # | Indicateur | Fréquence | Seuil d'alerte | Source |
|---|---|---|---|---|
| 1 | Taux d'octroi global | chaque cohorte | hors de 36–44 % | `surveillance.py` |
| 2 | Écart de taux d'octroi centres − régions éloignées | chaque cohorte | > 5 points | `surveillance.py` |
| 3 | Ratio des 4/5 (taux du groupe le moins favorisé ÷ taux de l'autre) | chaque cohorte | < 0,80 | `surveillance.py` |
| 4 | Taux d'octroi de chacune des 5 régions | chaque cohorte | une région à plus de 8 points de la moyenne | `surveillance.py` |
| 5 | Dérive des variables (PSI : cote R, heures, revenu, distance) | chaque cohorte | PSI > 0,20 | `surveillance.py` |
| 6 | Part des régions éloignées parmi les demandes | chaque cohorte | variation > 20 % | `surveillance.py` |
| 7 | **Écart d'égalité des chances**, mesuré sur un échantillon d'audit indépendant | annuelle | > 0,05 | panel indépendant |
| 8 | Taux de recours et de décisions renversées, par région | trimestrielle | un groupe à plus du double de l'autre | registre des recours |
| 9 | Réussite des boursiers (diplomation, maintien de la bourse), par région | annuelle | écart > 5 points à cote R comparable | registre académique |

**Pourquoi l'indicateur 7 demande un panel.** L'égalité des chances se mesure contre le mérite réel,
pas contre les décisions du modèle. Chaque année, on tire au hasard au moins 400 dossiers, en
nombre égal par groupe. Un panel indépendant les évalue **sans voir** la région, le code postal ni la
distance. On calcule ensuite le taux d'octroi des dossiers jugés méritants, dans chaque groupe. C'est
le seul indicateur qui mesure directement ce que l'on veut garantir.

Les indicateurs 1 à 6 ne demandent aucune étiquette et donnent l'alerte dès la publication des
décisions.

## 3. En cas d'alerte

| Niveau | Déclencheur | Action | Délai |
|---|---|---|---|
| Vigilance | un seuil franchi sur les indicateurs 4, 5, 6 ou 8 | analyse par l'équipe d'audit, note au comité d'éthique | 2 semaines |
| Alerte | un seuil franchi sur les indicateurs 2, 3, 7 ou 9, ou deux cohortes de suite en vigilance | revue humaine de tous les refus de la cohorte dans la région touchée, audit complet du modèle | avant la publication suivante |
| Arrêt | indicateur 1 hors enveloppe, ou écart d'égalité des chances > 0,10 | retour au processus humain (comité à l'aveugle sur la région), modèle suspendu | immédiat |

## 4. Garde-fous humains

- **Zone grise.** Les dossiers dont le score est à moins de 0,25 point de cote R du seuil sont revus par
  un membre du comité, sans voir la région. Sur la cohorte d'évaluation, cela représente environ
  250 dossiers sur 4 000 (6 %).
- **Explication.** Chaque candidat refusé reçoit les principaux facteurs de la décision (cote R, heures
  travaillées) et apprend qu'un traitement automatisé a été utilisé.
- **Recours.** Tout candidat peut demander une révision par une personne en mesure de modifier la
  décision. Les recours sont consignés par région (indicateur 8).

## 5. Cadre légal

- **Loi 25, article 12.1 de la Loi sur la protection des renseignements personnels dans le secteur
  privé.** Une décision fondée exclusivement sur un traitement automatisé doit être signalée à la
  personne. Sur demande, elle doit connaître les renseignements utilisés, les raisons et principaux
  facteurs de la décision, et pouvoir présenter ses observations à un membre du personnel en mesure
  de la réviser. La section 4 y répond.
- **Charte des droits et libertés de la personne du Québec, article 10.** La « condition sociale » est
  un motif de discrimination interdit. Avantager les familles aisées, comme le faisait le comité, pose
  ce risque. C'est une raison de plus de neutraliser le revenu familial.

## 6. Réentraînement

Le modèle n'est réentraîné que si **toutes** ces conditions sont réunies :

1. les nouvelles étiquettes viennent d'une source indépendante des décisions du modèle (panel à
   l'aveugle, ou résultats académiques réels) ;
2. `audit_rapport.ipynb` est réexécuté sur les nouvelles données, et la pénalité régionale mesurée est
   documentée ;
3. le nouveau modèle fait au moins aussi bien que l'ancien sur l'indicateur 7, sur l'échantillon
   d'audit de l'année ;
4. le comité d'éthique approuve le changement, et la version est consignée (date, données, résultats).

Si l'indicateur 5 signale une dérive (PSI > 0,20), on réaudite avant toute nouvelle cohorte, même
sans réentraîner.

## 7. Rôles

| Rôle | Responsabilité |
|---|---|
| Propriétaire du modèle | exécute `surveillance.py` à chaque cohorte, tient le registre des versions |
| Équipe d'audit (indépendante de l'équipe modèle) | seule à accéder à la région ; analyse les alertes ; organise le panel annuel |
| Comité d'éthique | tranche les alertes, approuve les réentraînements et les choix éthiques (section 8) |
| Auditeur externe | revue complète une fois par an |

## 8. Choix éthiques documentés

Ces choix ne sont pas techniques. Le comité d'éthique doit les revoir chaque année.

| Choix | Raison | Alternative écartée |
|---|---|---|
| Égalité des chances plutôt que parité démographique | une bourse au mérite doit traiter également les mérites égaux | la parité imposerait des quotas indépendants des dossiers |
| Heures travaillées conservées | réussir en travaillant pendant ses études est un mérite réel | les retirer pénaliserait les étudiants des régions, qui travaillent plus |
| Revenu familial neutralisé | avantager les familles aisées n'est pas un critère de mérite et reproduit un biais régional | le garder maintiendrait un avantage aux grands centres |
| Code postal et distance exclus | ils n'ont aucun effet sur la décision à région égale ; ils ne font que révéler la région | les garder laisserait passer la pénalité par la bande |
| Première génération neutre | le comité ne l'utilisait pas, et les données ne justifient ni bonus ni pénalité | un bonus serait un choix de politique, à décider explicitement |

## 9. Calendrier

| Moment | Action |
|---|---|
| Avant le déploiement | audit complet, test de `surveillance.py` sur les décisions historiques, fiche du modèle publiée |
| À chaque cohorte | `python surveillance.py decisions.csv dossiers.csv`, revue de la zone grise |
| Chaque trimestre | bilan des recours par région |
| Chaque année | panel à l'aveugle (indicateur 7), réussite des boursiers (indicateur 9), audit externe, revue des choix éthiques |

## 10. Utiliser `surveillance.py`

```bash
python surveillance.py predictions.csv data/candidats_evaluation.csv
```

Le script affiche le taux d'octroi par région, l'écart entre groupes, le ratio des 4/5, la part des
régions éloignées et la dérive des variables. Il liste les alertes et renvoie un code de sortie 1 s'il y
en a, ce qui permet de l'intégrer à une chaîne automatisée.

Sur notre soumission, il ne lève aucune alerte (écart −0,004, ratio des 4/5 de 1,01). Sur les décisions
du modèle en production, il en lève six : écart de 0,190, ratio de 0,59, et quatre régions sur cinq à plus
de 8 points de la moyenne.