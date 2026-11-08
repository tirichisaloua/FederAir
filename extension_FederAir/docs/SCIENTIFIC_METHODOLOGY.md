# Méthodologie scientifique — FederAir Health

## Objectif
Explorer techniquement une chaîne de traitement qui relie des indicateurs environnementaux à des indicateurs de santé respiratoire, dans une architecture où les organisations conservent leurs données.

## Provenance
Le jeu étendu inclus dans le dépôt est synthétique, créé avec une graine pseudo-aléatoire fixe. Il couvre chaque jour du 01/01/2019 au 31/12/2025 (2 557 jours). Les colonnes `data_origin` valent `SYNTHETIC_DEMO`. Les données ne sont pas des observations de stations ni des admissions réelles.

## Variables environnementales simulées
PM2.5, PM10, NO2, O3, température, humidité relative, vent, précipitations et indice de trafic. La génération intègre des composantes saisonnières, calendaires, du bruit aléatoire et des bornes plausibles destinées à la démonstration.

## Variables hospitalières simulées
Nombre quotidien d'admissions respiratoires et ventilation synthétique en trois classes d'âge. Le scénario comporte une saisonnalité et une association modérée avec la pollution afin de permettre un exercice de modélisation. Cette association est une hypothèse génératrice du simulateur, pas une découverte empirique.

## Modélisation
Deux modèles de régression sont comparés : Random Forest et HistGradientBoosting. La séparation apprentissage/test est chronologique (80 % passé, 20 % période ultérieure). Les métriques sont MAE, RMSE et R². Les transformations temporelles utilisent des retards et moyennes glissantes calculés à partir du passé.

## Interprétation
Les performances mesurent la capacité des modèles à reproduire le scénario synthétique. Elles ne peuvent pas être généralisées à la ville de Tanger ou à une population de patients. Une validation sur des observations réelles, une analyse des biais, des facteurs de confusion et une validation par des spécialistes seraient indispensables avant tout usage opérationnel.

## Association et causalité
La corrélation mensuelle est descriptive. Elle n'établit pas que la pollution provoque les admissions. Saisonnalité, infections, âge, accès aux soins, météo et autres variables peuvent influencer les observations.

## Passage aux observations réelles
L'importeur OpenAQ récupère des mesures journalières pour un capteur sélectionné. Il faut vérifier les métadonnées du capteur, la géolocalisation, la période, les unités, les valeurs invalides, les trous de mesure et la licence. La série hospitalière restera synthétique tant qu'une source de données agrégées et légalement réutilisable n'aura pas été identifiée.
