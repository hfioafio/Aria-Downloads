# Passation — branche `claude/amelioration-2026-11-21`

- **Date :** 21 novembre 2026, 12 h 41 (heure de Paris)
- **Agent :** Claude Code (cloud), modèle Opus 5.5
- **Base :** `main` à `00e703f` ; aucune fusion, aucune PR, aucune version publiée.

## Ce qui a été fait

**Site (`docs/`, généré par `tools/build_pages.py`)**
- Bouton « Auto » du choix d’apparence : son nom accessible commence par le texte visible
  (WCAG 2.5.3), sur `index.html` et `en.html`.
- `stats.html` : gris secondaire assombri (contraste 3,75:1 → 4,9:1), tableau défilant
  atteignable au clavier (`tabindex="0"`, `role="region"`, nom accessible).
- Apostrophe typographique du français posée par le générateur (fragments FR, accueil, 404,
  titres, descriptions et fils d’Ariane FR). Le contenu des balises `script`, `style`, `code`
  et `pre` n’est pas touché.
- Quelques tournures françaises corrigées dans les fragments (`tools/pages/`).

**Outils**
- `check_site.py` : contrôle aussi la langue, le titre, la meta description, l’attribut `alt`
  des images et la validité du JSON-LD ; signale les titres et descriptions de longueur
  inhabituelle. Faux positif supprimé : les identifiants courts de playlist YouTube
  (PL + 11 caractères) sont valides.
- `adoption_stats.mjs` : délai maximal par appel à l’API, écriture atomique, détection « rc »
  plus stricte, fonctions importables sans lancer le relevé.
- `build_pages.py` : import inutilisé retiré.

**Documentation**
- README : noms de DMG affichés identiques aux fichiers liés, section française complétée
  (mises à jour, confidentialité, guide d’installation), description fidèle du contenu du dépôt.
- Notes de version 2.48.0, 2.51.0 et 2.51.1 : anglicismes remplacés, sens inchangé.

Non modifiés : `updates/`, fichiers `.sha256`, URL de téléchargement, workflow GitHub Actions,
fichiers binaires.

## Ce qui a été testé

- `python3 tools/build_pages.py` puis `python3 tools/check_site.py` : OK, sans avertissement.
- Playwright (Chromium) sur les 28 pages, en 390 × 844 et 1440 × 900, thèmes clair et sombre :
  aucune erreur de console ni de requête, aucun débordement horizontal, axe-core
  (WCAG 2.0/2.1/2.2 A et AA, bonnes pratiques) sans violation. Captures relues.
- `stats.html` testée avec des réponses GitHub simulées (39 versions réelles, historique réel) :
  rendu correct, aucune erreur, axe sans violation.
- Navigation au clavier (Tab) sur les accueils, une page d’article, la 404 et les stats : focus
  visible partout (la vidéo utilise les contrôles natifs du navigateur).
- Performance locale : environ 150 Ko transférés sur les accueils, 22 Ko sur les articles,
  LCP sur le titre, CLS nul.
- Liens externes (14) vérifiés : tous répondent ; `issues/new` renvoie 403 sans session GitHub,
  ce qui est normal. Les deux playlists YouTube ouvrent bien les vidéos Aria.
- Vidéos de présentation : piste audio musicale sans parole détectée, donc pas de sous-titres
  nécessaires.
- `adoption_stats.mjs` rejoué hors ligne (`STATS_RELEASES_FILE`) : même instantané que le dernier
  relevé du workflow. Scripts du workflow passés à `shellcheck` : aucun avertissement.

## Suite possible

- Après fusion et déploiement : `python3 tools/check_site.py --live`.
- Les fragments EN gardent l’apostrophe droite, usage courant en anglais ; à uniformiser
  seulement si on le souhaite.
- La date `lastmod` du sitemap n’est mise à jour que pour les pages réécrites par le générateur ;
  une modification manuelle de `index.html` ou `en.html` ne la change pas.

---

