"""Premium-mal for frisører og skjønnhetssalonger: tre stilvarianter, bilder fra Pexels (valgfritt)."""
import hashlib
import html
import urllib.parse

E = html.escape

INNHOLD = {
    "frisor": {
        "kicker": "Frisørsalong i {sted}",
        "tagline": ["Hår som kler deg", "Hverdagshår, gjort vakkert", "Din faste stol i {sted}"],
        "ingress": "Klipp, farge og styling med god tid og ærlige råd. Vi lager frisyrer som er like fine dag fem som dag én.",
        "meny": [
            ("Dameklipp", "Vask, klipp og føn", "fra 690"),
            ("Herreklipp", "Klipp med maskin og saks", "fra 450"),
            ("Barneklipp", "Til og med 12 år", "fra 350"),
            ("Helfarge", "Inkl. pleiebehandling", "fra 1 190"),
            ("Balayage / striper", "Etter konsultasjon", "fra 1 690"),
            ("Oppsett og styling", "Bryllup, konfirmasjon, fest", "fra 790"),
        ],
        "om": "{navn} er en salong i {sted} der du blir sett og hørt. Vi tar oss tid til en ordentlig prat før saksen kommer frem – og sender deg hjem med tips til hvordan du får det til selv.",
        "verdier": [("Konsultasjon", "Vi starter alltid med en prat om ønsker, hårtype og hverdag."),
                    ("Skånsomme produkter", "Farger og pleie som tar vare på håret over tid."),
                    ("Lett å stelle", "Frisyrer som fungerer også når du gjør den selv.")],
        "cta": "Bestill time",
        "sok": ["hair salon interior", "hairdresser styling hair", "hair stylist cutting hair",
                "hair color salon", "barber shop interior"],
    },
    "skjonnhet": {
        "kicker": "Hud- og skjønnhetspleie i {sted}",
        "tagline": ["Ta en pause – for deg", "Pleie med tid og ro", "Vakker hud, rolig sinn"],
        "ingress": "Behandlinger for ansikt, vipper, bryn og negler i rolige omgivelser. Vi tilpasser alt til huden din og det du ønsker.",
        "meny": [
            ("Ansiktsbehandling", "Rens, peeling, maske og massasje", "fra 890"),
            ("Vipper og bryn", "Farge, forming og lift", "fra 490"),
            ("Manikyr", "Fil, neglebånd og lakk", "fra 590"),
            ("Pedikyr", "Fotbad, hard hud og lakk", "fra 690"),
            ("Voksing", "Ben, armer og ansikt", "fra 290"),
            ("Gavekort", "Valgfritt beløp", "—"),
        ],
        "om": "{navn} holder til i {sted}. Hos oss skal du kunne senke skuldrene, få god veiledning og gå ut med hud og negler du er fornøyd med.",
        "verdier": [("Personlig veiledning", "Vi anbefaler bare det huden din faktisk trenger."),
                    ("Kvalitetsprodukter", "Utvalgte merker vi kjenner godt og stoler på."),
                    ("Rolig atmosfære", "En time for deg selv, uten stress.")],
        "cta": "Bestill behandling",
        "sok": ["beauty salon interior", "facial treatment spa", "manicure nails salon",
                "eyelash beauty treatment", "spa relaxing skincare"],
    },
}

# Tre stilvarianter. (bakgrunn, flate, tekst, dempet, aksent, aksent-tekst, display-font-css, font-url)
VARIANTER = {
    "editorial": ("#F7F3EE", "#EDE6DD", "#1E1A17", "#6B625A", "#7A4E36", "#FFFFFF",
                  "'Cormorant Garamond', 'Iowan Old Style', Georgia, serif",
                  "Cormorant+Garamond:ital,wght@0,500;0,600;1,500"),
    "natt": ("#141211", "#1F1C1A", "#F3EDE4", "#A99F93", "#C8A46A", "#141211",
             "'Playfair Display', 'Didot', Georgia, serif",
             "Playfair+Display:ital,wght@0,500;0,700;1,500"),
    "myk": ("#F6ECE6", "#EEDDD3", "#3B2A2A", "#806A66", "#B76E68", "#FFFFFF",
            "'Fraunces', 'Iowan Old Style', Georgia, serif",
            "Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400"),
}


def variant_for(orgnr):
    navn = list(VARIANTER)
    return navn[int(hashlib.sha1(orgnr.encode()).hexdigest(), 16) % len(navn)]


