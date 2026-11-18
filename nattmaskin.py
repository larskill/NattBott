#!/usr/bin/env python3
"""Nattmaskinen: finner bedrifter i Bergen uten nettside og lager demo-sider + salgsutkast.

Bruk:
  python3 nattmaskin.py hent                 # henter kandidater fra Brønnøysund -> data/kandidater.json
  python3 nattmaskin.py bygg [--utelat ORGNR,ORGNR]   # lager demoer + morgenrapport fra kandidatene
  python3 nattmaskin.py slett ORGNR         # bedriften sa nei: fjern demo, aldri kontakt igjen
  python3 nattmaskin.py hent --fixture test_data/eksempel.json   # test uten nett

Kun standardbiblioteket; ingen pip-pakker trengs.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

import maler
import salong

ROT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROT, "data")
DEMO_DIR = os.path.join(ROT, "docs", "demo")
RAPPORT_DIR = os.path.join(ROT, "rapporter")
API = "https://data.brreg.no/enhetsregisteret/api/enheter"

GENERISKE_EPOSTDOMENER = {
    "gmail.com", "hotmail.com", "hotmail.no", "outlook.com", "outlook.no", "live.no", "live.com",
    "yahoo.com", "yahoo.no", "icloud.com", "me.com", "mac.com", "online.no", "getmail.no",
    "broadpark.no", "frisurf.no", "start.no", "lyse.net", "c2i.net", "msn.com", "protonmail.com",
    "proton.me", "bkkfiber.no", "bkk.no", "telia.no", "altibox.no", "ebnett.no", "tele2.no",
}
REGNSKAP_ORD = re.compile(r"regnskap|accounting|revisjon|revisor|økonomi|okonomi|lønn|lonn|fiken|tripletex", re.I)
EPOST_TILLATT_FORMER = {"AS", "ANS", "DA", "NUF", "ASA", "SA"}  # juridiske personer; ENK = fysisk person (mfl. § 15)


def les_json(sti, standard):
    try:
        with open(sti, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return standard


def skriv_json(sti, data):
    os.makedirs(os.path.dirname(sti), exist_ok=True)
    with open(sti, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ssl_kontekst():
    for kandidat in (os.environ.get("SSL_CERT_FILE"), os.environ.get("REQUESTS_CA_BUNDLE"),
                     os.path.expanduser("~/.ccr/ca-bundle.crt")):
        if kandidat and os.path.exists(kandidat):
            return ssl.create_default_context(cafile=kandidat)
    return ssl.create_default_context()


def api_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "nattmaskin/1.0"})
    for forsok in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl_kontekst()) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if forsok == 2:
                raise RuntimeError(f"Klarte ikke hente {url}: {e}") from e
            time.sleep(2 * (forsok + 1))


def hent_sok(sok, kommunenummer, maks=2000):
    """Henter alle enheter for ett søk (paginert)."""
    enheter, side = [], 0
    while True:
        params = dict(sok, kommunenummer=kommunenummer, size=100, page=side)
        svar = api_get(params)
        enheter += svar.get("_embedded", {}).get("enheter", [])
        sider = svar.get("page", {}).get("totalPages", 0)
        side += 1
        if side >= sider or len(enheter) >= maks or side * 100 >= 10000:
            return enheter
        time.sleep(0.3)


# ---------- hjelpefunksjoner for data ----------

def org_form(e):
    return (e.get("organisasjonsform") or {}).get("kode", "")


def kode(e):
    return (e.get("naeringskode1") or {}).get("kode", "")


def epostdomene(epost):
    return epost.split("@")[-1].lower().strip() if epost and "@" in epost else ""


def normaliser_tlf(t):
    if not t:
        return ""
    d = re.sub(r"\D", "", t)
    if d.startswith("0047"):
        d = d[4:]
    if d.startswith("47") and len(d) == 10:
        d = d[2:]
    if len(d) != 8:
        return t.strip()
    if d[0] in "49":
        return f"{d[:3]} {d[3:5]} {d[5:]}"
    return f"{d[:2]} {d[2:4]} {d[4:6]} {d[6:]}"


SMAAORD = {"OG": "og", "I": "i", "PÅ": "på", "AV": "av", "TIL": "til", "FOR": "for", "MED": "med",
           "FRA": "fra", "HOS": "hos"}
FORMER_SUFFIKS = re.compile(r"\s+(AS|ENK|ANS|DA|NUF|ASA|SA)$", re.I)


def pent_navn(navn):
    navn = FORMER_SUFFIKS.sub("", navn.strip())
    ord_ = []
    for i, w in enumerate(navn.split()):
        if i > 0 and w.upper() in SMAAORD:
            ord_.append(SMAAORD[w.upper()])
        elif len(w) <= 3 and w.isupper() and not any(c in "AEIOUYÆØÅ" for c in w[1:]):
            ord_.append(w)  # forkortelser som "BKS", "VVS"
        else:
            ord_.append("-".join(p.capitalize() for p in w.split("-")))
    return " ".join(ord_)


def pent_sted(s):
    if not s:
        return ""
    return " ".join(w if w in ("i", "på") else "-".join(p.capitalize() for p in w.split("-"))
                    for w in s.lower().split())


def slugify(tekst):
    t = tekst.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "bedrift"


def matcher_bransje(e, b):
    tekst = f"{e.get('navn', '')} {(e.get('naeringskode1') or {}).get('beskrivelse', '')}"
    if any(kode(e).startswith(p) for p in b.get("ekskluder_kode_prefiks", [])):
        return False
    if b.get("ekskluder_regex") and re.search(b["ekskluder_regex"], tekst, re.I):
        return False
    if b.get("krev_navn_regex") and not re.search(b["krev_navn_regex"], e.get("navn", ""), re.I):
        return False
    if b.get("kode_prefiks") and any(kode(e).startswith(p) for p in b["kode_prefiks"]):
        return True
    if b.get("navn_regex") and re.search(b["navn_regex"], e.get("navn", ""), re.I):
        return True
    return not b.get("kode_prefiks") and not b.get("navn_regex")


def aktiv(e):
    return not any(e.get(k) for k in ("konkurs", "underAvvikling",
                                      "underTvangsavviklingEllerTvangsopplosning", "slettedato"))


def vurder(e, b, idag):
    """Returnerer (poeng, grunner, flagg) eller None hvis uaktuell."""
    if not aktiv(e):
        return None
    form = org_form(e)
    grunner, flagg, poeng = [], [], 0
    epost = (e.get("epostadresse") or "").strip()
    dom = epostdomene(epost)
    if dom and dom not in GENERISKE_EPOSTDOMENER:
        if REGNSKAP_ORD.search(dom):
            flagg.append("E-posten ser ut til å gå til regnskapsfører – ring heller")
        else:
            poeng -= 5
            flagg.append(f"Har eget domene ({dom}) – sjekk om {dom} allerede har nettside")
    kan_epost = form in EPOST_TILLATT_FORMER and bool(epost) and not REGNSKAP_ORD.search(dom)
    if kan_epost:
        poeng += 2
        grunner.append("kan kontaktes på e-post")
    tlf = e.get("mobil") or e.get("telefon")
    if tlf:
        poeng += 1
        grunner.append("har telefon")
    if not kan_epost and not tlf:
        poeng -= 3
        flagg.append("Ingen kontaktinfo i registeret – må finnes manuelt")
    reg = e.get("registreringsdatoEnhetsregisteret") or e.get("stiftelsesdato")
    if reg:
        try:
            alder = (idag - dt.date.fromisoformat(reg[:10])).days
            if alder < 365:
                poeng += 3
                grunner.append("nyregistrert (under 1 år)")
            elif alder < 3 * 365:
                poeng += 1
        except ValueError:
            pass
    if (e.get("antallAnsatte") or 0) > 0:
        poeng += 1
        grunner.append(f"{e['antallAnsatte']} ansatte")
    return poeng, grunner, flagg


def til_kandidat(e, b, poeng, grunner, flagg):
    adr = e.get("forretningsadresse") or {}
    form = org_form(e)
    epost = (e.get("epostadresse") or "").strip()
    return {
        "orgnr": e["organisasjonsnummer"],
        "registernavn": e.get("navn", ""),
        "navn": pent_navn(e.get("navn", "")),
        "form": form,
        "bransje": b["id"],
        "bransje_navn": b["navn"],
        "mal": b["mal"],
        "naeringskode": kode(e),
        "naering": (e.get("naeringskode1") or {}).get("beskrivelse", ""),
        "adresse": ", ".join(adr.get("adresse") or []),
        "postnummer": adr.get("postnummer", ""),
        "poststed": pent_sted(adr.get("poststed", "")),
        "epost": epost,
        "epost_lov": form in EPOST_TILLATT_FORMER and bool(epost) and not REGNSKAP_ORD.search(epostdomene(epost)),
        "telefon": normaliser_tlf(e.get("mobil") or e.get("telefon") or ""),
        "registrert": e.get("registreringsdatoEnhetsregisteret", ""),
        "ansatte": e.get("antallAnsatte") or 0,
        "poeng": poeng,
        "grunner": grunner,
        "flagg": flagg + (["Har bare Facebook/Instagram-side"] if sosial_side(e.get("hjemmeside")) else []),
        "nettside": egen_nettside(e.get("hjemmeside")),
        "type": "oppgradering" if egen_nettside(e.get("hjemmeside")) else "ny",
    }


def sosial_side(url):
    return bool(url and re.search(r"facebook|instagram|fb\.com|tiktok|linkedin", url, re.I))


def egen_nettside(url):
    """Domenet til bedriftens egen nettside fra registeret (ikke Facebook o.l.), ellers ''."""
    url = (url or "").strip()
    if not url or sosial_side(url):
        return ""
    dom = urllib.parse.urlparse(url if "://" in url else "http://" + url).netloc.lower()
    return dom.removeprefix("www.")


# ---------- bilder fra Unsplash (eller Pexels) – gratis lisens ----------

_BILDE_CACHE = {}
_UNSPLASH_NYE = []
_BILDE_STOPP = []


def _hent_json(url, headers):
    req = urllib.request.Request(url, headers=dict(headers, **{"User-Agent": "nattmaskin/1.0"}))
    with urllib.request.urlopen(req, timeout=30, context=ssl_kontekst()) as r:
        return json.load(r)


def bilde_sok(sporring):
    if sporring in _BILDE_CACHE:
        return _BILDE_CACHE[sporring]
    if _BILDE_STOPP:
        return []
    fotos = []
    unsplash = os.environ.get("UNSPLASH_KEY", "").strip()
    pexels = os.environ.get("PEXELS_KEY", "").strip()
    try:
        if unsplash:
            url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
                {"query": sporring, "per_page": 30, "orientation": "portrait", "content_filter": "high"})
            data = _hent_json(url, {"Authorization": f"Client-ID {unsplash}", "Accept-Version": "v1"})
            utm = "?utm_source=nattbott&utm_medium=referral"
            for f in data.get("results", []):
                fotos.append({"id": f["id"], "src": f["urls"]["raw"] + "&w=1400&q=80&fm=jpg&fit=max",
                              "alt": f.get("alt_description") or "", "fotograf": f["user"]["name"],
                              "fotograf_url": f["user"]["links"]["html"] + utm, "kilde": "Unsplash",
                              "kilde_url": "https://unsplash.com/" + utm,
                              "nedlasting": f["links"]["download_location"]})
        elif pexels:
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": sporring, "per_page": 40, "orientation": "portrait"})
            data = _hent_json(url, {"Authorization": pexels})
            for f in data.get("photos", []):
                fotos.append({"id": str(f["id"]), "src": f["src"].get("large2x") or f["src"]["large"],
                              "alt": f.get("alt") or "", "fotograf": f.get("photographer", ""),
                              "fotograf_url": f.get("photographer_url", ""), "kilde": "Pexels",
                              "kilde_url": "https://www.pexels.com"})
    except Exception as e:  # noqa: BLE001
        print(f"::warning::Bildesøk feilet ({sporring}): {e}")
        if "403" in str(e) or "429" in str(e):
            _BILDE_STOPP.append(1)
            print("::warning::Bildetjenesten sier stopp (grense per time) – resten bygges uten bilder.")
    _BILDE_CACHE[sporring] = fotos
    return fotos


def registrer_unsplash_bruk():
    """Unsplash ber om et kall til download_location for bilder som tas i bruk (maks 35 per kjøring)."""
    nokkel = os.environ.get("UNSPLASH_KEY", "").strip()
    if not nokkel or not _UNSPLASH_NYE:
        return
    sti = os.path.join(DATA, "unsplash_brukt.json")
    brukt = set(les_json(sti, []))
    sendt = 0
    for f in _UNSPLASH_NYE:
        if f["id"] in brukt or sendt >= 15:
            continue
        try:
            _hent_json(f["nedlasting"], {"Authorization": f"Client-ID {nokkel}", "Accept-Version": "v1"})
            brukt.add(f["id"])
            sendt += 1
        except Exception:  # noqa: BLE001
            pass
    skriv_json(sti, sorted(brukt))


def velg_bilder(kand, antall=5):
    """Fem ulike bilder per demo, valgt ut fra orgnr så samme bedrift alltid får de samme."""
    if kand["mal"] not in salong.INNHOLD:
        return []
    inn = salong.innhold_for(kand)
    h = int(hashlib.sha1(kand["orgnr"].encode()).hexdigest(), 16)
    valgt = []
    for i in range(antall):
        pool = bilde_sok(inn["sok"][(h + i) % len(inn["sok"])])
        if not pool:
            continue
        for j in range(len(pool)):
            kandidat = pool[(h // 7 + i * 11 + j) % len(pool)]
            if kandidat not in valgt:
                valgt.append(kandidat)
                if kandidat.get("nedlasting"):
                    _UNSPLASH_NYE.append(kandidat)
                break
    return valgt


# ---------- kommandoer ----------

def kmd_hent(args, cfg):
    idag = dt.date.today()
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    fixture = les_json(args.fixture, None) if args.fixture else None
    kandidater, logg = {}, []
    for b in cfg["bransjer"]:
        funnet = 0
        for sok in b["sok"]:
            if fixture is not None:
                enheter = fixture
            else:
                try:
                    enheter = hent_sok(sok, cfg["kommunenummer"])
                except RuntimeError as feil:
                    logg.append(f"FEIL {b['id']} {sok}: {feil}")
                    continue
            if fixture is None:
                logg.append(f"{b['id']} {sok}: {len(enheter)} treff")
            for e in enheter:
                onr = e.get("organisasjonsnummer")
                if not onr or onr in sett or onr in kandidater:
                    continue
                if org_form(e) not in cfg["organisasjonsformer"] or not matcher_bransje(e, b):
                    continue
                if (e.get("forretningsadresse") or {}).get("kommunenummer") not in (None, cfg["kommunenummer"]):
                    continue
                v = vurder(e, b, idag)
                if v is None:
                    continue
                kandidater[onr] = til_kandidat(e, b, *v)
                funnet += 1
        if funnet == 0 and fixture is None:
            logg.append(f"ADVARSEL: 0 nye kandidater for {b['id']} – sjekk næringskode/søk i config.json")
    alle = sorted(kandidater.values(), key=lambda k: -k["poeng"])
    nye = [k for k in alle if k["type"] == "ny"][: cfg["maks_kandidater_per_natt"]]
    oppg = [k for k in alle if k["type"] == "oppgradering"][: cfg.get("maks_oppgradering_kandidater", 25)]
    liste = nye + oppg
    skriv_json(os.path.join(DATA, "kandidater.json"), {"dato": idag.isoformat(), "logg": logg, "kandidater": liste})
    print("\n".join(logg))
    print(f"{len(liste)} kandidater skrevet til data/kandidater.json (av {len(kandidater)} mulige)")


def kmd_bygg(args, cfg):
    idag = dt.date.today().isoformat()
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    k = les_json(os.path.join(DATA, "kandidater.json"), {"kandidater": []})
    utelat = {}
    if args.utelat_fil:
        utelat = les_json(args.utelat_fil, {})  # {orgnr: "grunn"}
    for onr in (args.utelat or "").split(","):
        if onr.strip():
            utelat.setdefault(onr.strip(), "utelatt manuelt")
    for onr, grunn in utelat.items():
        sett[onr] = {"dato": idag, "status": "utelatt", "grunn": grunn}

    brukte = set(os.listdir(DEMO_DIR)) if os.path.isdir(DEMO_DIR) else set()
    laget = []
    tak = {"ny": cfg["maks_demoer_per_natt"], "oppgradering": cfg.get("maks_oppgradering_per_natt", 8)}
    for kand in k["kandidater"]:
        typ = kand.get("type", "ny")
        if kand["orgnr"] in utelat or kand["orgnr"] in sett:
            continue
        if typ == "oppgradering" and not kand.get("problemer"):
            continue  # ikke revidert (nettsjekken har ikke kjørt)
        if sum(1 for x in laget if x.get("type", "ny") == typ) >= tak[typ]:
            continue
        slug = slugify(kand["navn"])
        if slug in brukte:
            slug = f"{slug}-{kand['orgnr'][-4:]}"
        brukte.add(slug)
        kand["slug"] = slug
        kand["demo_url"] = f"{cfg['demo_base_url'].rstrip('/')}/{slug}/"
        kand["bilder"] = velg_bilder(kand)
        mappe = os.path.join(DEMO_DIR, slug)
        os.makedirs(mappe, exist_ok=True)
        with open(os.path.join(mappe, "index.html"), "w", encoding="utf-8") as f:
            f.write(maler.demo_side(kand, cfg))
        kand["utkast"] = maler.utkast(kand, cfg)
        sett[kand["orgnr"]] = {"dato": idag, "status": "demo", "slug": slug}
        if typ == "oppgradering":
            sett[kand["orgnr"]].update(type="oppgradering", nettside=kand["nettside"], problemer=kand["problemer"])
        laget.append(kand)

    os.makedirs(RAPPORT_DIR, exist_ok=True)
    html = maler.morgenrapport(laget, utelat, k.get("logg", []), cfg, idag)
    for navn in (f"rapport-{idag}.html", "siste.html"):
        with open(os.path.join(RAPPORT_DIR, navn), "w", encoding="utf-8") as f:
            f.write(html)
    skriv_json(os.path.join(DATA, "sett.json"), sett)
    skriv_json(os.path.join(DATA, f"leads-{idag}.json"), laget)
    with open(os.path.join(DATA, "sist_natt.txt"), "w") as f:
        f.write(idag)
    registrer_unsplash_bruk()
    # robots + indeks som ikke lister kundene offentlig
    os.makedirs(DEMO_DIR, exist_ok=True)
    with open(os.path.join(ROT, "docs", "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /\n")
    with open(os.path.join(ROT, "docs", "index.html"), "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta name=robots content=noindex><title>Demo</title><p>Ingenting her.</p>")
    print(f"{len(laget)} demoer laget, {len(utelat)} utelatt. Rapport: rapporter/rapport-{idag}.html")


def kmd_slett(args, cfg):
    """Fjerner demoen for bedrifter som har sagt nei, og sørger for at de aldri kontaktes igjen."""
    import shutil
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    for onr in args.orgnr.split(","):
        onr = onr.strip()
        slug = (sett.get(onr) or {}).get("slug")
        if slug and os.path.isdir(os.path.join(DEMO_DIR, slug)):
            shutil.rmtree(os.path.join(DEMO_DIR, slug))
        sett[onr] = {"dato": dt.date.today().isoformat(), "status": "nei"}
        print(f"{onr}: demo slettet, merket «nei»")
    os.makedirs(DEMO_DIR, exist_ok=True)
    skriv_json(os.path.join(DATA, "sett.json"), sett)


# ---------- nettsjekk: har bedriften likevel en nettside? ----------

PARKERING = re.compile(r"domeneshop|parkert|er registrert hos|domain (is )?for sale|this domain|kjøp dette domenet|"
                       r"one\.com|webhuset|uniweb|hostinger|godaddy|coming soon|under construction|under arbeid", re.I)


def fold(t):
    t = t.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def hent_side(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nattmaskin nettsjekk)"})
    try:
        with urllib.request.urlopen(req, timeout=6, context=ssl_kontekst()) as r:
            if r.status != 200:
                return None
            return r.read(200_000).decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return None


def domener_a_sjekke(k):
    """Gjetter domener ut fra e-post og navn: belezamjbeauty.no, belezabeauty.no, beleza-beauty.no osv."""
    doms = []
    dom = epostdomene(k.get("epost", ""))
    if dom and dom not in GENERISKE_EPOSTDOMENER and not REGNSKAP_ORD.search(dom):
        doms.append(dom)
    ord_ = [w for w in slugify(k["navn"]).split("-") if w and w not in ("og", "i", "the", "by", "and", "as")]
    lange = [w for w in ord_ if len(w) >= 3]
    baser = ["".join(ord_), "-".join(ord_), "".join(lange), "-".join(lange)]
    if len(lange) >= 2:
        baser += [lange[0] + lange[-1], lange[0] + "-" + lange[-1], lange[0] + lange[1]]
    if lange and len(lange[0]) >= 6:
        baser.append(lange[0])
    for i, base in enumerate(dict.fromkeys(x for x in baser if len(x) >= 4)):
        doms.append(base + ".no")
        if i < 2:
            doms.append(base + ".com")
    return list(dict.fromkeys(doms))[:12]


KATALOGER = re.compile(r"facebook|instagram|tiktok|linkedin|youtube|twitter|x\.com|gulesider|1881|proff|brreg|"
                      r"purehelp|finn\.no|google|bing|yelp|tripadvisor|bedriftssok|webagent|21st\.ai|funnelfeedr|"
                      r"companexia|dnb\.com|utdanning|bytt\.no|mittanbud|fixa|wikipedia|kartverket|enirogs|"
                      r"hitta|kompass|opencorporates|norgeshandelen|regnskapstall|forvalt|allabolag|merinfo", re.I)
BOOKING = re.compile(r"timma|bestille\.no|fresha|booksy|treatwell|planway|bokadirekt|easyfrisor|onlinebooq|setmore", re.I)
_SOK_BRUKT = []


def nettsok(sporring):
    """Websøk via Tavily (gratis: 1000 søk/mnd). Returnerer liste med (url, tittel)."""
    nokkel = os.environ.get("TAVILY_KEY", "").strip()
    if not nokkel or len(_SOK_BRUKT) >= 35:
        return []
    _SOK_BRUKT.append(1)
    body = json.dumps({"query": sporring, "max_results": 6, "search_depth": "basic", "api_key": nokkel}).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {nokkel}"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_kontekst()) as r:
            return [(x.get("url", ""), x.get("title", "")) for x in json.load(r).get("results", [])]
    except Exception as e:  # noqa: BLE001
        print(f"::warning::Websøk feilet: {e}")
        return []


def sok_etter_nettside(kand):
    """Søker på navn + sted. Treff på et domene som inneholder navnet = egen nettside."""
    ord_ = [w for w in re.findall(r"[a-z0-9]+", fold(kand["navn"])) if len(w) >= 4]
    if not ord_:
        return None
    sted = kand.get("poststed") or "Bergen"
    for url, tittel in nettsok(f'"{kand["navn"]}" {sted}'):
        dom = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
        if not dom or KATALOGER.search(dom):
            continue
        if BOOKING.search(dom):
            kand.setdefault("flagg", []).append(f"Har bookingside: {url}")
            continue
        dom_fold = re.sub(r"[^a-z0-9]", "", dom.split(".")[0])
        if any(w in dom_fold for w in ord_) or (sum(1 for w in ord_ if w in fold(tittel)) >= min(2, len(ord_))
                                                 and len(ord_) >= 2):
            return dom
    return None


def finn_nettside(kand):
    """Returnerer domenet hvis bedriften ser ut til å ha en nettside, ellers None.
    Gjettede domener godtas bare hvis siden både nevner navnet OG har lokalt bevis
    (orgnr, telefonnummer, Bergen eller poststedet) – ellers flagges de for manuell sjekk."""
    funnet = sok_etter_nettside(kand)
    if funnet:
        return funnet
    ord_ = [w for w in re.findall(r"[a-z0-9]+", fold(kand["navn"])) if len(w) >= 4]
    trengs = min(2, len(ord_)) or 1
    epostdom = epostdomene(kand.get("epost", ""))
    tlf = re.sub(r"\D", "", kand.get("telefon") or "")[-8:]
    sted = fold(kand.get("poststed") or "")
    for dom in domener_a_sjekke(kand):
        html_ = None
        for url in (f"https://{dom}", f"https://www.{dom}", f"http://{dom}"):
            html_ = hent_side(url)
            if html_:
                break
        if not html_:
            continue
        if PARKERING.search(html_) and len(html_) < 20000:
            continue
        if dom == epostdom:
            return dom
        tekst = fold(html_)
        sifre = re.sub(r"\D", "", html_)
        lokalt = (("bergen" in tekst) or (sted and sted in tekst) or (kand.get("orgnr") and kand["orgnr"] in sifre)
                  or (len(tlf) == 8 and tlf in sifre))
        if lokalt and sum(1 for w in ord_ if w in tekst) >= trengs:
            return dom
        kand.setdefault("flagg", []).append(f"{dom} svarer – sjekk om det er deres side")
    return None


# ---------- revisjon av eksisterende nettside ----------

GAMMEL_TEKNOLOGI = [
    (re.compile(r"\.swf\b|shockwave-flash", re.I), "Flash"),
    (re.compile(r"microsoft frontpage", re.I), "FrontPage"),
    (re.compile(r"adobe muse", re.I), "Adobe Muse"),
    (re.compile(r"iweb", re.I), "iWeb"),
    (re.compile(r'name="generator"[^>]*content="joomla!? ?[1-3]\b', re.I), "gammel Joomla"),
    (re.compile(r'name="generator"[^>]*content="wordpress [1-4]\.', re.I), "gammel WordPress"),
]


def hent_side_info(url, timeout=10):
    """(html, sekunder, endelig_url, feil). feil: None, 'http' (svarer, men avviser oss) eller 'nett' (svarer ikke)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_kontekst()) as r:
            html_ = r.read(1_500_000).decode("utf-8", "ignore")
            return html_, time.time() - start, r.geturl(), None
    except urllib.error.HTTPError:
        return None, None, None, "http"
    except Exception:  # noqa: BLE001
        return None, None, None, "nett"