## Relecture indépendante — 21/11/2026, 15 h 08 (heure de Paris)

- **Agent :** Claude Code (cloud), modèle Opus 5.5, réflexion standard. Relecture des 4 commits
  ci-dessus, sans fusion ni PR.

**Vérifié, sans correction nécessaire**
- `build_pages.py` : l’apostrophe typographique ne touche que du texte entre balises des pages FR
  (et les titres, descriptions et fils d’Ariane FR de `PAGES`). Comparaison avec `00e703f` : aucun
  attribut de fragment, aucune URL, aucun bloc `script`/`style`/`code`/`pre` modifié ; pages EN et
  `en.html` intactes (seul le bouton « Auto » y change). Tous les remplacements sont des élisions
  françaises (l’, d’, qu’, jusqu’…). Le JSON-LD reprend simplement le texte visible, et reste valide.
- Génération idempotente : relancer `build_pages.py` ne modifie plus rien.
- Validateur HTML (vnu via `html5validator`) : mêmes erreurs qu’avant la branche, toutes
  antérieures. Les fichiers de vérification Google n’ont pas de doctype (normal, à ne pas toucher) ;
  le `<style>` du bloc `install-dialog:start/end` est dans `<body>` sur les deux accueils. Ce bloc
  est délimité par des marqueurs, sans doute réinjecté par l’outil de publication : laissé en place.
  Une fois déplacé dans `<head>` (copie de test), aucune autre erreur n’apparaît.
- Liens du README et des notes : tous répondent (les DMG et `.sha256` en GET).

**Corrigé**
- `stats.html` : vert du thème clair `#1d8a4e` → `#187a45`. Le texte « +2 depuis le 16 nov. »
  (13 px) n’avait que 4,37:1 sur blanc ; axe le signalait en 390 et 1440 avec les données réelles.
  Nouveau contraste : 5,4:1 sur blanc, 4,7:1 sur le fond secondaire.
- Notes 2.51.1 : retour au sens d’origine. « Correctif qui renforce les validations » devenait une
  promesse plus large que « Correctif de validation » ; « après le redémarrage » perdait le sujet
  (celui du processus de rendu) ; « toutes les améliorations » ajoutait « toutes ».
- README FR, confidentialité : ajout de deux phrases présentes en anglais et absentes en français
  (relais au débit limité, compteurs pseudonymes et bornés pour le quota ; statistiques détaillées
  désactivées par défaut). Sans elles, la version française promettait plus que l’anglaise.

**Testé**
- `python3 tools/build_pages.py` puis `python3 tools/check_site.py` : OK.
- Playwright (Chromium) sur les 28 pages, 390 et 1440 px, clair et sombre, axe-core (WCAG 2.0 à
  2.2 A/AA + bonnes pratiques) : aucune violation, aucun débordement horizontal. La 404 doit être
  servie sous `/Aria-Downloads/` (chemins absolus) pour être testée correctement.

**Suite**
- Inchangé : `check_site.py --live` après déploiement.

---

## Relecture des textes anglais — 21/11/2026, 15 h 15 (heure de Paris)

- **Agent :** Claude Code (cloud), modèle Opus 5.5, réflexion standard.

**Fait**
- Relu les 12 pages EN (`tools/pages/*.html`), `en.html` et la partie anglaise du README. Pas de
  notes de version EN (les trois fichiers sont en français). Orthographe britannique cohérente
  (licence, notarised, recognise).
- Promesses ramenées au vrai : « Nothing leaves the Mac » (dictée hors ligne) → « Keep speech
  processing on your Mac », et côté FR « Dicter sans que rien ne parte » → « Garder le traitement
  de la voix sur le Mac » (le quota et le mode Automatique passent par le réseau) ; titre réunion
  « with speaker names » → « with speaker labels » (la FAQ dit qu’Aria n’identifie pas les vrais
  noms) ; dictée Apple « built in and offline » → hors ligne sur Apple Silicon une fois la langue
  téléchargée (EN et FR) ; README EN « No network, no upload » → pas d’envoi d’audio, connexion
  possible pour le quota.