def _bilde(b, klasse, plassholder_tekst, i):
    if b:
        return (f'<figure class="{klasse}"><img src="{E(b["src"])}" alt="{E(b.get("alt") or "")}" loading="lazy">'
                f'</figure>')
    return (f'<figure class="{klasse} tom t{i % 3}"><span>{E(plassholder_tekst)}</span></figure>')


def demo(k, cfg):
    inn = INNHOLD[k["mal"]]
    vnavn = k.get("variant") or variant_for(k["orgnr"])
    bg, flate, tekst, dempet, aksent, aksent_tekst, display, font_url = VARIANTER[vnavn]
    sted = k.get("poststed") or "Bergen"
    navn = k["navn"]
    fyll = lambda s: s.format(navn=navn, sted=sted)  # noqa: E731
    h = int(hashlib.sha1(k["orgnr"].encode()).hexdigest(), 16)
    tagline = fyll(inn["tagline"][h % len(inn["tagline"])])
    selger = cfg["selger"]
    tlf = k.get("telefon", "")
    tlf_lenke = "tel:+47" + tlf.replace(" ", "") if tlf else "#kontakt"
    epost = k.get("epost", "")
    adresse = ", ".join(x for x in (k.get("adresse"), f"{k.get('postnummer', '')} {sted}".strip()) if x)
    kart = "https://www.google.com/maps?output=embed&q=" + urllib.parse.quote(f"{adresse}")
    bilder = (k.get("bilder") or []) + [None] * 5
    b = bilder[:5]
    meny = "".join(
        f'<li><div><strong>{E(t)}</strong><span>{E(d)}</span></div><i></i><em>{E(p)}{" kr" if p[0].isdigit() or p.startswith("fra") else ""}</em></li>'
        for t, d, p in inn["meny"])
    verdier = "".join(f'<div class="verdi"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in inn["verdier"])
    sett_ = {}
    for x in k.get("bilder") or []:
        if x.get("fotograf"):
            sett_[x["fotograf"]] = x
    kreditt_html = ""
    if sett_:
        deler = [f'<a href="{E(x.get("fotograf_url") or "#")}">{E(n)}</a>' for n, x in sett_.items()]
        kilde = next(iter(sett_.values()))
        kreditt_html = (f' · Eksempelbilder av {", ".join(deler)} på '
                        f'<a href="{E(kilde.get("kilde_url") or "#")}">{E(kilde.get("kilde") or "")}</a>')
    kontakt = []
    if tlf:
        kontakt.append(f'<p><span>Telefon</span><a href="{tlf_lenke}">{E(tlf)}</a></p>')
    if epost:
        kontakt.append(f'<p><span>E-post</span><a href="mailto:{E(epost)}">{E(epost)}</a></p>')
    if adresse:
        kontakt.append(f'<p><span>Adresse</span>{E(adresse)}</p>')
    kontakt.append('<p><span>Åpningstider</span>Tir–fre 10–18 · Lør 10–15 <em>(eksempel)</em></p>')
    init = "".join(w[0] for w in navn.split() if w[:1].isalpha() and not w.islower())[:2].upper() or "•"

    return f"""<!doctype html>
<html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{E(navn)} – {E(tagline)} (forslag)</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={font_url}&family=Jost:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:{bg};--flate:{flate};--tekst:{tekst};--dempet:{dempet};--aksent:{aksent};--aksent-tekst:{aksent_tekst};--display:{display}}}
*{{box-sizing:border-box;margin:0}}html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--tekst);font:17px/1.65 'Jost',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}img{{display:block;width:100%;height:100%;object-fit:cover}}
.demo{{background:var(--tekst);color:var(--bg);font-size:13px;letter-spacing:.02em;padding:9px 20px;text-align:center}}
.demo a{{color:var(--bg);font-weight:500}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 28px}}
header{{display:flex;align-items:center;justify-content:space-between;padding:26px 0}}
.logo{{display:flex;align-items:center;gap:14px;text-decoration:none;font-family:var(--display);font-size:24px;font-weight:600;letter-spacing:.01em}}
.mono{{width:46px;height:46px;border:1px solid var(--tekst);border-radius:50%;display:grid;place-items:center;font-size:17px;letter-spacing:.06em}}
nav a{{margin-left:30px;text-decoration:none;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--dempet)}}
nav a:hover{{color:var(--tekst)}}
.knapp{{display:inline-block;background:var(--aksent);color:var(--aksent-tekst);text-decoration:none;padding:15px 30px;font-size:13px;letter-spacing:.16em;text-transform:uppercase;transition:opacity .2s}}
.knapp:hover{{opacity:.85}}.knapp.strek{{background:none;color:var(--tekst);border:1px solid var(--tekst)}}
.kicker{{font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--aksent)}}
h1,h2,h3{{font-family:var(--display);font-weight:500;letter-spacing:-.01em}}
h1{{font-size:clamp(46px,7vw,96px);line-height:.98;margin:18px 0 26px}}
h1 em,h2 em{{font-style:italic;color:var(--aksent)}}
h2{{font-size:clamp(34px,4.4vw,56px);line-height:1.05;margin:14px 0 22px}}
.ingress{{font-size:19px;color:var(--dempet);max-width:36ch;margin-bottom:34px}}
.handling{{display:flex;gap:12px;flex-wrap:wrap}}
section{{padding:110px 0}}
.flate{{background:var(--flate)}}
figure{{overflow:hidden;background:var(--flate);position:relative}}
figure.tom span{{position:absolute;inset:auto 18px 16px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--dempet)}}
figure.tom.t0{{background:radial-gradient(120% 90% at 20% 10%,color-mix(in srgb,var(--aksent) 35%,var(--flate)),var(--flate) 60%)}}
figure.tom.t1{{background:linear-gradient(160deg,var(--flate),color-mix(in srgb,var(--aksent) 25%,var(--flate)))}}
figure.tom.t2{{background:radial-gradient(90% 120% at 90% 90%,color-mix(in srgb,var(--tekst) 12%,var(--flate)),var(--flate) 70%)}}
/* --- variant: editorial --- */
.v-editorial .hero{{display:grid;grid-template-columns:1.05fr .95fr;gap:64px;align-items:end;padding:40px 0 100px}}
.v-editorial .hero figure{{aspect-ratio:4/5}}
.v-editorial .stripe{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}
.v-editorial .stripe figure{{aspect-ratio:3/4}}
.v-editorial h1{{border-top:1px solid var(--tekst);padding-top:26px}}
/* --- variant: natt --- */
.v-natt .hero{{position:relative;min-height:86vh;display:flex;align-items:flex-end;padding:0 0 90px}}
.v-natt .hero figure{{position:absolute;inset:0}}
.v-natt .hero figure::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,18,17,.25),rgba(20,18,17,.92))}}
.v-natt .hero .tekst{{position:relative;z-index:1;max-width:760px}}
.v-natt .stripe{{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px}}
.v-natt .stripe figure{{aspect-ratio:auto;height:420px}}
.v-natt nav a,.v-natt .logo{{position:relative;z-index:2}}
/* --- variant: myk --- */
.v-myk .hero{{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center;padding:30px 0 100px}}
.v-myk .hero figure{{aspect-ratio:4/5;border-radius:999px 999px 24px 24px}}
.v-myk .stripe{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.v-myk .stripe figure{{aspect-ratio:1;border-radius:50%}}
.v-myk .knapp{{border-radius:999px}}
.v-myk .stripe figure.tom span{{inset:auto 0 46%;text-align:center}}
/* --- felles seksjoner --- */
.meny{{display:grid;grid-template-columns:.8fr 1.2fr;gap:70px}}
.meny ul{{list-style:none;padding:0}}
.meny li{{display:flex;align-items:baseline;gap:14px;padding:20px 0;border-bottom:1px solid color-mix(in srgb,var(--tekst) 14%,transparent)}}
.meny li div{{display:flex;flex-direction:column}}.meny li strong{{font-family:var(--display);font-size:24px;font-weight:500}}
.meny li span{{font-size:14px;color:var(--dempet)}}.meny li i{{flex:1}}.meny li em{{font-style:normal;font-size:16px;white-space:nowrap}}
.merk{{font-size:13px;color:var(--dempet);margin-top:16px}}
.om{{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center}}
.om figure{{aspect-ratio:5/6}}
.om p.stor{{font-family:var(--display);font-size:clamp(24px,2.4vw,32px);line-height:1.35;margin-bottom:34px}}
.verdier{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:10px}}
.verdi h3{{font-size:22px;margin-bottom:6px}}.verdi p{{font-size:15px;color:var(--dempet)}}
.insta{{text-align:center}}.insta p{{color:var(--dempet);max-width:46ch;margin:0 auto 28px}}
.kontakt{{display:grid;grid-template-columns:1fr 1.1fr;gap:64px}}
.kontakt p{{display:flex;flex-direction:column;padding:16px 0;border-bottom:1px solid color-mix(in srgb,var(--tekst) 14%,transparent);font-size:18px}}
.kontakt p span{{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--dempet)}}
.kontakt p em{{font-size:13px;color:var(--dempet)}}
.kart{{min-height:380px;background:var(--flate);filter:grayscale(.6) contrast(1.05)}}
.kart iframe{{width:100%;height:100%;min-height:380px;border:0}}
footer{{padding:34px 0;font-size:13px;color:var(--dempet)}}
@media(max-width:900px){{.v-editorial .hero,.v-myk .hero,.meny,.om,.kontakt{{grid-template-columns:1fr;gap:40px}}
 nav{{display:none}}.verdier{{grid-template-columns:1fr}}.v-natt .stripe{{grid-template-columns:1fr 1fr}}
 .v-natt .stripe figure:first-child{{grid-column:1/-1}}section{{padding:80px 0}}}}
</style></head>
<body class="v-{vnavn}">
<div class="demo">Forslag til nettside for {E(navn)}, laget av {E(selger['navn'])} – ikke bedriftens offisielle side.
Interessert? <a href="tel:{E(selger['telefon'].replace(' ', ''))}">{E(selger['telefon'])}</a> · <a href="mailto:{E(selger['epost'])}">{E(selger['epost'])}</a></div>
{'<div class="hero">' + _bilde(b[0], "", "Deres beste bilde her", 0) + '<div class="wrap" style="width:100%"><header><a class="logo" href="#"><span class="mono">' + E(init) + '</span>' + E(navn) + '</a><nav><a href="#meny">Priser</a><a href="#om">Om oss</a><a href="#kontakt">Kontakt</a></nav></header><div class="tekst"><span class="kicker">' + E(fyll(inn["kicker"])) + '</span><h1>' + E(tagline) + '</h1><p class="ingress">' + E(fyll(inn["ingress"])) + '</p><div class="handling"><a class="knapp" href="' + tlf_lenke + '">' + E(inn["cta"]) + '</a><a class="knapp strek" href="#meny">Se priser</a></div></div></div></div>' if vnavn == "natt" else
'<div class="wrap"><header><a class="logo" href="#"><span class="mono">' + E(init) + '</span>' + E(navn) + '</a><nav><a href="#meny">Priser</a><a href="#om">Om oss</a><a href="#kontakt">Kontakt</a></nav></header><div class="hero"><div><span class="kicker">' + E(fyll(inn["kicker"])) + '</span><h1>' + E(tagline) + '</h1><p class="ingress">' + E(fyll(inn["ingress"])) + '</p><div class="handling"><a class="knapp" href="' + tlf_lenke + '">' + E(inn["cta"]) + '</a><a class="knapp strek" href="#meny">Se priser</a></div></div>' + _bilde(b[0], "", "Deres beste bilde her", 0) + '</div></div>'}
<section class="flate"><div class="wrap stripe">{_bilde(b[1], "", "Bilde fra salongen", 1)}{_bilde(b[2], "", "Før / etter", 2)}{_bilde(b[3], "", "Teamet", 0)}</div></section>
<section id="meny"><div class="wrap meny"><div><span class="kicker">Behandlinger</span><h2>Priser og <em>tjenester</em></h2>
<p class="ingress">Alle priser er veiledende. Ta kontakt for et uforpliktende tilbud.</p>
<a class="knapp" href="{tlf_lenke}">{E(inn['cta'])}</a></div><div><ul>{meny}</ul><p class="merk">Eksempelpriser – byttes ut med salongens egne.</p></div></div></section>
<section id="om" class="flate"><div class="wrap om">{_bilde(b[4], "", "Portrett av eier", 1)}<div><span class="kicker">Om oss</span><h2>Velkommen til <em>{E(navn)}</em></h2>
<p class="stor">{E(fyll(inn['om']))}</p><div class="verdier">{verdier}</div></div></div></section>
<section class="insta"><div class="wrap"><span class="kicker">Instagram</span><h2>Følg oss for <em>inspirasjon</em></h2>
<p>Her vises de siste innleggene fra salongens egen Instagram-konto – automatisk oppdatert.</p>
<a class="knapp strek" href="#kontakt">Kobles til ved oppstart</a></div></section>
<section id="kontakt" class="flate"><div class="wrap kontakt"><div><span class="kicker">Kontakt</span><h2>Finn <em>oss</em></h2>{''.join(kontakt)}
<p style="border:0;padding-top:28px"><a class="knapp" href="{tlf_lenke}">{E(inn['cta'])}</a></p></div>
<div class="kart"><iframe loading="lazy" src="{E(kart)}" title="Kart"></iframe></div></div></section>
<footer class="wrap">© {E(navn)} · Org.nr. {E(k['orgnr'])}{kreditt_html}</footer>
</body></html>"""