def revider_nettside(dom, idag=None):
    """Finner konkrete svakheter. Returnerer (poeng, svakheter). Sterke svakheter = 2 poeng, svake = 1.
    Siden må kunne leses for å bli vurdert – avviser den oss (f.eks. 403), lar vi den være."""
    idag = idag or dt.date.today()
    feil = []
    html_ = sek = endelig = None
    for url in (f"https://{dom}", f"https://www.{dom}", f"http://{dom}", f"http://www.{dom}"):
        html_, sek, endelig, f = hent_side_info(url)
        if html_:
            break
        feil.append(f)
    if not html_:
        if feil and all(f == "nett" for f in feil):
            return 3, ["Nettsiden svarte ikke da jeg prøvde å åpne den"]
        return 0, []
    https_ok = (endelig or "").startswith("https")
    sterke, svake = [], []
    if PARKERING.search(html_) and len(html_) < 20000:
        return 3, ["Domenet viser bare en parkeringsside"]
    if re.search(r"facebook\.com", endelig or "", re.I):
        return 3, ["Domenet sender bare videre til Facebook"]
    if not https_ok:
        sterke.append("Mangler sikker tilkobling (nettlesere viser «Ikke sikker»)")
    if not re.search(r'<meta[^>]+name=["\']?viewport', html_, re.I):
        sterke.append("Ikke tilpasset mobil")
    aar = [int(x) for x in re.findall(r"(?:©|&copy;|copyright)\D{0,40}?((?:19|20)\d\d)(?!\d)", html_, re.I)]
    if aar and max(aar) <= idag.year - 3:
        sterke.append(f"Ser ikke ut til å ha vært oppdatert siden {max(aar)}")
    for mønster, navn in GAMMEL_TEKNOLOGI:
        if mønster.search(html_):
            sterke.append(f"Bygget med utdatert teknologi ({navn})")
            break
    if not re.search(r'<meta[^>]+name=["\']?description', html_, re.I):
        svake.append("Mangler beskrivelse for Google-søk")
    if sek and sek > 3.5:
        svake.append(f"Treg å laste ({sek:.0f} sekunder)")
    return 2 * len(sterke) + len(svake), sterke + svake


