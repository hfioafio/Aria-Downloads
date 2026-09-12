#!/usr/bin/env python3
"""Génère les pages de contenu du site Aria à partir d'un gabarit commun.

Chaque page est décrite dans PAGES ; son corps HTML vit dans tools/pages/<slug>.html.
Lancer : python3 tools/build_pages.py  (depuis la racine du dépôt)
"""
import datetime, io, json, os, re, sys

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
  <meta property="og:image" content="{base}{ogimage}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{base}{ogimage}">
  <link rel="icon" href="favicon.png" sizes="96x96">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
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
{related}    </div>
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
         description="Wispr Flow Pro is $15 a month. Aria does system-wide Mac dictation offline, same 2,000 free words a week, and Pro is €5 once. Side by side.",
         crumb="Wispr Flow alternative", pair="alternative-wispr-flow"),
    dict(slug="alternative-wispr-flow", lang="fr",
         title="Alternative à Wispr Flow sur Mac : 5 € une fois",
         description="Wispr Flow Pro coûte 15 $ par mois et passe par le cloud. Aria dicte hors ligne sur votre Mac, mêmes 2 000 mots gratuits par semaine, Pro à 5 € une fois.",
         crumb="Alternative à Wispr Flow", pair="wispr-flow-alternative"),
    dict(slug="mac-dictation-no-subscription", lang="en",
         title="Mac Dictation With No Subscription — €5 Once",
         description="Most Mac dictation apps want a monthly fee or $30 to $250 up front. Aria is free up to 2,000 words a week and €5 once for unlimited. Real prices compared.",
         crumb="No subscription", pair="dictee-vocale-mac-sans-abonnement"),
    dict(slug="dictee-vocale-mac-sans-abonnement", lang="fr",
         title="Dictée vocale Mac sans abonnement : 5 € une fois",
         description="La plupart des apps de dictée sur Mac exigent un abonnement mensuel. Aria est gratuite jusqu'à 2 000 mots par semaine, puis 5 € une seule fois.",
         crumb="Sans abonnement", pair="mac-dictation-no-subscription"),
    dict(slug="superwhisper-alternative", lang="en",
         title="Superwhisper Alternative: Local Dictation, €5 Once",
         description="Superwhisper Pro is $8.49 a month. Aria runs the same kind of local model on your Mac for €5 once, with a free tier of 2,000 words a week.",
         crumb="Superwhisper alternative", pair="alternative-superwhisper"),
    dict(slug="transcribe-audio-file-mac", lang="en",
         title="Transcribe an Audio File on Mac, Offline",
         description="Drop an MP3, M4A, WAV or MP4 into Aria and get the text back, without uploading anything. Speaker labels included, and it works with no internet.",
         crumb="Transcribe a file", pair="transcrire-fichier-audio-mac"),
    dict(slug="transcrire-fichier-audio-mac", lang="fr",
         title="Transcrire un fichier audio sur Mac, hors ligne",
         description="Déposez un MP3, M4A, WAV ou MP4 dans Aria et récupérez le texte, sans rien téléverser. Locuteurs identifiés, et ça marche sans connexion.",
         crumb="Transcrire un fichier", pair="transcribe-audio-file-mac"),
    dict(slug="voice-typing-for-developers", lang="en",
         title="Voice Typing for Developers on a Mac",
         description="Dictating prose beats typing it, even for people who type fast. What works in an editor, a terminal and a pull request — and what does not.",
         crumb="For developers", pair=None),
    dict(slug="install-aria-mac", lang="en",
         title="Installing Aria on macOS: the Gatekeeper Step",
         description="macOS says it cannot verify the developer, or that the app is damaged. What each message means, and how to open Aria safely.",
         crumb="Installing Aria", pair="installer-aria-mac"),
    dict(slug="installer-aria-mac", lang="fr",
         title="Installer Aria sur macOS : l'étape Gatekeeper",
         description="macOS ne peut pas vérifier le développeur, ou dit l'app endommagée. Ce que ces messages veulent dire, comment ouvrir Aria, et vérifier le fichier.",
         crumb="Installer Aria", pair="install-aria-mac"),
    dict(slug="offline-dictation-mac", lang="en",
         title="Offline Dictation for Mac — No Cloud, No Account",
         description="Hold a key, talk, and the sentence lands in Mail, Slack or Notes. Nothing leaves your Mac. Free up to 2,000 words a week, €5 once for unlimited.",
         crumb="Offline dictation", pair="dictee-vocale-mac-hors-ligne"),
    dict(slug="best-dictation-apps-mac", lang="en",
         title="Best Dictation Apps for Mac in 2026, Compared",
         description="Six Mac dictation apps compared on real prices, offline support and languages — by the developer of one of them, including where it loses.",
         crumb="Best dictation apps", pair="dictee-vocale-mac"),
    dict(slug="alternative-superwhisper", lang="fr",
         title="Alternative à Superwhisper : locale, 5 € une fois",
         description="Superwhisper Pro coûte 8,49 $ par mois. Aria fait tourner le même type de modèle local sur votre Mac pour 5 € une fois, 2 000 mots gratuits par semaine.",
         crumb="Alternative à Superwhisper", pair="superwhisper-alternative"),
    dict(slug="meeting-transcription-mac", lang="en",
         title="Transcribe a Meeting on Mac, With Speaker Names",
         description="Turn a meeting recording into a transcript with each speaker labelled, entirely on your Mac. No bot in the call, no account, no upload.",
         crumb="Meeting transcription", pair="transcrire-reunion-mac"),
    dict(slug="transcrire-reunion-mac", lang="fr",
         title="Transcrire une réunion sur Mac, hors ligne",
         description="Transformez l'enregistrement d'une réunion en transcription avec chaque locuteur identifié, entièrement sur votre Mac. Aucun bot, aucun compte.",
         crumb="Transcrire une réunion", pair="meeting-transcription-mac"),
    dict(slug="apple-dictation-alternative", lang="en",
         title="Apple Dictation Not Working? Fixes, Then Options",
         description="Missing punctuation, accuracy that collapses, dictation that stops on its own: real fixes for macOS dictation, and what to use instead.",
         crumb="Apple Dictation", pair=None),
    dict(slug="parakeet-mac", lang="en",
         title="NVIDIA Parakeet on Mac: Offline Dictation App",
         description="Run NVIDIA Parakeet TDT V3 locally on Apple Silicon for dictation into any app. No Python, no install script, no cloud. Free up to 2,000 words a week.",
         crumb="Parakeet on Mac", pair=None),
    dict(slug="macwhisper-alternative", lang="en",
         title="MacWhisper Alternative for Live Mac Dictation",
         description="MacWhisper Pro is €64 and built around audio files. Aria does live dictation into any app plus file transcription, for €5 once. Honest comparison.",
         crumb="MacWhisper alternative", pair=None),
    dict(slug="dictee-vocale-mac-hors-ligne", lang="fr",
         title="Dictée vocale Mac hors ligne : ce qui marche",
         description="Dicter sur Mac sans connexion et sans compte : la dictée d'Apple, Whisper en local, Parakeet. Ce que chacune sait faire, et où elle s'arrête.",
         crumb="Dictée hors ligne", pair="offline-dictation-mac"),
    dict(slug="dictee-vocale-mac", lang="fr",
         title="Dictée vocale Mac : quelle app choisir en 2026",
         description="Comparatif des apps de dictée vocale sur Mac en 2026 : dictée d'Apple, Wispr Flow, Superwhisper, MacWhisper, Aria. Prix réels, hors ligne, langues.",
         crumb="Dictée vocale sur Mac", pair="best-dictation-apps-mac"),
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
            # x-default désigne la version servie à qui ne parle ni français ni anglais.
            # Sans lui, le moteur choisit seul, et son choix change d'un pays à l'autre.
            default = p["slug"] if lang == "en" else p["pair"]
            alt = (f'  <link rel="alternate" hreflang="{lang}" href="{BASE}{p["slug"]}.html">\n'
                   f'  <link rel="alternate" hreflang="{other}" href="{BASE}{p["pair"]}.html">\n'
                   f'  <link rel="alternate" hreflang="x-default" href="{BASE}{default}.html">\n')
        # Le FAQPage est déduit des blocs <details> du corps : une seule source de vérité.
        pairs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", body, re.S)
        # Fil d'Ariane : Google s'en sert pour afficher le chemin sous le titre du résultat.
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Aria",
             "item": BASE if lang == "fr" else BASE + "en.html"},
            {"@type": "ListItem", "position": 2, "name": p["crumb"],
             "item": BASE + p["slug"] + ".html"}]}
        jsonld = ('  <script type="application/ld+json">\n    '
                  + json.dumps(crumbs, ensure_ascii=False) + "\n  </script>\n")
        if pairs:
            strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
            data = {"@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": strip(q),
                                    "acceptedAnswer": {"@type": "Answer", "text": strip(a)}}
                                   for q, a in pairs]}
            jsonld += ('  <script type="application/ld+json">\n    '
                       + json.dumps(data, ensure_ascii=False) + "\n  </script>\n")
        siblings = [q for q in PAGES if q["lang"] == lang and q["slug"] != p["slug"]]
        related = ""
        if siblings:
            heading = "À lire aussi" if lang == "fr" else "Read next"
            items = "".join(
                '          <a href="%s.html">%s</a>\n' % (q["slug"], q["crumb"])
                for q in siblings[:8])
            related = ('      <section class="related" aria-label="%s">\n'
                       '        <h2>%s</h2>\n        <div class="related-links">\n%s'
                       '        </div>\n      </section>\n') % (heading, heading, items)

        html = TEMPLATE.format(
            lang=lang, title=p["title"], description=p["description"], base=BASE, slug=p["slug"],
            alternates=alt, jsonld=jsonld, oglocale="fr_FR" if lang == "fr" else "en_US",
            body=body, related=related, crumb=p["crumb"], homehref="./" if lang == "fr" else "en.html",
            ogimage="og-image.png" if lang == "fr" else "og-image-en.png",
            otherlang="en" if lang == "fr" else "fr",
            dlanchor="telecharger" if lang == "fr" else "download",
            privanchor="confidentialite" if lang == "fr" else "privacy", **loc)
        out = os.path.join("docs", p["slug"] + ".html")
        io.open(out, "w", encoding="utf-8").write(html)
        written.append(out)
    return written

