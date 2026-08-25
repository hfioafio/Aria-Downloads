# Aria 2.51.0

Cette version fiabilise la mise à jour et les parcours qui protègent une dictée jusqu’à son
insertion finale.

- Mise à jour transactionnelle avec reprise du téléchargement et restauration automatique de la
  version précédente si la nouvelle application ne démarre pas correctement.
- Dictées et réunions mieux protégées contre les interruptions, workers bloqués et insertions
  incomplètes.
- Journal audio allégé sans réduire la récupération après un arrêt brutal.
- Intégrations Mistral, ElevenLabs et Soniox alignées sur leurs API actuelles, avec nettoyage des
  ressources distantes temporaires.
- Apparence Nova disponible comme aperçu facultatif et entièrement réversible.

## Téléchargements

- Apple Silicon : `Aria-2.51.0-Apple-Silicon.dmg`
- Intel : `Aria-2.51.0-Intel.dmg`

Chaque DMG possède un fichier `.sha256` associé. Cette bêta conserve l’identité Apple de la
version 2.50.0 afin de préserver les autorisations lors de la mise à jour. Elle n’est pas encore
notarisée avec Developer ID : l’avertissement macOS reste attendu lors d’une première installation.
