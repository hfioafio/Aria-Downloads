# Cartes de partage (Open Graph)

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
