# Roadmap ÉquiAlgo

Stratégie end-to-end pour le défi ÉquiAlgo (Hackathon Génie et Informatique 2026, 24 h).

> **En une phrase :** ce défi ne se gagne pas avec un meilleur modèle, il se gagne en reconstruisant une cible débiaisée.

## Table des matières

1. [Ce qui détermine réellement le score](#1-ce-qui-détermine-réellement-le-score)
2. [Diagnostic (EDA)](#2-diagnostic-eda-orienté-vers-une-seule-question--doù-viennent-les-21-points-)
3. [Le cœur : reconstruire une cible débiaisée](#3-le-cœur--reconstruire-une-cible-débiaisée)
4. [Validation sans vérité terrain](#4-validation-sans-vérité-terrain)
5. [Modèles](#5-modèles--ce-qui-vaut-la-peine-et-ce-qui-ne-la-vaut-pas)
6. [Choix de la métrique d'équité](#6-choix-de-la-métrique-déquité-à-défendre-devant-le-jury)
7. [Gouvernance et monitoring](#7-gouvernance-et-monitoring-25-points-souvent-bâclés-par-les-autres-équipes)
8. [Planning sur 24 h](#8-planning-sur-24-h-hypothèse--3-ou-4-personnes)
9. [Structure du dépôt](#9-structure-du-dépôt-adaptée-aux-livrables-imposés)
10. [Priorisation par ROI](#10-priorisation-par-roi)

---

## 1. Ce qui détermine réellement le score

| Bloc | Points | Ce qui compte vraiment |
|---|---:|---|
| Équité (auto) | 20 | Part de l'écart d'égalité des chances (0,270) fermée, **mesurée contre l'étalon caché** |
| Utilité (auto) | 15 | Accord avec l'étalon caché, entre un tirage aléatoire et une allocation parfaite |
| Diagnostic | 25 | Rigueur de la preuve du biais et des proxys |
| Gouvernance | 25 | Plan de monitoring, choix éthiques justifiés |
| Pitch et code | 15 | Clarté, reproductibilité |

**La nature réelle du problème.** C'est une classification binaire avec **étiquettes biaisées (label bias)**, sous contrainte de budget. En pratique, c'est un problème de **classement puis seuil** : il faut classer 4 000 candidats et en retenir environ 1 600.

**Le piège central.** Les 88 % d'exactitude mesurent la fidélité au comité audité, pas la justesse. Le carnet le dit lui-même en section 4 : le TPR est calculé contre `decision_octroi`. Maximiser l'exactitude sur `decision_octroi` revient à maximiser la reproduction du biais.

**Hypothèse de travail sur l'étalon (à confirmer en EDA).** L'étalon ressemble à « la règle du comité, sans la pénalité régionale ». Le README dit que l'écart de cote R explique *une partie* des 21 points. L'étalon contient donc probablement encore un **petit écart légitime** entre groupes, quelques points.

### Conséquences

- La parité démographique (écart = 0) **surcorrigerait** et coûterait des points d'utilité.
- L'égalité des chances est à la fois la métrique notée et la bonne métrique pour une bourse au mérite.
- Il faut viser un écart de taux de sélection égal à **l'écart expliqué par les variables légitimes**, ni plus ni moins. Un écart inversé ne compte probablement pas comme « fermé ».

### Contraintes dures

- Viser un taux d'octroi de **40,0 %** (1 600 octrois), au centre de la fourchette 36–44 %. Une assertion automatique doit le vérifier avant chaque export.
- Même ordre et mêmes `id_candidat` que `candidats_evaluation.csv`, valeurs 0/1, 4 000 lignes.

### Risques principaux

1. Surcorrection, avec un écart inversé.
2. Extrapolation hors support dans le contrefactuel : les distances des régions éloignées n'existent pas dans les centres.
3. Décalage de distribution entre l'historique et l'évaluation.
4. Sortie du budget.

---

## 2. Diagnostic (EDA) orienté vers une seule question : d'où viennent les 21 points ?

Les analyses sont classées par priorité. Pour chacune, ce qu'on cherche à découvrir.

| # | Analyse | Ce qu'on cherche | Priorité |
|---|---|---|:---:|
| A | Taux d'octroi par tranche de cote R, une courbe par groupe | À R égal, l'écart persiste-t-il ? Si oui, c'est un biais direct. **C'est LE graphique du pitch.** | 🔴 |
| B | Logit interprétable : `octroi ~ R + programme + revenu + heures + distance + 1re_gen + éloigné` | Rapport de cotes de « éloigné » toutes choses égales | 🔴 |
| C | Décomposition de Fairlie (Oaxaca adapté au logit) | Part expliquée et part inexpliquée des 21 points, chiffrées. Donne la **cible d'écart résiduel** | 🔴 |
| D | Effets intra-groupe : la distance et les heures influencent-elles la décision *à l'intérieur* des centres ? Des régions éloignées ? | Si la distance n'a d'effet qu'entre les groupes, c'est un proxy pur à neutraliser. Si les heures pénalisent partout, c'est une règle du comité, et le fait de la garder est un choix éthique à documenter | 🔴 |
| E | Détection des proxys : modèle qui prédit la région à partir des autres variables (AUC globale), puis AUC variable par variable et information mutuelle | Classement des proxys pour `audit_rapport.ipynb` | 🔴 |
| F | Correspondance `code_postal_3` → région | Probablement déterministe, donc le code postal est une copie de la région et doit sortir du modèle | 🟠 |
| G | Distributions de chaque variable par groupe, avec le chevauchement | Où le contrefactuel va extrapoler | 🟠 |
| H | Historique vs évaluation : parts régionales, validation adversariale | Si l'AUC est proche de 0,5, pas de décalage, sinon il faut ajuster | 🟠 |
| I | Intersectionnel : éloigné × 1re génération, × quintile de revenu, × programme, et les 5 régions séparément | Sous-groupes doublement pénalisés, utiles pour le jury | 🟡 |
| J | Qualité : doublons, IDs communs aux deux fichiers, bornes de R, revenus aberrants | Hygiène. `info()` montre déjà zéro valeur manquante | 🟡 |

---

## 3. Le cœur : reconstruire une cible débiaisée

Quatre approches, classées par ROI. **Les implémenter toutes, puis les comparer et les combiner.**

### Approche 1 : contrefactuel « région neutralisée » (principale)

- On entraîne un modèle **additif** (logistique, ou un GAM/EBM) **avec** la région explicite et **sans** le code postal.
- En incluant la région, le biais est absorbé par le terme régional au lieu de s'étaler sur les proxys.
- À l'inférence, on fixe tous les candidats à « Centre » et on classe sur ce score.
- Pourquoi un modèle additif plutôt qu'une forêt : une forêt extrapole mal quand on combine « région = Montréal » avec 300 km de distance.
- Si l'analyse D montre que la distance est un proxy pur, on la retire ou on la plafonne.
- Argument de gouvernance très fort : **la région sert à mesurer et neutraliser le biais, jamais à décider.**

### Approche 2 : apprendre la règle sur le groupe non pénalisé

- On entraîne uniquement sur les centres, puis on applique ce modèle à tout le monde.
- Narration très défendable : « on applique à chaque candidat la règle appliquée aux grands centres ».
- Même risque d'extrapolation sur la distance et les heures, donc on ajoute des contraintes monotones ou on retire ces variables.

### Approche 3 : correction des étiquettes (massaging de Kamiran-Calders)

- On classe les candidats éloignés refusés par score décroissant et on inverse leurs étiquettes.
- On s'arrête quand l'écart résiduel égale l'écart expliqué obtenu en C.
- On réentraîne ensuite sur les étiquettes corrigées.

### Approche 4 : fairlearn, comme bouton de réglage pour le front de Pareto

- `ExponentiatedGradient` avec une borne de parité démographique ε, ou `ThresholdOptimizer`.
- ⚠️ Le `ThresholdOptimizer` avec contrainte d'égalité des chances **égalise le TPR contre les étiquettes biaisées**. Il ferme donc l'écart du mauvais étalon.
- C'est un bon point à expliquer au jury : il prouve qu'on a compris le piège.

### Passage du score à la décision

On garde les 1 600 meilleurs scores débiaisés avec un **seuil global unique**. Il n'y a pas de quota par région en production.

### Réglage de l'intensité du débiaisage

Le paramètre α va de 0 (comité brut) à 1 (pénalité entièrement retirée). On choisit le point où l'écart de taux de sélection égale l'écart expliqué de C. Ce balayage en α sert aussi de **front de Pareto**.

---

## 4. Validation sans vérité terrain

Le split interne contre `decision_octroi` n'est pas une estimation du score. On s'en sert autrement :

| Mesure | Rôle |
|---|---|
| **Exactitude sur les centres seulement (held-out)** | Meilleur proxy de l'utilité, *si* le comité n'a pas biaisé les centres (hypothèse à afficher) |
| Écart de taux de sélection vs écart cible de C | Proxy de l'équité |
| Égalité des chances contre des pseudo-étiquettes contrefactuelles | Proxy direct de la métrique notée |
| Stabilité sur 5 plis et plusieurs seeds | Robustesse du classement |
| **Oracle simulé** : générer des étiquettes avec une pénalité connue, vérifier que la méthode la retrouve | Très bon pour la note de rigueur. Coût moyen |

**Protocole :** 5 plis stratifiés sur `decision_octroi × groupe`, seed 42 partout.

> **HxBuddy, point à clarifier en urgence.** Il affiche une exactitude et un F1 « indicatifs ». Contre quoi ? S'ils sont calculés contre l'étalon, c'est un signal précieux pour l'utilité. Dans ce cas, il faut l'utiliser avec parcimonie : 3 ou 4 soumissions pour trancher entre stratégies, pas 50 pour régler des hyperparamètres. Sinon on fait du surapprentissage sur le classement et c'est indéfendable devant un jury d'éthique.

---

## 5. Modèles : ce qui vaut la peine, et ce qui ne la vaut pas

| Niveau | Modèle | Verdict |
|---|---|---|
| Naïf | 40 % meilleures cotes R, et c'est tout | 🔴 À soumettre dès la 2e heure. Ce sera probablement une baseline étonnamment forte si l'étalon est fondé sur le mérite. C'est le filet de sécurité |
| Classique | Logistique additive + contrefactuel | 🔴 Modèle principal, interprétable, extrapole proprement |
| Performant | EBM (`interpret`) ou GAM | 🟠 Mêmes avantages avec des effets non linéaires, et de bons graphiques pour le jury |
| Performant | LightGBM avec contraintes monotones | 🟡 Seulement si le logit sous-ajuste nettement sur les centres |
| Avancé | Réseaux de neurones, Transformers, stacking | ❌ Inutile : 9 variables, 10 000 lignes, et l'erreur vient de l'étiquette, pas de la capacité du modèle |

**Feature engineering.** Il est minimal et chaque variable doit être justifiée :

- `log(revenu)`, `log(distance)`.
- Interaction R × programme, si la cote est relative au programme.
- Suppression de `code_postal_3`, redondant avec la région.

**Tuning.** Optuna est inutile ici. On règle seulement C (régularisation) et `min_samples_leaf`, à la main.

**Ensemble.** Une moyenne des rangs des approches 1 à 3 apporte de la robustesse, pour un petit gain. On le fait en fin de parcours.

**Pseudo-labelling.** Contre-productif, il amplifie le biais.

**TTA et données externes.** Sans objet ici.

**Analyse d'erreurs utile.** Comparer **qui entre et qui sort** par rapport au modèle de production. Par exemple : « 140 candidats éloignés avec une cote R > 30 étaient refusés ». C'est l'histoire humaine du pitch.

---

## 6. Choix de la métrique d'équité (à défendre devant le jury)

- **L'égalité des chances** est le bon choix pour une bourse au mérite. À mérite égal, la chance doit être égale.
- **La parité démographique** ignorerait l'écart réel de cote R (27,3 contre 28,0) et pénaliserait des candidats des centres plus forts.
- **La faiblesse de l'égalité des chances** est qu'elle dépend de la définition du mérite, donc des étiquettes. C'est exactement pour cela qu'on reconstruit les étiquettes au lieu de faire confiance au comité.

On rapporte aussi :

- la parité démographique ;
- le ratio des 4/5 ;
- les cinq régions séparément ;
- la calibration intra-groupe ;
- le théorème d'impossibilité (Kleinberg, Chouldechova), en une diapositive.

---

## 7. Gouvernance et monitoring (25 points, souvent bâclés par les autres équipes)

### Plan de monitoring

| Indicateur | Fréquence | Seuil d'alerte | Action |
|---|---|---|---|
| Taux d'octroi par région (les 5) | Chaque cohorte | Écart > écart légitime + 5 pts | Revue humaine, gel du modèle |
| Dérive des proxys (PSI sur distance, heures, revenu) | Mensuelle | PSI > 0,2 | Réaudit |
| Part des régions dans les demandes | Chaque cohorte | Variation > 20 % | Vérifier le décalage de population |
| Résultats réels (réussite, diplomation) par région | Annuelle | Calibration divergente | Revoir la définition du mérite |
| Taux d'appels et d'inversions en appel | Trimestrielle | Concentration régionale | Enquête |

### Mesures de gouvernance

- **Boucle de rétroaction :** ne jamais réentraîner sur les décisions du modèle. Il faut des étiquettes indépendantes, comme les résultats académiques ou un panel indépendant.
- **Révision humaine** des cas proches du seuil.
- **Recours** pour les candidats refusés.
- **Model card.**
- **Audit annuel indépendant.**
- **Région conservée** uniquement pour l'audit.
- **Cadre légal québécois :** la Loi 25 (art. 12.1 de la loi sur le secteur privé) oblige à informer la personne d'une décision fondée exclusivement sur un traitement automatisé et à lui permettre d'en demander la révision. *Point à valider avec un mentor.*

---

## 8. Planning sur 24 h (hypothèse : 3 ou 4 personnes)

### 0–1 h
- Exécuter le carnet.
- Mettre en place la structure du dépôt.
- Répartir les rôles : diagnostic, modèle, gouvernance et pitch.

### 1–4 h
- Analyses A à F.
- Soumettre la baseline « top 40 % cote R » pour avoir un `predictions.csv` valide.
- Clarifier HxBuddy.

### 4–9 h
- Implémenter les approches 1 à 4.
- Faire le balayage en α et le front de Pareto.
- Calculer les métriques proxys.

### 9–13 h
- Oracle simulé.
- Choix de l'approche finale.
- Robustesse sur les seeds et les plis.
- Nettoyage de `audit_rapport.ipynb`.

### 13–17 h
- Plan de monitoring et gouvernance.
- Model card.
- Organiser des quarts de sommeil.

### 17–21 h
- Figures finales.
- `presentation.pdf`.
- Répétition chronométrée du pitch de 5 min.

### 21–23 h
- **Gel du modèle.**
- Réexécution complète depuis zéro.
- Vérifications : 4 000 lignes, IDs dans l'ordre, valeurs 0/1, taux entre 36 et 44 %.

### Dernière heure
- Aucune modification de code. Seulement le pitch.

---

## 9. Structure du dépôt (adaptée aux livrables imposés)

```text
defi-equialgo/
├── predictions.csv          # livrable, à la racine
├── audit_rapport.ipynb      # livrable
├── model_corrige.py         # livrable : pipeline complet + front de Pareto
├── presentation.pdf         # livrable
├── baseline_model.ipynb
├── data/
├── src/
│   ├── diagnostic.py        # décomposition de Fairlie, proxys, courbes par tranche de R
│   ├── debiaisage.py        # approches 1 à 4
│   ├── metriques.py         # écarts, égalité des chances vs pseudo-étalon, budget
│   └── export.py            # assertions + écriture du CSV
├── outputs/figures/
└── README.md                # comment reproduire en une commande
```

**À automatiser :** une seule fonction `soumettre(scores)` qui coupe à 40 %, vérifie toutes les contraintes et écrit le CSV. On ne doit pas pouvoir exporter un fichier invalide.

---

## 10. Priorisation par ROI

| Action | Gain | Difficulté | Temps | Risque | Priorité |
|---|---|---|---|---|---:|
| Soumission de secours « top 40 % R » | Moyen | Très faible | 15 min | Nul | 1 |
| Courbes par tranche de R + décomposition de Fairlie | Très élevé (jury + cible) | Faible | 1,5 h | Faible | 2 |
| Approche 1 (contrefactuel logit) | Très élevé | Moyenne | 2 h | Moyen (extrapolation) | 3 |
| Analyse intra-groupe des proxys (D) | Élevé | Faible | 1 h | Faible | 4 |
| Balayage en α = front de Pareto | Élevé (livrable) | Faible | 1 h | Faible | 5 |
| Plan de monitoring + Loi 25 | Élevé (25 pts) | Faible | 2 h | Nul | 6 |
| Approches 2 et 3 + moyenne des rangs | Moyen | Moyenne | 2 h | Faible | 7 |
| Oracle simulé | Moyen (rigueur) | Moyenne | 2 h | Faible | 8 |
| Fairlearn (`ExponentiatedGradient` / `ThresholdOptimizer`) | Faible-moyen | Faible | 1 h | Faible | 9 |
| LightGBM monotone | Faible | Moyenne | 1,5 h | Moyen | 10 |
