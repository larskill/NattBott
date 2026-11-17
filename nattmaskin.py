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
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

import maler

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
    if not aktiv(e) or (e.get("hjemmeside") or "").strip():
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
        "flagg": flagg,
    }


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
    liste = sorted(kandidater.values(), key=lambda k: -k["poeng"])[: cfg["maks_kandidater_per_natt"]]
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
    for kand in k["kandidater"]:
        if kand["orgnr"] in utelat or kand["orgnr"] in sett:
            continue
        if len(laget) >= cfg["maks_demoer_per_natt"]:
            break
        slug = slugify(kand["navn"])
        if slug in brukte:
            slug = f"{slug}-{kand['orgnr'][-4:]}"
        brukte.add(slug)
        kand["slug"] = slug
        kand["demo_url"] = f"{cfg['demo_base_url'].rstrip('/')}/{slug}/"
        mappe = os.path.join(DEMO_DIR, slug)
        os.makedirs(mappe, exist_ok=True)
        with open(os.path.join(mappe, "index.html"), "w", encoding="utf-8") as f:
            f.write(maler.demo_side(kand, cfg))
        kand["utkast"] = maler.utkast(kand, cfg)
        sett[kand["orgnr"]] = {"dato": idag, "status": "demo", "slug": slug}
        laget.append(kand)

    os.makedirs(RAPPORT_DIR, exist_ok=True)
    html = maler.morgenrapport(laget, utelat, k.get("logg", []), cfg, idag)
    for navn in (f"rapport-{idag}.html", "siste.html"):
        with open(os.path.join(RAPPORT_DIR, navn), "w", encoding="utf-8") as f:
            f.write(html)
    skriv_json(os.path.join(DATA, "sett.json"), sett)
    skriv_json(os.path.join(DATA, f"leads-{idag}.json"), laget)
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
    doms = []
    dom = epostdomene(k.get("epost", ""))
    if dom and dom not in GENERISKE_EPOSTDOMENER and not REGNSKAP_ORD.search(dom):
        doms.append(dom)
    base = slugify(k["navn"])
    for variant in (base.replace("-", ""), base):
        if len(variant) >= 4:
            doms.append(variant + ".no")
    return list(dict.fromkeys(doms))


def kmd_nettsjekk(args, cfg):
    sti = os.path.join(DATA, "kandidater.json")
    k = les_json(sti, {"kandidater": []})
    utelat = les_json(os.path.join(DATA, "utelat.json"), {})
    nokkelord = lambda navn: [w for w in fold(navn).split() if len(w) >= 4]  # noqa: E731
    for kand in k["kandidater"]:
        ord_ = nokkelord(kand["navn"])
        for dom in domener_a_sjekke(kand):
            html_ = None
            for url in (f"https://{dom}", f"https://www.{dom}", f"http://{dom}"):
                html_ = hent_side(url)
                if html_:
                    break
            if not html_:
                continue
            tekst = fold(html_)
            if PARKERING.search(html_) and len(html_) < 20000:
                continue
            if any(w in tekst for w in ord_) or dom == epostdomene(kand.get("epost", "")):
                utelat[kand["orgnr"]] = f"har trolig nettside: {dom}"
                break
            kand["flagg"].append(f"{dom} svarer – sjekk om det er deres side")
    skriv_json(sti, k)
    skriv_json(os.path.join(DATA, "utelat.json"), utelat)
    print(f"Nettsjekk: {len(utelat)} utelatt")


# ---------- morgenrapport på e-post ----------

def kmd_epost(args, cfg):
    import smtplib
    from email.message import EmailMessage
    bruker, passord = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
    if not bruker or not passord:
        sys.exit("Mangler GMAIL_USER / GMAIL_APP_PASSWORD – rapporten ble ikke sendt.")
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
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_kontekst()) as s:
        s.login(bruker, passord)
        s.send_message(msg)
    print("Morgenrapport sendt til", msg["To"])


def kmd_gjenskap(args, cfg):
    """Lager morgenrapporten på nytt for demoer laget en gitt dato (f.eks. hvis e-posten feilet)."""
    idag = dt.date.today()
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
        kand["utkast"] = maler.utkast(kand, cfg)
        leads.append(kand)
    leads.sort(key=lambda k: -k["poeng"])
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
    g = sub.add_parser("gjenskap")
    g.add_argument("dato", help="YYYY-MM-DD")
    sl = sub.add_parser("slett")
    sl.add_argument("orgnr", help="kommaseparerte orgnr som har takket nei")
    args = p.parse_args()
    cfg = les_json(os.path.join(ROT, "config.json"), None)
    if cfg is None:
        sys.exit("Fant ikke config.json")
    {"hent": kmd_hent, "bygg": kmd_bygg, "slett": kmd_slett,
     "nettsjekk": kmd_nettsjekk, "epost": kmd_epost, "gjenskap": kmd_gjenskap}[args.kmd](args, cfg)


if __name__ == "__main__":
    main()
