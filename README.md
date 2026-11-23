# Pibody Match Engine

Moteur d'intelligence relationnelle, d'appariement explicable et d'optimisation combinatoire.

## Fonctionnalites cles
- **Need Discovery** : analyse d'un besoin libre, extraction d'intention et questions de clarification.
- **Scoring 6 dimensions & Reciprocite** : pertinence, competences, complementarite, disponibilite, objectifs et reciprocite mutuelle.
- **Privacy-by-Design** : stockage SQLite protege avec pseudonymisation tant que le seuil de match mutuel n'est pas atteint.
- **Skill Path Intelligence** : parcours d'apprentissage (ressource, mentor, projet) pour combler les lacunes.
- **Optimisation combinatoire & Gouvernance** : algorithme Hongrois, Gale-Shapley, invariance sous anonymisation et audit humain tracable.

## Commandes
- pibody-match serve --port 8765 : demarre le Studio sur base SQLite vierge.
- pibody-match serve --port 8765 --demo : pre-remplit avec le jeu d'essai.
- uff check . && mypy src examples tests && pytest -v : controles qualite et tests.
