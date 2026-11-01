# Cartes de partage (Open Graph)

La vitrine utilise désormais les visuels existants `docs/aria-video-fr.jpg` et
`docs/aria-video-en.jpg` (1280 × 720), issus de ses présentations animées. Ils ne
présentent pas le tarif Pro comme une offre déjà ouverte. Les métadonnées des
accueils et le générateur d’articles pointent vers ces deux fichiers.

Les cartes ci-dessous sont les sources historiques ; leurs PNG restent disponibles
pour les anciens liens, mais ne sont plus les images de partage de la vitrine.

`card-fr.html` et `card-en.html` produisent `docs/og-image.png` et `docs/og-image-en.png`,
les images affichées quand un lien Aria est collé sur Reddit, Hacker News, X, LinkedIn,
Slack ou Discord. Format imposé par ces plateformes : **1200 × 630**.

Régénérer après une modification :

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=2 --window-size=1200,630 \
  --screenshot=/tmp/og.png --virtual-time-budget=2500 file://$PWD/tools/og/card-fr.html
sips -Z 1200 /tmp/og.png --out docs/og-image.png
```

Le rendu se fait à 2× puis est réduit à 1200 px : le texte reste net et le fichier
descend sous 250 Ko, là où un export direct dépassait 850 Ko.
