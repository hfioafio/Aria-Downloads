# Génération des pages du site

`build_pages.py` produit `docs/*.html` à partir des fragments de `pages/` et d'un gabarit unique.
Modifier un fragment, jamais le HTML produit, puis relancer :

```
python3 tools/build_pages.py
```

Le sitemap est régénéré au passage depuis la même liste de pages : il ne peut pas diverger.

## Règle à ne pas casser : aucune version figée dans les pages de contenu

Les boutons des pages de comparaison renvoient vers la section de téléchargement des deux
accueils (`./#telecharger` et `en.html#download`), jamais vers une URL de DMG.

La raison est concrète : une automatisation met à jour les liens de `index.html` et `en.html` à
chaque nouvelle version. Le 11 septembre 2026, les accueils proposaient la 2.60.5-preview.94
pendant que quinze pages de comparaison offraient encore la 2.60.3 du 5 septembre — c'est-à-dire
que les pages censées accueillir les visiteurs servaient une version périmée. Une seule source de
vérité règle le problème définitivement.

Pour la même raison, un bouton qui mène à cette section ne doit pas promettre une architecture :
il dit « Télécharger Aria », pas « Télécharger pour Apple Silicon ». Le choix Apple Silicon ou
Intel se fait dans la section, qui porte aussi les empreintes SHA-256 et la marche à suivre au
premier lancement.

## Cartes de partage

Voir `og/README.md`.
