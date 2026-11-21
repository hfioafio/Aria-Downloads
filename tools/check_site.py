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
        self.lang = None
        self.title = None
        self.description = None
        self.images_without_alt = 0
        self.in_title = False
        self.json_errors = []
        self.jsonld = []
        self.json_text = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "title":
            self.title = ""
            self.in_title = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content", "")
        # alt="" reste permis (image décorative) ; son absence est une erreur d'accessibilité.
        if tag == "img" and "alt" not in attrs:
            self.images_without_alt += 1
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
        if self.in_title:
            self.title += value

    def handle_endtag(self, tag):
        if tag == "script" and self.json_text is not None:
            try:
                self.jsonld.append(json.loads(self.json_text))
            except json.JSONDecodeError as error:
                self.json_errors.append(str(error))
            self.json_text = None
        if tag == "title":
            self.in_title = False


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
        require(not page.json_errors, f"{name}: données structurées JSON-LD illisibles : {page.json_errors}")
        require(page.images_without_alt == 0, f"{name}: {page.images_without_alt} image(s) sans attribut alt")
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
        require(page.lang in ("fr", "en"), f"{name}: langue de la page (<html lang>) absente")
        require(bool(page.title and page.title.strip()), f"{name}: <title> absent ou vide")
        require(bool(page.description), f"{name}: meta description absente")
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
    site_version = next(iter(versions[0]), None)

    # Sécurité du téléchargement : chaque DMG proposé a son empreinte, au même nom, et tout
    # désigne la même version (le robot de publication remplace les numéros un par un).
    for name in ("index.html", "en.html"):
        links = {href for tag, href in pages[name].refs if tag == "a"}
        for dmg in [h for h in links if h.endswith(".dmg")]:
            require(dmg + ".sha256" in links, f"{name}: empreinte SHA-256 absente pour {dmg.rsplit('/', 1)[-1]}")
        apps = [data for data in pages[name].jsonld if data.get("@type") == "SoftwareApplication"]
        require(apps and apps[0].get("softwareVersion") == site_version, f"{name}: softwareVersion différente des liens de téléchargement")
        require(f"releases/tag/v{site_version}" in sources[name], f"{name}: lien vers la page de version absent ou périmé")

    manifest = json.loads((ROOT / "updates" / "preview.json").read_text(encoding="utf-8"))
    require(manifest.get("version") == site_version, f"updates/preview.json ({manifest.get('version')}) ≠ version proposée sur le site ({site_version})")
    for arch, entry in manifest.get("downloads", {}).items():
        require(f"/releases/download/v{manifest.get('version')}/" in entry.get("url", ""), f"preview.json : URL {arch} hors de la version annoncée")
        require(re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")) is not None, f"preview.json : SHA-256 {arch} invalide")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_dmg = re.findall(r"\((https://github\.com/[^)]+?\.dmg)\)", readme)
    readme_sha = set(re.findall(r"\((https://github\.com/[^)]+?\.dmg\.sha256)\)", readme))
    require(readme_dmg and all(f"/releases/download/v{site_version}/" in url for url in readme_dmg), "README : liens de téléchargement d'une autre version que le site")
    require(all(url + ".sha256" in readme_sha for url in set(readme_dmg)), "README : empreinte SHA-256 absente pour un DMG")

    # GitHub Pages sert 404.html pour toute URL absente, même imbriquée : rien de relatif.
    for tag, href in pages["404.html"].refs:
        require(re.match(r"(https?:|/|#)", href) is not None, f"404.html : chemin relatif {href}, cassé sur une URL imbriquée")

    # La vitrine promet de ne transmettre « aucune visite ni aucun clic » : la politique de
    # sécurité le garantit (aucune requête sortante possible depuis ces pages).
    for name in indexed + ["404.html"]:
        csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', sources[name])
        require(csp is not None and "connect-src 'none'" in csp.group(1), f"{name}: politique de sécurité absente ou autorisant des requêtes sortantes")

    for name, source in sources.items():
        for wrap in re.findall(r'<div class="table-wrap"[^>]*>', source):
            require('tabindex="0"' in wrap, f"{name}: tableau défilant inaccessible au clavier")

    # Avertissements : ne bloquent pas, mais signalent ce qu'un humain doit vérifier.
    warnings = []
    for name in indexed:
        title, description = (pages[name].title or "").strip(), pages[name].description or ""
        if len(title) > 70:
            warnings.append(f"{name}: titre de {len(title)} caractères, souvent tronqué dans les résultats de recherche")
        if not 50 <= len(description) <= 170:
            warnings.append(f"{name}: meta description de {len(description)} caractères (50 à 170 conseillés)")
    for name, source in sorted(sources.items()):
        for playlist in sorted(set(re.findall(r"youtube\.com/playlist\?list=([\w-]+)", source))):
            # Les playlists récentes ont des identifiants courts (PL + 11 caractères) : ceux des
            # deux accueils, vérifiés le 21/11/2026, ouvrent bien « démarrer avec Aria ».
            if not re.fullmatch(r"PL[\w-]{11}|PL[\w-]{16}|PL[\w-]{32}", playlist):
                warnings.append(f"{name}: identifiant de playlist YouTube inhabituel ({playlist}, {len(playlist)} caractères) : lien probablement tronqué")

    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap = ET.parse(DOCS / "sitemap.xml").getroot()
    urls = [node.findtext("s:loc", namespaces=ns) for node in sitemap.findall("s:url", ns)]
    expected = {BASE + ("" if name == "index.html" else name) for name in indexed}
    require(len(urls) == len(expected) and set(urls) == expected, "Sitemap différent des pages indexables")

    for message in warnings:
        print("Avertissement : " + message, file=sys.stderr)
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
        # Les fichiers .sha256 proposés aux visiteurs doivent porter l'empreinte du manifeste de mise à
        # jour (les DMG « Installer » et ceux de la mise à jour sont identiques). Quelques octets chacun.
        for arch, label in (("arm64", "Apple-Silicon"), ("x64", "Intel")):
            url = next(href for tag, href in pages["index.html"].refs if tag == "a" and href.endswith(f"-{label}.dmg.sha256"))
            try:
                with urlopen(Request(url), timeout=25, context=context) as response:
                    published = response.read(4096).decode("utf-8", "replace").split()[0].lower()
            except (OSError, IndexError) as error:
                print(f"Empreinte publiée illisible ({label}) : {error}", file=sys.stderr)
                return 1
            if published != manifest["downloads"][arch]["sha256"]:
                print(f"Empreinte {label} publiée ≠ manifeste de mise à jour", file=sys.stderr)
                return 1
            checked += 1
        print(f"OK : {checked} fichiers réellement servis identiques aux fichiers validés, empreintes publiées conformes au manifeste ; aucun DMG téléchargé.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Comparer aussi les fichiers réellement servis sur GitHub Pages")
    sys.exit(check(parser.parse_args().live))