- Anglais plus naturel : « restores a capital or a full stop » → « adds capitals and full
  stops » (Superwhisper, développeurs, `en.html`, et FR développeurs aligné) ; lede hors ligne
  réécrit ; « a membership of » → « membership of » ; deux h2 presque identiques sur la page
  MacWhisper ; « optional » ajouté aux locuteurs (comme en FR).
- Parité EN/FR : section « Fidèle par défaut » ajoutée à `alternative-superwhisper` (présente
  seulement en EN) ; section « Help » ajoutée au README EN (présente seulement en FR).
- `sitemap.xml` : `lastmod` de `en.html` mis au 21/11 à la main (le générateur le conserve).

**Vérifié sans correction**
- Titres ≤ 60 caractères et descriptions 110–160 sur les 24 pages générées.
- canonical = og:url = hreflang de soi sur les 26 pages indexables ; hreflang réciproques et
  x-default identiques dans chaque paire ; sitemap = mêmes 26 URL et mêmes alternates ; tous les
  JSON-LD se lisent (SoftwareApplication, FAQPage, VideoObject, BreadcrumbList) ; FAQ EN/FR des
  accueils : mêmes 10 questions, mêmes faits. robots.txt inchangé (commentaire exact).

**Testé**
- `build_pages.py` puis `check_site.py` : OK (30 fichiers, 26 indexables, 905 références).
- Playwright Chromium, 27 pages (hors stats, non modifiée), 390 et 1440, clair et sombre,
  axe-core WCAG 2.0–2.2 A/AA + bonnes pratiques : aucune violation, aucune erreur, aucun
  débordement.

**Suite**
- Les paires `offline-dictation-mac` / `dictee-vocale-mac-hors-ligne` et
  `best-dictation-apps-mac` / `dictee-vocale-mac` ne sont pas des traductions : plan et contenu
  différents (la FR compare Apple, Whisper et Aria ; l’EN décrit Aria seul). Aucune promesse en
  plus d’un côté, mais à harmoniser si l’on veut deux versions jumelles.
- « Then keep Aria for life » / « Puis gardez Aria à vie » (accueils) : promesse forte alors que
  Pro n’est pas en vente ; le paragraphe suivant le précise. À reformuler si souhaité.
- Inchangé : `check_site.py --live` après déploiement.

---

## Promesse « à vie » reformulée — 21/11/2026, 15 h 18 (heure de Paris)

- **Agent :** Claude Code (cloud), modèle Opus 5.5, réflexion standard. Tâche planifiée.

**Fait**
- Accueils, section Pro : « Simple et définitif / Essayez chaque semaine. Puis gardez Aria à vie. »
  → « Simple, sans abonnement / Gratuit chaque semaine. Pro bientôt, en achat unique. » ;
  EN « Simple and final / Try it every week. Then keep Aria for life. » → « Simple, no
  subscription / Free every week. Pro soon, as a one-time purchase. ». L’achat Pro n’étant pas
  ouvert, le titre ne promet plus ce que le paragraphe suivant corrige. Aucun lien ni URL touché.
- `tools/README.md` : apostrophes typographiques dans la prose (code et exemple « l'app » gardés).
- `sitemap.xml` : `lastmod` de l’accueil FR mis au 21/11 à la main (le générateur le conserve).

**Testé**
- `build_pages.py` puis `check_site.py` : OK (30 fichiers, 26 indexables, 905 références).
- Playwright Chromium sur `index.html` et `en.html`, 390 et 1440, clair et sombre, axe-core
  WCAG 2.0–2.2 A/AA + bonnes pratiques : aucune violation, aucune erreur console, aucun
  débordement ; titre et sur-titre lus dans la page.

**Suite**
- Inchangé : harmoniser les paires hors ligne et comparatif EN/FR si souhaité ;
  `check_site.py --live` après déploiement.