def sitemap():
    """Le sitemap est déduit de PAGES : il ne peut pas diverger des pages réellement produites."""
    today = datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    def block(loc, alts, prio):
        out.append("  <url>")
        out.append(f"    <loc>{loc}</loc>")
        for hl, href in alts:
            out.append(f'    <xhtml:link rel="alternate" hreflang="{hl}" href="{href}"/>')
        out.append(f"    <lastmod>{today}</lastmod>")
        out.append("    <changefreq>weekly</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        out.append("  </url>")

    home = [("fr", BASE), ("en", BASE + "en.html"), ("x-default", BASE + "en.html")]
    block(BASE, home, "1.0")
    block(BASE + "en.html", home, "1.0")
    for p in PAGES:
        alts = []
        if p.get("pair"):
            other = "en" if p["lang"] == "fr" else "fr"
            default = p["slug"] if p["lang"] == "en" else p["pair"]
            alts = [(p["lang"], BASE + p["slug"] + ".html"), (other, BASE + p["pair"] + ".html"),
                    ("x-default", BASE + default + ".html")]
        block(BASE + p["slug"] + ".html", alts, "0.8" if p.get("pair") else "0.7")
    out.append("</urlset>")
    io.open(os.path.join("docs", "sitemap.xml"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(PAGES) + 2


if __name__ == "__main__":
    for f in build():
        print("écrit", f)
    print("sitemap.xml :", sitemap(), "URL")
