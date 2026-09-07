#!/usr/bin/env python3
"""Génère les pages de contenu du site Aria à partir d'un gabarit commun.

Chaque page est décrite dans PAGES ; son corps HTML vit dans tools/pages/<slug>.html.
Lancer : python3 tools/build_pages.py  (depuis la racine du dépôt)
"""
import io, json, os, re, sys

BASE = "https://hfioafio.github.io/Aria-Downloads/"
VERSION = "2.60.3"
DMG_ARM = f"https://github.com/hfioafio/Aria-Downloads/releases/download/v{VERSION}/Aria-{VERSION}-Apple-Silicon.dmg"
DMG_X64 = f"https://github.com/hfioafio/Aria-Downloads/releases/download/v{VERSION}/Aria-{VERSION}-Intel.dmg"

L = {
    "fr": dict(home="Accueil", nav_dl="Télécharger", other="EN", other_href="en.html",
               f_home="Accueil", f_privacy="Confidentialité", f_dl="Télécharger",
               tagline="Dictée et transcription pour macOS.", skip="Aller au contenu",
               dl_arm="Télécharger pour Apple Silicon", dl_x64="Mac Intel"),
    "en": dict(home="Home", nav_dl="Download", other="FR", other_href="./",
               f_home="Home", f_privacy="Privacy", f_dl="Download",
               tagline="Voice dictation and transcription for macOS.", skip="Skip to content",
               dl_arm="Download for Apple Silicon", dl_x64="Intel Mac"),
}

