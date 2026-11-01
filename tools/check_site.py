#!/usr/bin/env python3
"""Contrôle la vitrine et, avec --live, compare les pages réellement publiées."""
import argparse
import json
import re
import ssl
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True
from build_pages import BASE, PAGES, faq_entities

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.refs = []
        self.canonical = []
        self.alternates = {}
        self.h1 = 0
        self.jsonld = []
        self.json_text = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and attrs.get("property", attrs.get("name", "")) in ("og:image", "twitter:image"):
            self.refs.append(("image", attrs.get("content", "")))
        for key in ("href", "src", "poster"):
            if attrs.get(key):
                self.refs.append((tag, attrs[key]))
        if tag == "link":
            if attrs.get("rel") == "canonical":
                self.canonical.append(attrs.get("href"))
            if attrs.get("rel") == "alternate" and attrs.get("hreflang"):
                self.alternates[attrs["hreflang"]] = attrs.get("href")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.json_text = ""

    def handle_data(self, value):
        if self.json_text is not None:
            self.json_text += value

    def handle_endtag(self, tag):
        if tag == "script" and self.json_text is not None:
            self.jsonld.append(json.loads(self.json_text))
            self.json_text = None


def check(live=False):
    sources = {path.name: path.read_text(encoding="utf-8") for path in DOCS.glob("*.html")}
    pages = {name: Page(source) for name, source in sources.items()}
    indexed = ["index.html", "en.html"] + [p["slug"] + ".html" for p in PAGES]
    errors = []
    references = 0

    def require(condition, message):
        if not condition:
            errors.append(message)

    for name, page in pages.items():
        require(not [key for key, n in Counter(page.ids).items() if n > 1], f"{name}: identifiants répétés")
        for tag, href in page.refs:
            references += 1
            url = urlsplit(urljoin(BASE + name, href))
            require(name not in indexed or ".chatgpt.site" not in url.netloc, f"{name}: lien vers l’hébergement privé")
            require(not (tag == "script" and url.netloc != urlsplit(BASE).netloc), f"{name}: script tiers")
            if url.netloc != urlsplit(BASE).netloc or url.scheme not in ("http", "https"):
                continue
            require(url.path.startswith(urlsplit(BASE).path), f"{name}: chemin hors de la vitrine : {href}")
            if not url.path.startswith(urlsplit(BASE).path):
                continue
            relative = unquote(url.path[len(urlsplit(BASE).path):]) or "index.html"
            target = DOCS / relative
            if target.is_dir():
                target = target / "index.html"
            require(target.exists(), f"{name}: fichier absent : {href}")
            if url.fragment and target.name in pages:
                require(unquote(url.fragment) in pages[target.name].ids, f"{name}: ancre absente : {href}")

    for name in indexed:
        page = pages[name]
        canonical = BASE + ("" if name == "index.html" else name)
        require(page.h1 == 1, f"{name}: attendu un seul titre principal")
        require(page.canonical == [canonical], f"{name}: URL canonique incorrecte")
        require(set(page.alternates) == {"fr", "en", "x-default"}, f"{name}: traductions incomplètes")
        faqs = [data for data in page.jsonld if data.get("@type") == "FAQPage"]
        entities = faq_entities(sources[name])
        require(len(faqs) == (1 if entities else 0), f"{name}: nombre de FAQ structurées incorrect")
        if faqs:
            require(faqs[0].get("mainEntity") == entities, f"{name}: FAQ structurée différente des réponses visibles")
        for data in page.jsonld:
            if data.get("@type") == "SoftwareApplication":
                require(all(str(offer.get("price")) == "0" for offer in data.get("offers", [])), f"{name}: offre payante structurée alors que Pro est fermé")

    for entry in PAGES:
        name = entry["slug"] + ".html"
        other = "fr" if entry["lang"] == "en" else "en"
        require(pages[name].alternates.get(other) == BASE + entry["pair"] + ".html", f"{name}: traduction incorrecte")
        require(not re.search(r"releases/download/.*?\.dmg", sources[name]), f"{name}: article lié à une version figée")

    versions = []
    for name in ("index.html", "en.html"):
        links = [href for tag, href in pages[name].refs if tag == "a" and href.endswith(".dmg")]
        require(len(links) == 2 and all("/Aria-Installer-" in href for href in links), f"{name}: deux installateurs distincts attendus")
        versions.append(set(re.findall(r"releases/download/v([^/]+)/", " ".join(links))))
    require(len(versions[0]) == 1 and versions[0] == versions[1], "Versions FR/EN des installateurs incohérentes")

    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap = ET.parse(DOCS / "sitemap.xml").getroot()
    urls = [node.findtext("s:loc", namespaces=ns) for node in sitemap.findall("s:url", ns)]
    expected = {BASE + ("" if name == "index.html" else name) for name in indexed}
    require(len(urls) == len(expected) and set(urls) == expected, "Sitemap différent des pages indexables")

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    print(f"OK : {len(pages)} fichiers HTML, {len(indexed)} pages indexables, {references} références ; FAQ, langues, sitemap et installateurs cohérents.")
    if live:
        checked = 0
        # Python installé séparément sur macOS n’a pas toujours son propre magasin de CA.
        # Utiliser les certificats système disponibles en conservant la vérification TLS.
        system_ca = Path("/etc/ssl/cert.pem")
        context = ssl.create_default_context(cafile=str(system_ca) if system_ca.is_file() else None)
        for name in indexed + ["sitemap.xml", "pages.css", "aria-video-fr.jpg", "aria-video-en.jpg"]:
            url = BASE + ("" if name == "index.html" else name)
            request = Request(url, headers={"Cache-Control": "no-cache"})
            try:
                with urlopen(request, timeout=25, context=context) as response:
                    content = response.read()
            except OSError as error:
                print(f"Vérification HTTPS impossible pour {name} : {error}", file=sys.stderr)
                return 1
            if content != (DOCS / name).read_bytes():
                print(f"Publication différente du fichier validé : {name}", file=sys.stderr)
                return 1
            checked += 1
        print(f"OK : {checked} fichiers réellement servis identiques aux fichiers validés ; aucun DMG téléchargé.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Comparer aussi les fichiers réellement servis sur GitHub Pages")
    sys.exit(check(parser.parse_args().live))