def kmd_nettsjekk(args, cfg):
    """Nye kandidater: finnes det likevel en nettside? Da blir de oppgraderings-kandidater.
    Oppgraderings-kandidater: revider siden – bare de med tydelige svakheter går videre."""
    sti = os.path.join(DATA, "kandidater.json")
    k = les_json(sti, {"kandidater": []})
    utelat = les_json(os.path.join(DATA, "utelat.json"), {})
    for kand in k["kandidater"]:
        if kand.get("type", "ny") == "ny":
            dom = finn_nettside(kand)
            if dom:
                kand["type"], kand["nettside"] = "oppgradering", dom
        if kand.get("type") == "oppgradering":
            poeng, svakheter = revider_nettside(kand["nettside"])
            kand["problemer"] = svakheter
            if poeng < 2:
                utelat[kand["orgnr"]] = f"nettsiden {kand['nettside']} ser oppdatert ut"
    skriv_json(sti, k)
    skriv_json(os.path.join(DATA, "utelat.json"), utelat)
    n_opp = sum(1 for x in k["kandidater"] if x.get("type") == "oppgradering" and x["orgnr"] not in utelat)
    print(f"Nettsjekk: {len(utelat)} utelatt, {n_opp} oppgraderings-kandidater med svakheter")


def kmd_sjekk_igjen(args, cfg):
    """Sjekker en dags demoer på nytt. Har bedriften nettside: revider den – svak side = oppgraderings-lead,
    god side = demoen fjernes. Bedrifter som tidligere ble fjernet pga. nettside vurderes også på nytt."""
    import shutil
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    dato = args.dato or dt.date.today().isoformat()
    logg = []
    for onr, info in list(sett.items()):
        if info.get("dato") != dato or info.get("status") not in ("demo", "har_nettside"):
            continue
        try:
            e = api_get_enhet(onr)
        except Exception:  # noqa: BLE001
            continue
        adr = e.get("forretningsadresse") or {}
        kand = {"navn": pent_navn(e.get("navn", "")), "epost": e.get("epostadresse") or "", "orgnr": onr,
                "telefon": e.get("mobil") or e.get("telefon") or "", "poststed": adr.get("poststed", "")}
        dom = info.get("nettside") or egen_nettside(e.get("hjemmeside")) or (
            info.get("grunn") if info["status"] == "har_nettside" else None) or finn_nettside(kand)
        if dom:
            dom = re.sub(r"^.*?:\s*", "", dom).strip()
        slug = info.get("slug") or slugify(kand["navn"])
        if not dom:
            if info["status"] == "har_nettside":
                sett[onr] = {"dato": dato, "status": "demo", "slug": slug}
                logg.append(f"Gjenopprettet (fant ikke sikker nettside): {kand['navn']}")
            continue
        poeng, svakheter = revider_nettside(dom)
        if poeng >= 2:
            sett[onr] = {"dato": dato, "status": "demo", "slug": slug, "type": "oppgradering",
                         "nettside": dom, "problemer": svakheter}
            logg.append(f"Oppgradering: {kand['navn']} ({dom}) – {'; '.join(svakheter)}")
        else:
            if os.path.isdir(os.path.join(DEMO_DIR, slug)):
                shutil.rmtree(os.path.join(DEMO_DIR, slug))
            sett[onr] = {"dato": dato, "status": "har_nettside", "grunn": dom, "slug": slug}
            logg.append(f"God nettside – demo fjernet: {kand['navn']} ({dom})")
    skriv_json(os.path.join(DATA, "sett.json"), sett)
    print("\n".join(logg) or "Ingen endringer")


