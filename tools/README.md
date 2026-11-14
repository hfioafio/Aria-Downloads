# Génération des pages du site

`build_pages.py` produit `docs/*.html` à partir des fragments de `pages/` et d'un gabarit unique.
Modifier un fragment, jamais le HTML produit, puis relancer :

```
python3 tools/build_pages.py
python3 tools/check_site.py
```

Le sitemap est régénéré depuis la même liste de pages. Les dates des pages inchangées sont
conservées. Les FAQ des deux accueils sont alignées sur leurs réponses visibles ; celles des
articles sont déduites de leurs fragments, avec décodage des caractères HTML.

Le générateur pose aussi les espaces insécables du français (avant « ? ! ; : », dans « 2 000 »,
devant « € ») sur les fragments FR, `index.html`, `404.html` et `stats.html` : écrire avec des
espaces ordinaires, la sortie est corrigée.

Le contrôle vérifie les fichiers et ancres liés, les URL canoniques, les traductions, le sitemap,
les FAQ structurées, l’offre gratuite et les liens Installer, ainsi que la chaîne de
téléchargement : chaque DMG proposé a son `.sha256` au même nom, `softwareVersion` et la page
de version suivent les liens, `updates/preview.json` annonce la version du site, le README
pointe vers la même version. Il refuse les chemins relatifs dans `404.html` (servie pour des URL
imbriquées) et les tableaux défilants sans `tabindex`. Les identifiants de playlist YouTube de
forme inhabituelle sont signalés en avertissement, sans bloquer. Après déploiement GitHub Pages :

```
python3 tools/check_site.py --live
```

Cette option compare les 26 pages indexables et les ressources communes réellement servies aux
fichiers validés, puis vérifie que les deux fichiers `.sha256` proposés aux visiteurs portent
l’empreinte du manifeste de mise à jour. Elle ne télécharge aucun DMG et ne mesure pas des
installations. Vérifier aussi
le rendu et les interactions dans un navigateur quand celui-ci est disponible.

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