TEMPLATE = """<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f6f6f3">
  <meta name="color-scheme" content="light dark">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{base}{slug}.html">
{alternates}  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Aria">
  <meta property="og:locale" content="{oglocale}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{base}{slug}.html">
  <meta property="og:image" content="{base}aria-setup-preview.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{base}aria-setup-preview.png">
  <link rel="icon" href="favicon.png">
  <link rel="stylesheet" href="pages.css">
{jsonld}  <script>
    (function () {{
      var choice = 'auto';
      try {{ choice = localStorage.getItem('aria-site-theme') || 'auto'; }} catch (_) {{}}
      if (['auto','light','dark'].indexOf(choice) < 0) choice = 'auto';
      var dark = choice === 'dark' || (choice === 'auto' && matchMedia('(prefers-color-scheme:dark)').matches);
      document.documentElement.dataset.theme = dark ? 'dark' : 'light';
      document.querySelector('meta[name="theme-color"]').content = dark ? '#08090b' : '#f6f6f3';
    }})();
  </script>
</head>
<body>
  <a class="skip" href="#content">{skip}</a>
  <nav class="nav">
    <div class="shell nav-in">
      <a class="brand" href="{homehref}"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>Aria</a>
      <div class="nav-links">
        <a href="{homehref}">{home}</a>
        <a href="{other_href}" hreflang="{otherlang}">{other}</a>
        <a class="button" href="{homehref}#{dlanchor}">{nav_dl}</a>
      </div>
    </div>
  </nav>
  <main id="content">
    <div class="shell">
      <p class="crumb"><a href="{homehref}">Aria</a> · {crumb}</p>
{body}
    </div>
  </main>
  <footer>
    <div class="shell footer-in">
      <a class="brand" href="{homehref}"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>Aria</a>
      <span>{tagline}</span>
      <div class="footer-links">
        <a href="{homehref}">{f_home}</a>
        <a href="{homehref}#{privanchor}">{f_privacy}</a>
        <a href="{other_href}" hreflang="{otherlang}">{other}</a>
        <a href="{homehref}#{dlanchor}">{f_dl}</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""

PAGES = [
    dict(slug="wispr-flow-alternative", lang="en",
         title="Wispr Flow Alternative for Mac — Offline, €5 Once",
         description="Wispr Flow Pro is $15 a month. Aria does system-wide Mac dictation offline, with the same 2,000 free words a week, and Pro is €5 once. Side-by-side comparison.",
         crumb="Wispr Flow alternative", pair="alternative-wispr-flow"),
    dict(slug="alternative-wispr-flow", lang="fr",
         title="Alternative à Wispr Flow sur Mac : 5 € une fois",
         description="Wispr Flow Pro coûte 15 $ par mois et passe par le cloud. Aria dicte hors ligne sur votre Mac, avec les mêmes 2 000 mots gratuits par semaine, et Pro est à 5 € une seule fois.",
         crumb="Alternative à Wispr Flow", pair="wispr-flow-alternative"),
    dict(slug="mac-dictation-no-subscription", lang="en",
         title="Mac Dictation With No Subscription — €5 Once",
         description="Most Mac dictation apps want a monthly fee or $30 to $250 up front. Aria is free up to 2,000 words a week and €5 once for unlimited. Real prices compared.",
         crumb="No subscription", pair="dictee-vocale-mac-sans-abonnement"),
    dict(slug="dictee-vocale-mac-sans-abonnement", lang="fr",
         title="Dictée vocale Mac sans abonnement : 5 € une fois",
         description="La plupart des apps de dictée sur Mac exigent un abonnement mensuel ou 30 à 250 € d'un coup. Aria est gratuite jusqu'à 2 000 mots par semaine, puis 5 € une seule fois.",
         crumb="Sans abonnement", pair="mac-dictation-no-subscription"),
    dict(slug="superwhisper-alternative", lang="en",
         title="Superwhisper Alternative: Local Dictation, €5 Once",
         description="Superwhisper Pro is $8.49 a month. Aria runs the same kind of local model on your Mac — Parakeet, Whisper — for €5 once, with a free tier of 2,000 words a week.",
         crumb="Superwhisper alternative", pair=None),
    dict(slug="dictee-vocale-mac", lang="fr",
         title="Dictée vocale Mac : quelle app choisir en 2026",
         description="Comparatif des applications de dictée vocale sur Mac en 2026 : dictée d'Apple, Wispr Flow, Superwhisper, MacWhisper, Aria. Prix réels, hors ligne ou non, langues.",
         crumb="Dictée vocale sur Mac", pair=None),
]

def build():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    written = []
    for p in PAGES:
        lang = p["lang"]; loc = L[lang]
        src = os.path.join("tools", "pages", p["slug"] + ".html")
        body = io.open(src, encoding="utf-8").read().rstrip("\n")
        loc = dict(loc)
        if p.get("pair"):
            loc["other_href"] = p["pair"] + ".html"
        alt = ""
        if p.get("pair"):
            other = "en" if lang == "fr" else "fr"
            alt = (f'  <link rel="alternate" hreflang="{lang}" href="{BASE}{p["slug"]}.html">\n'
                   f'  <link rel="alternate" hreflang="{other}" href="{BASE}{p["pair"]}.html">\n')
        # Le FAQPage est déduit des blocs <details> du corps : une seule source de vérité.
        pairs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", body, re.S)
        jsonld = ""
        if pairs:
            strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
            data = {"@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": strip(q),
                                    "acceptedAnswer": {"@type": "Answer", "text": strip(a)}}
                                   for q, a in pairs]}
            jsonld = ('  <script type="application/ld+json">\n    '
                      + json.dumps(data, ensure_ascii=False) + "\n  </script>\n")
        html = TEMPLATE.format(
            lang=lang, title=p["title"], description=p["description"], base=BASE, slug=p["slug"],
            alternates=alt, jsonld=jsonld, oglocale="fr_FR" if lang == "fr" else "en_US",
            body=body, crumb=p["crumb"], homehref="./" if lang == "fr" else "en.html",
            otherlang="en" if lang == "fr" else "fr",
            dlanchor="telecharger" if lang == "fr" else "download",
            privanchor="confidentialite" if lang == "fr" else "privacy", **loc)
        out = os.path.join("docs", p["slug"] + ".html")
        io.open(out, "w", encoding="utf-8").write(html)
        written.append(out)
    return written

if __name__ == "__main__":
    for f in build():
        print("écrit", f)