def kmd_oppgrader(args, cfg):
    """Legger bedrifter manuelt til som oppgraderings-leads (f.eks. pen-men-utdatert design som revisjonen ikke ser)."""
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    dato = args.dato or dt.date.today().isoformat()
    for onr in [x.strip() for x in args.orgnr.split(",") if x.strip()]:
        e = api_get_enhet(onr)
        info = sett.get(onr, {})
        dom = (info.get("nettside") or egen_nettside(e.get("hjemmeside"))
               or re.sub(r"^.*?:\s*", "", info.get("grunn") or "").strip())
        _, svakheter = revider_nettside(dom) if dom else (0, [])
        slug = info.get("slug") or slugify(pent_navn(e.get("navn", "")))
        sett[onr] = {"dato": dato, "status": "demo", "slug": slug, "type": "oppgradering",
                     "nettside": dom, "problemer": svakheter}
        print(f"Lagt til som oppgradering: {pent_navn(e.get('navn', ''))} ({dom or 'ukjent nettside'})"
              f" – {'; '.join(svakheter) or 'ingen tekniske svakheter, bare design'}")
    skriv_json(os.path.join(DATA, "sett.json"), sett)


# ---------- morgenrapport på e-post ----------

def kmd_epost(args, cfg):
    import smtplib
    from email.message import EmailMessage
    bruker = os.environ.get("GMAIL_USER") or cfg["selger"]["epost"]
    passord = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "").strip()
    if not passord:
        sys.exit("Mangler apppassord (secret NATTBOTT) – rapporten ble ikke sendt.")
    idag = dt.date.today().isoformat()
    leads = les_json(os.path.join(DATA, f"leads-{idag}.json"), [])
    with open(os.path.join(RAPPORT_DIR, "siste.html"), encoding="utf-8") as f:
        html_ = f.read()
    n_epost = sum(1 for x in leads if x["utkast"]["type"] == "epost")
    msg = EmailMessage()
    msg["Subject"] = f"Morgenrapport {idag}: {len(leads)} nye demoer ({n_epost} e-post, {len(leads) - n_epost} ring)"
    msg["From"] = bruker
    msg["To"] = cfg.get("rapport_til") or bruker
    msg.set_content("Åpne vedlegget for morgenrapporten.\n\n" + "\n".join(
        f"- {x['navn']} ({x['bransje_navn']}): {x['demo_url']}" for x in leads))
    msg.add_alternative(html_, subtype="html")
    msg.add_attachment(html_.encode("utf-8"), maintype="text", subtype="html", filename=f"morgenrapport-{idag}.html")
    # Trygg diagnose uten å avsløre passordet
    print(f"Avsender: {bruker} | apppassord: {len(passord)} tegn, "
          f"bare små bokstaver: {'ja' if passord.isalpha() and passord.islower() else 'nei'}")
    feil = []
    for metode in ("SSL 465", "STARTTLS 587"):
        try:
            if metode == "SSL 465":
                s = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30)
            else:
                s = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
            s.ehlo()
            s.login(bruker, passord)
            s.send_message(msg)
            s.quit()
            break
        except smtplib.SMTPAuthenticationError as e:
            feil.append(f"{metode}: Gmail godtok ikke innloggingen ({e.smtp_code}) "
                        f"{e.smtp_error.decode(errors='ignore')[:200]}")
        except Exception as e:  # noqa: BLE001
            feil.append(f"{metode}: {type(e).__name__}: {e}")
    else:
        print("\n".join(feil))
        sys.exit("E-posten ble ikke sendt. Sjekk at secret NATTBOTT er apppassordet (16 små bokstaver).")
    print("Morgenrapport sendt til", msg["To"])


