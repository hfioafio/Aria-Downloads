# Aria 2.51.1

Correctif qui renforce les validations du canal de mise à jour transactionnel introduit dans
Aria 2.51.

- confirmation du bon fonctionnement de l’interface (processus de rendu) après le redémarrage ;
- la sauvegarde de l’ancienne version n’est supprimée qu’une fois le démarrage confirmé ;
- restauration automatique de l’ancienne version si l’interface ne démarre pas ou si la
  vérification finale de la signature échoue ;
- reprend toutes les améliorations de la 2.51.0 : dictée, réunions, journal audio, fournisseurs
  et aperçu Nova.

Les DMG Apple Silicon et Intel sont signés avec l’identité Apple stable d’Aria et contrôlés par
taille et SHA-256 avant installation. Cette bêta publique n’est pas encore notarisée.
