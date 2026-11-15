#!/usr/bin/env python3
"""Génère les pages de contenu du site Aria à partir d'un gabarit commun.

Chaque page est décrite dans PAGES ; son corps HTML vit dans tools/pages/<slug>.html.
Lancer : python3 tools/build_pages.py  (depuis la racine du dépôt)
"""
import datetime, io, json, os, re, sys
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = "https://hfioafio.github.io/Aria-Downloads/"

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

# Politique de sécurité : aucune requête sortante possible (connect-src 'none'), donc aucune
# mesure d'audience, même ajoutée par erreur ; scripts et styles en ligne autorisés (le site en
# dépend), ressources limitées au site. stats.html, qui lit l'API GitHub, n'en a pas.
CSP = """default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'"""

TEMPLATE = """<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="{csp}">
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
  <meta property="og:image:width" content="1280">
  <meta property="og:image:height" content="720">
  <meta property="og:image:alt" content="{imagealt}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{base}{ogimage}">
  <meta name="twitter:image:alt" content="{imagealt}">
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
         title="Wispr Flow Alternative for Mac — Try Local Dictation",
         description="Compare Mac dictation workflows. Aria offers a local engine and 2,000 free words a week in its public beta. Quota checks may require a connection.",
         crumb="Wispr Flow alternative", pair="alternative-wispr-flow"),
    dict(slug="alternative-wispr-flow", lang="fr",
         title="Alternative à Wispr Flow sur Mac : essayer la dictée locale",
         description="Comparez les usages de dictée sur Mac. Aria propose un moteur local et 2 000 mots gratuits par semaine en bêta. Le quota peut nécessiter une connexion.",
         crumb="Alternative à Wispr Flow", pair="wispr-flow-alternative"),
    dict(slug="mac-dictation-no-subscription", lang="en",
         title="Mac Dictation With No Subscription — Free Beta",
         description="Try Mac dictation without a subscription. Aria includes 2,000 free words a week, with local and online engines. Pro purchases are not yet open.",
         crumb="No subscription", pair="dictee-vocale-mac-sans-abonnement"),
    dict(slug="dictee-vocale-mac-sans-abonnement", lang="fr",
         title="Dictée vocale Mac sans abonnement : bêta gratuite",
         description="Essayez la dictée Mac sans abonnement : 2 000 mots gratuits par semaine, moteurs locaux et en ligne. L'achat Aria Pro n'est pas encore ouvert.",
         crumb="Sans abonnement", pair="mac-dictation-no-subscription"),
    dict(slug="superwhisper-alternative", lang="en",
         title="Superwhisper Alternative: Try Local Mac Dictation",
         description="Aria's public beta offers local dictation and 2,000 free words a week. Compare the workflow, quota checks and Mac installation steps.",
         crumb="Superwhisper alternative", pair="alternative-superwhisper"),
    dict(slug="transcribe-audio-file-mac", lang="en",
         title="Transcribe an Audio File on Mac With a Local Engine",
         description="Transcribe audio or video with Aria's local engine. Export TXT, SRT or VTT and optionally identify speakers. Quota checks may need a connection.",
         crumb="Transcribe a file", pair="transcrire-fichier-audio-mac"),
    dict(slug="transcrire-fichier-audio-mac", lang="fr",
         title="Transcrire un fichier audio sur Mac avec un moteur local",
         description="Transcrivez l'audio ou la vidéo sur votre Mac et exportez en TXT, SRT ou VTT. Locuteurs en option ; le quota peut nécessiter une connexion.",
         crumb="Transcrire un fichier", pair="transcribe-audio-file-mac"),
    dict(slug="dictee-apple-ne-fonctionne-pas", lang="fr",
         title="La dictée d'Apple ne marche pas : solutions",
         description="Ponctuation absente, précision qui s'effondre, dictée qui s'arrête seule. Les vraies causes sur macOS, comment les régler, et quoi faire si ça ne suffit pas.",
         crumb="Dictée d'Apple", pair="apple-dictation-alternative"),
    dict(slug="alternative-macwhisper", lang="fr",
         title="Alternative à MacWhisper pour dicter en direct",
         description="Découvrez la dictée au curseur et la transcription de fichiers d'Aria : 2 000 mots gratuits par semaine en bêta, avec un moteur local disponible.",
         crumb="Alternative à MacWhisper", pair="macwhisper-alternative"),
    dict(slug="voice-typing-for-developers", lang="en",
         title="Voice Typing for Developers on a Mac",
         description="Dictate documentation, issues and messages on a Mac with Aria. Where voice input helps in an editor, what to review and why code needs care.",
         crumb="For developers", pair="dictee-vocale-developpeurs"),
    dict(slug="modele-parakeet-mac", lang="fr",
         title="NVIDIA Parakeet sur Mac, sans ligne de commande",
         description="Utilisez NVIDIA Parakeet TDT V3 dans Aria : audio traité sur le Mac après téléchargement du modèle. Le quota et la licence peuvent nécessiter Internet.",
         crumb="Parakeet sur Mac", pair="parakeet-mac"),
    dict(slug="dictee-vocale-developpeurs", lang="fr",
         title="Dictée vocale pour développeurs sur Mac",
         description="Dictez documentation, tickets et messages sur Mac avec Aria. Les usages utiles dans un éditeur, les corrections à vérifier et les limites pour le code.",
         crumb="Pour les développeurs", pair="voice-typing-for-developers"),
    dict(slug="install-aria-mac", lang="en",
         title="Installing Aria on macOS: the Gatekeeper Step",
         description="macOS says it cannot verify the developer, or that the app is damaged. What each message means, and how to open Aria safely.",
         crumb="Installing Aria", pair="installer-aria-mac"),
    dict(slug="installer-aria-mac", lang="fr",
         title="Installer Aria sur macOS : l'étape Gatekeeper",
         description="macOS ne peut pas vérifier le développeur, ou dit l'app endommagée. Ce que ces messages veulent dire, comment ouvrir Aria, et vérifier le fichier.",
         crumb="Installer Aria", pair="install-aria-mac"),
    dict(slug="offline-dictation-mac", lang="en",
         title="Local Dictation for Mac — What Works Offline",
         description="Keep audio processing on your Mac with Aria's local engine. Learn what works offline and when the free quota or licence needs a connection.",
         crumb="Offline dictation", pair="dictee-vocale-mac-hors-ligne"),
    dict(slug="best-dictation-apps-mac", lang="en",
         title="Best Dictation Apps for Mac in 2026, Compared",
         description="Compare Mac dictation workflows, local processing and file transcription. A guide from Aria's team, with links to current vendor plans and limitations.",
         crumb="Best dictation apps", pair="dictee-vocale-mac"),
    dict(slug="alternative-superwhisper", lang="fr",
         title="Alternative à Superwhisper : essayer la dictée locale",
         description="La bêta Aria propose un moteur local et 2 000 mots gratuits par semaine. Comparez les usages, la vérification du quota et l'installation sur Mac.",
         crumb="Alternative à Superwhisper", pair="superwhisper-alternative"),
    dict(slug="meeting-transcription-mac", lang="en",
         title="Transcribe a Meeting on Mac With Speaker Labels",
         description="Transcribe a meeting recording with local audio processing and optional speaker labels. Export TXT, SRT or VTT. Quota checks may need a connection.",
         crumb="Meeting transcription", pair="transcrire-reunion-mac"),
    dict(slug="transcrire-reunion-mac", lang="fr",
         title="Transcrire une réunion sur Mac avec des repères de voix",
         description="Transcrivez une réunion avec un moteur local et des repères de locuteurs facultatifs. Exports TXT, SRT et VTT ; vérification du quota avec connexion.",
         crumb="Transcrire une réunion", pair="meeting-transcription-mac"),
    dict(slug="apple-dictation-alternative", lang="en",
         title="Apple Dictation Not Working? Fixes, Then Options",
         description="Missing punctuation, accuracy that collapses, dictation that stops on its own: real fixes for macOS dictation, and what to use instead.",
         crumb="Apple Dictation", pair="dictee-apple-ne-fonctionne-pas"),
    dict(slug="parakeet-mac", lang="en",
         title="NVIDIA Parakeet on Mac: Offline Dictation App",
         description="Use NVIDIA Parakeet TDT V3 in Aria for on-device Mac dictation after downloading the model. Quota and licence checks may require internet access.",
         crumb="Parakeet on Mac", pair="modele-parakeet-mac"),
    dict(slug="macwhisper-alternative", lang="en",
         title="MacWhisper Alternative for Live Mac Dictation",
         description="Explore Aria's dictation at the cursor and file transcription, with a local engine and 2,000 free words a week in the public beta.",
         crumb="MacWhisper alternative", pair="alternative-macwhisper"),
    dict(slug="dictee-vocale-mac-hors-ligne", lang="fr",
         title="Dictée vocale Mac hors ligne : ce qui marche",
         description="Comprenez la dictée locale sur Mac : audio traité sur l'appareil, téléchargement du modèle et connexion éventuelle pour le quota ou la licence Aria.",
         crumb="Dictée hors ligne", pair="offline-dictation-mac"),
    dict(slug="dictee-vocale-mac", lang="fr",
         title="Dictée vocale Mac : quelle app choisir en 2026",
         description="Comparez les usages de dictée et transcription sur Mac. Guide de l'équipe Aria : traitement local, fichiers, limites et liens vers les offres des éditeurs.",
         crumb="Dictée vocale sur Mac", pair="best-dictation-apps-mac"),
]

NBSP = " "
# Texte entre balises seulement : jamais dans un script, un style, du code ou un attribut.
_SKIP = re.compile(r"(<(script|style|code|pre|textarea)\b.*?</\2>|<[^>]+>)", re.S | re.I)


def french_spacing(html):
    """Espaces insécables du français, pour qu'un « ? » ou un « € » ne parte pas seul à la ligne.

    Sur téléphone, « Comment fonctionne la limite gratuite ? » laissait le point d'interrogation
    seul sur sa ligne, et « Une question ? » faisait de même dans un titre de 76 px. L'espace
    insécable ordinaire (U+00A0) est préféré à l'espace fine : toutes les polices l'ont.
    """
    def fix(text):
        text = re.sub(r"[ \t]+([?!;:»])", NBSP + r"\1", text)
        text = re.sub(r"«[ \t]+", "«" + NBSP, text)
        text = re.sub(r"(?<=\d) (?=\d{3}\b)", NBSP, text)          # 2 000 mots
        text = re.sub(r"(?<=\d) (?=(?:€|%|s\b|Mo\b|Go\b|mots\b|Mac\b))", NBSP, text)
        return text
    parts = _SKIP.split(html)
    out, i = [], 0
    # re.split avec deux groupes renvoie : texte, bloc ignoré, nom de balise, texte, …
    while i < len(parts):
        out.append(fix(parts[i]))
        if i + 1 < len(parts):
            out.append(parts[i + 1])
        i += 3
    return "".join(out)


def sync_french_spacing():
    root = Path(__file__).resolve().parent.parent
    changed = []
    for name in ("index.html", "404.html", "stats.html"):
        path = root / "docs" / name
        before = path.read_text(encoding="utf-8")
        head, sep, body = before.partition("<body")
        after = head + sep + french_spacing(body)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed.append(f"docs/{name}")
    return changed


def faq_entities(body):
    pairs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", body, re.S)
    def text(value):
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", value))).strip()
    return [{"@type": "Question", "name": text(q),
             "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in pairs]


def sync_home_faq():
    """Les réponses visibles font foi pour les données structurées des deux accueils."""
    root = Path(__file__).resolve().parent.parent
    changed = []
    for name in ("index.html", "en.html"):
        path = root / "docs" / name
        before = path.read_text(encoding="utf-8")
        entities = faq_entities(before)
        if not entities:
            raise ValueError(f"{name}: aucune FAQ visible")
        replaced = 0
        def refresh(match):
            nonlocal replaced
            data = json.loads(match.group(1))
            if data.get("@type") != "FAQPage":
                return match.group(0)
            replaced += 1
            data["mainEntity"] = entities
            return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + '</script>'
        after = re.sub(r'<script type="application/ld\+json">(.*?)</script>', refresh, before, flags=re.S)
        if replaced != 1:
            raise ValueError(f"{name}: attendu une FAQ structurée, trouvé {replaced}")
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed.append(f"docs/{name}")
    return changed


def build():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    written = []
    for p in PAGES:
        lang = p["lang"]; loc = L[lang]
        src = os.path.join("tools", "pages", p["slug"] + ".html")
        body = io.open(src, encoding="utf-8").read().rstrip("\n")
        if lang == "fr":
            body = french_spacing(body)
        loc = dict(loc)
        if p.get("pair"):
            loc["other_href"] = p["pair"] + ".html"
        # Une page sans jumelle doit quand même se déclarer : sans hreflang, le seul signal
        # de langue est <html lang>, et l'ensemble hreflang du site paraît incomplet.
        alt = (f'  <link rel="alternate" hreflang="{lang}" href="{BASE}{p["slug"]}.html">\n'
               f'  <link rel="alternate" hreflang="x-default" href="{BASE}{p["slug"]}.html">\n')
        if p.get("pair"):
            other = "en" if lang == "fr" else "fr"
            # x-default désigne la version servie à qui ne parle ni français ni anglais.
            # Sans lui, le moteur choisit seul, et son choix change d'un pays à l'autre.
            default = p["slug"] if lang == "en" else p["pair"]
            alt = (f'  <link rel="alternate" hreflang="{lang}" href="{BASE}{p["slug"]}.html">\n'
                   f'  <link rel="alternate" hreflang="{other}" href="{BASE}{p["pair"]}.html">\n'
                   f'  <link rel="alternate" hreflang="x-default" href="{BASE}{default}.html">\n')
        # Le FAQPage est déduit des blocs <details> du corps : une seule source de vérité.
        entities = faq_entities(body)
        # Fil d'Ariane : Google s'en sert pour afficher le chemin sous le titre du résultat.
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Aria",
             "item": BASE if lang == "fr" else BASE + "en.html"},
            {"@type": "ListItem", "position": 2, "name": p["crumb"],
             "item": BASE + p["slug"] + ".html"}]}
        jsonld = ('  <script type="application/ld+json">\n    '
                  + json.dumps(crumbs, ensure_ascii=False) + "\n  </script>\n")
        if entities:
            data = {"@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": entities}
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
            csp=CSP,
            lang=lang, title=p["title"], description=p["description"], base=BASE, slug=p["slug"],
            alternates=alt, jsonld=jsonld, oglocale="fr_FR" if lang == "fr" else "en_US",
            body=body, related=related, crumb=p["crumb"], homehref="./" if lang == "fr" else "en.html",
            ogimage="aria-video-fr.jpg" if lang == "fr" else "aria-video-en.jpg",
            imagealt="Présentation animée de la dictée Aria dans Notes sur Mac" if lang == "fr" else "Animated overview of Aria dictation in Notes on Mac",
            otherlang="en" if lang == "fr" else "fr",
            dlanchor="telecharger" if lang == "fr" else "download",
            privanchor="confidentialite" if lang == "fr" else "privacy", **loc)
        out = os.path.join("docs", p["slug"] + ".html")
        path = Path(out)
        if not path.exists() or path.read_text(encoding="utf-8") != html:
            path.write_text(html, encoding="utf-8")
            written.append(out)
    return written

def sitemap(changed=()):
    """Le sitemap est déduit de PAGES : il ne peut pas diverger des pages réellement produites."""
    today = datetime.date.today().isoformat()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    previous = {}
    path = Path(__file__).resolve().parent.parent / "docs" / "sitemap.xml"
    if path.exists():
        previous = {node.findtext("s:loc", namespaces=ns): node.findtext("s:lastmod", namespaces=ns)
                    for node in ET.parse(path).getroot().findall("s:url", ns)}
    changed_urls = {BASE + ("" if Path(name).name == "index.html" else Path(name).name) for name in changed}
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    def block(loc, alts, prio):
        out.append("  <url>")
        out.append(f"    <loc>{loc}</loc>")
        for hl, href in alts:
            out.append(f'    <xhtml:link rel="alternate" hreflang="{hl}" href="{href}"/>')
        lastmod = today if loc in changed_urls else previous.get(loc) or today
        out.append(f"    <lastmod>{lastmod}</lastmod>")
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
    changed = sync_french_spacing() + sync_home_faq() + build()
    for f in changed:
        print("écrit", f)
    print("sitemap.xml :", sitemap(changed), "URL")