def kmd_gjenskap(args, cfg):
    """Lager morgenrapporten på nytt for demoer laget en gitt dato (f.eks. hvis e-posten feilet)."""
    idag = dt.date.today()
    args.dato = args.dato or idag.isoformat()
    sett = les_json(os.path.join(DATA, "sett.json"), {})
    leads = []
    for onr, info in sett.items():
        if info.get("status") != "demo" or info.get("dato") != args.dato:
            continue
        e = api_get_enhet(onr)
        b = next((b for b in cfg["bransjer"] if matcher_bransje(e, b)), cfg["bransjer"][0])
        v = vurder(e, b, idag) or (0, [], [])
        kand = til_kandidat(e, b, *v)
        kand["slug"] = info["slug"]
        kand["demo_url"] = f"{cfg['demo_base_url'].rstrip('/')}/{info['slug']}/"
        kand["type"] = info.get("type", "ny")
        kand["nettside"] = info.get("nettside", "")
        kand["problemer"] = info.get("problemer", [])
        if args.bygg_demoer or not os.path.exists(os.path.join(DEMO_DIR, info["slug"], "index.html")):
            kand["bilder"] = velg_bilder(kand)
            mappe = os.path.join(DEMO_DIR, info["slug"])
            os.makedirs(mappe, exist_ok=True)
            with open(os.path.join(mappe, "index.html"), "w", encoding="utf-8") as f:
                f.write(maler.demo_side(kand, cfg))
        kand["utkast"] = maler.utkast(kand, cfg)
        leads.append(kand)
    leads.sort(key=lambda k: -k["poeng"])
    registrer_unsplash_bruk()
    bilder_brukt = sum(1 for k in leads if k.get("bilder"))
    if args.bygg_demoer:
        print(f"Demoer bygget på nytt: {len(leads)} (med bilder: {bilder_brukt})")
    os.makedirs(RAPPORT_DIR, exist_ok=True)
    html_ = maler.morgenrapport(leads, {}, [f"Gjenskapt rapport for {args.dato}"], cfg, args.dato)
    for navn in (f"rapport-{args.dato}.html", "siste.html"):
        with open(os.path.join(RAPPORT_DIR, navn), "w", encoding="utf-8") as f:
            f.write(html_)
    skriv_json(os.path.join(DATA, f"leads-{idag.isoformat()}.json"), leads)
    print(f"Rapport gjenskapt for {args.dato}: {len(leads)} bedrifter")


