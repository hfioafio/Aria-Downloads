# Aria pour macOS — téléchargements officiels

Ce dépôt public contient uniquement les versions compilées d’Aria pour macOS, leurs empreintes
SHA-256 et le manifeste de mise à jour. Le code source, les clés API et les données utilisateur
n’y sont pas publiés.

## Télécharger

- Apple Silicon (M1, M2, M3, M4 et suivants) : voir la dernière release et choisir
  `Aria-…-Apple-Silicon.dmg`.
- Intel : voir la dernière release et choisir `Aria-…-Intel.dmg`.

Page officielle : https://hfioafio.github.io/Aria-Downloads/

## Première ouverture de la bêta

La bêta actuelle n’est pas encore notarisée par Apple. Après avoir glissé Aria dans Applications,
ouvrez **Réglages Système → Confidentialité et sécurité**, puis cliquez sur **Ouvrir quand même**.
Cette étape disparaîtra lorsque la distribution Developer ID sera activée.

## Mises à jour

Aria vérifie ce dépôt au démarrage puis toutes les six heures. Avant d’ouvrir une mise à jour,
l’application vérifie son architecture, son nom de version, sa taille et son empreinte SHA-256.
Tant que la bêta n’est pas signée Developer ID, macOS demande de quitter Aria puis de glisser la
nouvelle version dans Applications. Le téléchargement et les mises à jour restent gratuits.

## Confidentialité

Les clés API restent dans le Trousseau macOS et les données de l’application restent sur le Mac.
Avec un modèle local, aucun audio n’est transmis à un fournisseur de transcription. Avec un modèle
API, seul l’audio à transcrire est envoyé au fournisseur choisi par l’utilisateur.

Copyright © 2026 — Tous droits réservés.