def api_get_enhet(orgnr):
    req = urllib.request.Request(f"{API}/{orgnr}", headers={"Accept": "application/json", "User-Agent": "nattmaskin/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ssl_kontekst()) as r:
        return json.load(r)


# ---------- kryptert rapportside på nettstedet ----------

def kmd_publiser_rapport(args, cfg):
    """Krypterer morgenrapporten (AES-256, passord fra RAPPORT_PASSORD) og legger den i docs/rapport/."""
    import base64
    import subprocess
    passord = os.environ.get("RAPPORT_PASSORD", "")
    if not passord:
        print("::warning::Mangler secret RAPPORT_PASSORD – rapportsiden ble ikke oppdatert.")
        return
    kilde = os.path.join(RAPPORT_DIR, "siste.html")
    if not os.path.exists(kilde):
        print("::warning::Ingen rapport å publisere.")
        return
    kryptert = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-md", "sha256", "-salt",
         "-pass", "env:RAPPORT_PASSORD", "-in", kilde],
        check=True, capture_output=True, env=dict(os.environ)).stdout
    data = base64.b64encode(kryptert).decode()
    dato = args.dato or dt.date.today().isoformat()
    rot = os.path.join(ROT, "docs", "rapport")
    arkiv = os.path.join(rot, "arkiv")
    os.makedirs(arkiv, exist_ok=True)
    with open(os.path.join(arkiv, f"{dato}.html"), "w", encoding="utf-8") as f:
        f.write(maler.laast_side(data, dato, [], "../"))
    datoer = sorted((n[:-5] for n in os.listdir(arkiv) if n.endswith(".html")), reverse=True)[:14]
    with open(os.path.join(rot, "index.html"), "w", encoding="utf-8") as f:
        f.write(maler.laast_side(data, dato, datoer, ""))
    print(f"Kryptert rapport publisert for {dato} (arkiv: {len(datoer)} dager)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kmd", required=True)
    h = sub.add_parser("hent")
    h.add_argument("--fixture", help="JSON-liste med enheter (for test uten nett)")
    b = sub.add_parser("bygg")
    b.add_argument("--utelat", help="kommaseparerte orgnr som skal hoppes over")
    b.add_argument("--utelat-fil", help="JSON {orgnr: grunn} fra nettsjekken")
    sub.add_parser("nettsjekk")
    sub.add_parser("epost")
    pr = sub.add_parser("publiser-rapport")
    pr.add_argument("dato", nargs="?", default="")
    op = sub.add_parser("oppgrader")
    op.add_argument("orgnr")
    op.add_argument("dato", nargs="?", default="")
    si = sub.add_parser("sjekk-igjen")
    si.add_argument("dato", nargs="?", default="")
    g = sub.add_parser("gjenskap")
    g.add_argument("dato", nargs="?", default="", help="YYYY-MM-DD (tom = i dag)")
    g.add_argument("--bygg-demoer", action="store_true", help="lag demo-sidene på nytt med nyeste maler")
    sl = sub.add_parser("slett")
    sl.add_argument("orgnr", help="kommaseparerte orgnr som har takket nei")
    args = p.parse_args()
    cfg = les_json(os.path.join(ROT, "config.json"), None)
    if cfg is None:
        sys.exit("Fant ikke config.json")
    {"hent": kmd_hent, "bygg": kmd_bygg, "slett": kmd_slett,
     "nettsjekk": kmd_nettsjekk, "epost": kmd_epost, "gjenskap": kmd_gjenskap,
     "publiser-rapport": kmd_publiser_rapport,
     "sjekk-igjen": kmd_sjekk_igjen, "oppgrader": kmd_oppgrader}[args.kmd](args, cfg)


if __name__ == "__main__":
    main()
