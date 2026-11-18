"""Premium-mal for håndverkere: rørlegger, elektriker, maler og snekker.

Energi og tillit: stor hero med bildecollage, glidende tjenestebånd, ikoner, «slik jobber vi»,
områdeoversikt med kart og et tilbudsskjema som åpner e-post. Bilder fra Unsplash (verktøy/materialer).
"""
import hashlib
import html
import urllib.parse

E = html.escape

BYDELER = ["Sentrum", "Bergenhus", "Årstad", "Fana", "Ytrebygda", "Fyllingsdalen",
           "Laksevåg", "Åsane", "Arna", "Askøy", "Os", "Sotra"]

# Enkle strek-ikoner (24x24), tegnet med currentColor
IKON = {
    "drape": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "bad": '<path d="M4 12h16v3a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5v-3zM6 12V6a2 2 0 0 1 4 0"/><path d="M8 20l-1 2M16 20l1 2"/>',
    "varme": '<path d="M12 3v10M8 7c0-2 1.8-4 4-4s4 2 4 4v6a5 5 0 1 1-8 0V7z"/>',
    "ror": '<path d="M3 8h8v8H3zM11 12h6a4 4 0 0 1 4 4v4"/>',
    "lyn": '<path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>',
    "plugg": '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0V8zM12 18v4"/>',
    "hus": '<path d="M3 11l9-8 9 8M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "skjold": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    "rulle": '<path d="M4 4h13v5H4zM17 6h3v6h-8v3"/><path d="M11 15h2v6h-2z"/>',
    "pensel": '<path d="M18 3l3 3-9 9-3-3 9-9zM9 12l-4 4c-1 1-1 3-3 4 2 0 4 0 5-1l4-4"/>',
    "hammer": '<path d="M14 4l6 6-3 3-6-6 3-3zM11 7l-8 8 3 3 8-8"/>',
    "vindu": '<path d="M4 3h16v18H4zM4 12h16M12 3v18"/>',
    "terrasse": '<path d="M3 13h18M5 13v7M19 13v7M3 17h18M7 4l5 4 5-4"/>',
    "sjekk": '<path d="M5 12l4 4L19 6"/>',
}


def ikon(navn, str_=22):
    return (f'<svg width="{str_}" height="{str_}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{IKON[navn]}</svg>')


INNHOLD = {
    "rorlegger": {
        "kicker": "Rørlegger i {sted}",
        "tagline": ["Rørlegger du faktisk får tak i", "Bad, lekkasje og varme – fikset", "Tett, trygt og ryddig"],
        "ingress": "Fra lekkasje en søndag kveld til nytt bad fra bunnen av. Vi kommer når vi sier vi kommer, gir fast pris og rydder etter oss.",
        "tillit": ["Fast pris på oppdraget", "Godkjent våtromsbedrift", "Akutt hjelp ved lekkasje"],
        "band": ["Bad og våtrom", "Lekkasje", "Varmtvannsbereder", "Sluk og avløp", "Vannbåren varme", "Kjøkken", "Service"],
        "tjenester": [("bad", "Bad og våtrom", "Totalrenovering eller nytt sluk, servant og dusj – dokumentert etter forskriftene."),
                      ("drape", "Lekkasje og akutt", "Lekker det? Ring, så prioriterer vi akutte oppdrag."),
                      ("varme", "Varmtvann og varme", "Bytte av bereder, varmekabler og vannbåren varme."),
                      ("ror", "Sluk og avløp", "Tette rør, lukt eller dårlig avrenning – vi finner årsaken.")],
        "sok": ["copper pipes plumbing", "modern bathroom tiles", "plumber tools wrench"],
        "palett": ("lys", "#F1F5F8", "#E2EAF0", "#0F2233", "#5A6B7B", "#0E7AC4", "#FFFFFF"),
    },
    "elektriker": {
        "kicker": "Elektriker i {sted}",
        "tagline": ["Strøm du kan stole på", "Trygt, ryddig og riktig koblet", "Fra sikringsskap til smarthus"],
        "ingress": "Vi gjør det elektriske trygt – med samsvarserklæring på alt. Elbillader, nytt sikringsskap, smarthus eller feilsøking.",
        "tillit": ["Samsvarserklæring på alt", "Fast pris eller timepris", "Rask feilsøking"],
        "band": ["Sikringsskap", "Elbillader", "Smarthus", "Feilsøking", "Belysning", "Varmekabler", "Termografi"],
        "tjenester": [("skjold", "Sikringsskap", "Moderne skap med jordfeilbrytere og overspenningsvern."),
                      ("plugg", "Elbillader", "Riktig lader til bilen og sikringsskapet ditt – montert og meldt."),
                      ("hus", "Smarthus", "Styr lys og varme fra mobilen og spar strøm."),
                      ("lyn", "Feilsøking", "Går sikringen? Vi finner feilen før den blir et problem.")],
        "sok": ["electrical wiring tools", "electrician tools pliers", "modern lighting interior"],
        "palett": ("mork", "#121417", "#1B1F24", "#F2F2EF", "#9AA3AD", "#FFC21A", "#121417"),
    },
    "maler": {
        "kicker": "Maler i {sted}",
        "tagline": ["Farger som tåler Bergensværet", "Rene linjer, inne og ute", "Grundig forarbeid. Vakkert resultat."],
        "ingress": "Utvendig maling som holder i vestlandsklima, og innvendig arbeid med presise kanter. Vi skjermer, sparkler og rydder.",
        "tillit": ["Gratis befaring", "Fast pris etter befaring", "Grundig forarbeid"],
        "band": ["Utvendig maling", "Innvendig maling", "Tapetsering", "Sparkling", "Vinduer", "Gjerder", "Fargeråd"],
        "tjenester": [("hus", "Utvendig maling", "Vask, skraping og maling av kledning, vinduer og gjerder."),
                      ("rulle", "Innvendig maling", "Vegger, tak og listverk med rene linjer."),
                      ("pensel", "Tapetsering", "Fra fototapet til klassisk mønster – satt opp med presisjon."),
                      ("sjekk", "Sparkling", "Jevne flater før maling. Det er her kvaliteten avgjøres.")],
        "sok": ["paint roller wall", "paint brushes cans", "paint color swatches"],
        "palett": ("lys", "#F7F4EF", "#ECE5DB", "#22303A", "#66717A", "#D2553A", "#FFFFFF"),
    },
    "snekker": {
        "kicker": "Snekker i {sted}",
        "tagline": ["Solid håndverk, fra plan til ferdig", "Vi bygger det du ser for deg", "Godt snekkerarbeid varer"],
        "ingress": "Oppussing, tilbygg, terrasser og innredning. Vi tar hele jobben – eller den delen du trenger hjelp til – og holder deg oppdatert underveis.",
        "tillit": ["Gratis befaring", "Fast pris eller timepris", "Ryddig byggeplass"],
        "band": ["Oppussing", "Tilbygg", "Terrasse", "Kjøkken", "Vinduer og dører", "Gulv", "Garderobe"],
        "tjenester": [("hammer", "Oppussing", "Nye gulv, vegger og himlinger – vi koordinerer gjerne andre fag."),
                      ("hus", "Kjøkken og innredning", "Montering av kjøkken, garderober og skreddersydde løsninger."),
                      ("terrasse", "Terrasse og uteområde", "Terrasser, levegger og boder som tåler vær og vind."),
                      ("vindu", "Vinduer og dører", "Utskifting som gir bedre isolasjon og lavere strømregning.")],
        "sok": ["woodworking tools workbench", "wood planks timber", "carpentry tools"],
        "palett": ("lys", "#F4EFE8", "#EAE2D6", "#231C15", "#6E6358", "#C0612B", "#FFFFFF"),
    },
}


def innhold_for(k):
    return INNHOLD[k["mal"]]


def _bilde(b, klasse=""):
    if b:
        return (f'<figure class="{klasse}"><img src="{E(b["src"])}" alt="{E(b.get("alt") or "")}" loading="lazy">'
                f'<small class="eks">Eksempelbilde</small></figure>')
    return f'<figure class="{klasse} tom"><span>Deres prosjektbilde her</span></figure>'


def demo(k, cfg):
    inn = innhold_for(k)
    modus, bg, flate, tekst, dempet, aksent, aksent_tekst = inn["palett"]
    sted = k.get("poststed") or "Bergen"
    navn = k["navn"]
    h = int(hashlib.sha1(k["orgnr"].encode()).hexdigest(), 16)
    tagline = inn["tagline"][h % len(inn["tagline"])]
    selger = cfg["selger"]
    tlf = k.get("telefon", "")
    tlf_lenke = "tel:+47" + tlf.replace(" ", "") if tlf else "#tilbud"
    epost = k.get("epost", "")
    adresse = ", ".join(x for x in (k.get("adresse"), f"{k.get('postnummer', '')} {sted}".strip()) if x)
    kart = "https://www.google.com/maps?output=embed&q=" + urllib.parse.quote(adresse or f"{navn} {sted}")
    b = ((k.get("bilder") or []) + [None] * 5)[:5]
    init = "".join(w[0] for w in navn.split() if w[:1].isalpha() and not w.islower())[:2].upper() or "•"
    band = "".join(f"<span>{E(x)}</span><i>✦</i>" for x in inn["band"]) * 2
    tillit = "".join(f"<li>{ikon('sjekk', 18)}{E(x)}</li>" for x in inn["tillit"])
    tjenester = "".join(f'<article class="tj"><div class="ik">{ikon(i, 26)}</div><h3>{E(t)}</h3><p>{E(d)}</p>'
                        f'<a href="#tilbud">Få pris →</a></article>' for i, t, d in inn["tjenester"])
    steg = [("Befaring", f"Vi kommer på befaring i {sted} og ser på jobben sammen med deg – uforpliktende."),
            ("Fast pris", "Du får et skriftlig tilbud med tydelig pris og tidsplan. Ingen overraskelser."),
            ("Ferdig jobb", "Vi gjør jobben, rydder etter oss og dokumenterer det som skal dokumenteres.")]
    steg_html = "".join(f'<div class="steg"><b>0{i + 1}</b><h3>{E(t)}</h3><p>{E(d)}</p></div>' for i, (t, d) in enumerate(steg))
    omrade = "".join(f"<span>{E(x)}</span>" for x in BYDELER)
    kreditt = {x["fotograf"]: x for x in k.get("bilder") or [] if x.get("fotograf")}
    kreditt_html = ""
    if kreditt:
        deler = ", ".join(f'<a href="{E(x.get("fotograf_url") or "#")}">{E(n)}</a>' for n, x in kreditt.items())
        kilde = next(iter(kreditt.values()))
        kreditt_html = f' · Eksempelbilder av {deler} på <a href="{E(kilde.get("kilde_url") or "#")}">{E(kilde.get("kilde") or "")}</a>'
    skjema_til = epost or selger["epost"]
    mork = modus == "mork"

    return f"""<!doctype html>
<html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{E(navn)} – {E(tagline)} (forslag)</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,500;75..125,800&family=Inter+Tight:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:{bg};--flate:{flate};--tekst:{tekst};--dempet:{dempet};--aksent:{aksent};--aksent-tekst:{aksent_tekst};
--linje:color-mix(in srgb,var(--tekst) 13%,transparent);--display:'Archivo','Helvetica Neue',Arial,sans-serif}}
*{{box-sizing:border-box;margin:0}}html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--tekst);font:17px/1.6 'Inter Tight',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}img{{display:block;width:100%;height:100%;object-fit:cover}}
.demo{{background:var(--tekst);color:var(--bg);font-size:13px;padding:9px 20px;text-align:center}}.demo a{{color:var(--bg);font-weight:600}}
.wrap{{max-width:1200px;margin:0 auto;padding:0 28px}}
header{{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--linje)}}
.hdr{{display:flex;align-items:center;justify-content:space-between;height:74px}}
.logo{{display:flex;align-items:center;gap:12px;text-decoration:none;font-family:var(--display);font-weight:800;font-stretch:90%;font-size:21px;letter-spacing:-.01em}}
.mono{{width:40px;height:40px;border-radius:10px;background:var(--aksent);color:var(--aksent-tekst);display:grid;place-items:center;font-size:15px}}
nav{{display:flex;align-items:center;gap:28px}}nav a{{text-decoration:none;font-weight:500;font-size:15px;color:var(--dempet)}}nav a:hover{{color:var(--tekst)}}
.knapp{{display:inline-flex;align-items:center;gap:10px;background:var(--aksent);color:var(--aksent-tekst);text-decoration:none;font-weight:600;
 padding:15px 24px;border-radius:12px;border:0;cursor:pointer;font:600 16px 'Inter Tight',sans-serif;transition:transform .15s,box-shadow .15s}}
.knapp:hover{{transform:translateY(-2px);box-shadow:0 10px 24px -10px var(--aksent)}}
.knapp.lys{{background:transparent;color:var(--tekst);border:1.5px solid var(--linje)}}
nav .knapp{{padding:11px 18px;font-size:15px;color:var(--aksent-tekst);white-space:nowrap}}
.hero{{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center;padding-top:72px;padding-bottom:84px}}
.kicker{{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--aksent)}}
.kicker::before{{content:"";width:28px;height:3px;background:var(--aksent);border-radius:2px}}
h1,h2,h3{{font-family:var(--display);letter-spacing:-.02em}}
h1{{font-weight:800;font-stretch:85%;font-size:clamp(46px,6.6vw,92px);line-height:.95;margin:18px 0 22px;text-wrap:balance}}
h2{{font-weight:800;font-stretch:88%;font-size:clamp(34px,4.4vw,58px);line-height:1;margin:12px 0 18px;text-wrap:balance}}
.ingress{{font-size:19px;color:var(--dempet);max-width:40ch;margin-bottom:30px}}
.handling{{display:flex;gap:12px;flex-wrap:wrap}}
.tillit{{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:10px 22px;margin-top:30px;font-size:15px;font-weight:500}}
.tillit li{{display:flex;align-items:center;gap:8px}}.tillit svg{{color:var(--aksent)}}
.collage{{position:relative;height:560px}}
.collage figure{{position:absolute;overflow:hidden;border-radius:22px;background:var(--flate)}}
.collage .a{{inset:0 18% 12% 0}}.collage .a .eks{{bottom:auto;top:12px;right:auto;left:12px}}.collage .b{{width:44%;height:46%;right:0;bottom:0;border:6px solid var(--bg)}}
.merke{{position:absolute;left:-18px;bottom:40px;z-index:3;background:var(--bg);border:1px solid var(--linje);border-radius:16px;padding:14px 18px;
 box-shadow:0 20px 40px -20px rgba(0,0,0,.35);display:flex;gap:12px;align-items:center;font-size:14px}}
.merke b{{display:block;font-family:var(--display);font-size:20px}}.merke .ik{{color:var(--aksent)}}
figure{{position:relative;overflow:hidden}}figure.tom{{background:repeating-linear-gradient(135deg,var(--flate) 0 14px,color-mix(in srgb,var(--flate) 70%,var(--bg)) 14px 28px)}}
figure.tom span{{position:absolute;left:16px;bottom:14px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--dempet)}}
.eks{{position:absolute;right:10px;bottom:10px;z-index:2;font-size:10px;letter-spacing:.14em;text-transform:uppercase;background:rgba(0,0,0,.5);color:#fff;padding:3px 8px;border-radius:4px}}
.band{{background:var(--aksent);color:var(--aksent-tekst);overflow:hidden;white-space:nowrap;padding:18px 0;font-family:var(--display);font-weight:800;font-stretch:85%;font-size:26px;text-transform:uppercase;letter-spacing:.01em}}
.band div{{display:inline-flex;gap:28px;animation:gli 38s linear infinite}}.band i{{font-style:normal;opacity:.6}}
@keyframes gli{{to{{transform:translateX(-50%)}}}}
@media(prefers-reduced-motion:reduce){{.band div{{animation:none}}}}
section{{padding:104px 0}}.flate{{background:var(--flate)}}
.topp{{display:flex;justify-content:space-between;align-items:end;gap:30px;margin-bottom:44px;flex-wrap:wrap}}.topp p{{max-width:44ch;color:var(--dempet)}}
.tjgrid{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}}
.tj{{background:var(--bg);border:1px solid var(--linje);border-radius:20px;padding:28px;display:flex;flex-direction:column;gap:10px;transition:transform .2s,border-color .2s}}
.tj:hover{{transform:translateY(-4px);border-color:var(--aksent)}}
.tj .ik{{width:52px;height:52px;border-radius:14px;display:grid;place-items:center;background:color-mix(in srgb,var(--aksent) 14%,transparent);color:var(--aksent);margin-bottom:8px}}
.tj h3{{font-size:22px;font-weight:800;font-stretch:90%}}.tj p{{font-size:15px;color:var(--dempet);flex:1}}.tj a{{font-weight:600;font-size:15px;text-decoration:none;color:var(--aksent)}}
.prosess{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--linje)}}
.steg{{padding:34px 30px 10px 0}}.steg+.steg{{padding-left:30px;border-left:1px solid var(--linje)}}
.steg b{{font-family:var(--display);font-size:56px;font-weight:800;font-stretch:80%;color:var(--aksent);line-height:1}}.steg h3{{font-size:24px;margin:14px 0 8px}}.steg p{{color:var(--dempet)}}
.galleri{{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:16px;height:440px}}.galleri figure{{border-radius:20px;background:var(--flate)}}
.omrade{{display:grid;grid-template-columns:1fr 1.1fr;gap:56px;align-items:center}}
.chips{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.chips span{{border:1px solid var(--linje);border-radius:999px;padding:8px 16px;font-size:15px;font-weight:500;background:var(--bg)}}
.kart{{border-radius:22px;overflow:hidden;min-height:400px;border:1px solid var(--linje);background:var(--bg)}}.kart iframe{{width:100%;height:100%;min-height:400px;border:0;filter:saturate(.75)}}
.tilbud{{display:grid;grid-template-columns:1fr 1fr;gap:56px}}
.tilbud .kontakt p{{display:flex;flex-direction:column;padding:14px 0;border-bottom:1px solid var(--linje);font-size:18px}}
.tilbud .kontakt span{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--dempet)}}
form{{background:var(--bg);border:1px solid var(--linje);border-radius:22px;padding:30px;display:grid;gap:14px}}
label{{display:grid;gap:6px;font-size:14px;font-weight:500;color:var(--dempet)}}
input,textarea{{font:inherit;color:var(--tekst);background:var(--flate);border:1px solid var(--linje);border-radius:12px;padding:13px 14px}}
input:focus,textarea:focus{{outline:2px solid var(--aksent);outline-offset:1px}}textarea{{min-height:110px;resize:vertical}}
form small{{color:var(--dempet);font-size:13px}}
footer{{padding:34px 0;font-size:13px;color:var(--dempet);border-top:1px solid var(--linje)}}
.mobilring{{display:none}}
@media(max-width:960px){{.hero,.omrade,.tilbud{{grid-template-columns:1fr;gap:40px}}.tjgrid{{grid-template-columns:1fr 1fr}}
 .prosess{{grid-template-columns:1fr}}.steg+.steg{{padding-left:0;border-left:0;border-top:1px solid var(--linje)}}
 nav a:not(.knapp){{display:none}}.collage{{height:420px}}.galleri{{grid-template-columns:1fr 1fr;height:auto}}.galleri figure{{height:220px}}
 .galleri figure:first-child{{grid-column:1/-1}}section{{padding:76px 0}}
 .mobilring{{display:flex;position:fixed;left:16px;right:16px;bottom:16px;z-index:30;justify-content:center}}}}
@media(max-width:560px){{.tjgrid{{grid-template-columns:1fr}}.merke{{left:8px}}.logo{{font-size:17px}}.wrap{{padding-left:20px;padding-right:20px}}}}
</style></head>
<body class="{'mork' if mork else 'lys'}">
<div class="demo">Forslag til nettside for {E(navn)}, laget av {E(selger['navn'])} – ikke bedriftens offisielle side.
Interessert? <a href="tel:{E(selger['telefon'].replace(' ', ''))}">{E(selger['telefon'])}</a> · <a href="mailto:{E(selger['epost'])}">{E(selger['epost'])}</a></div>
<header><div class="wrap hdr"><a class="logo" href="#"><span class="mono">{E(init)}</span>{E(navn)}</a>
<nav><a href="#tjenester">Tjenester</a><a href="#slik">Slik jobber vi</a><a href="#omrade">Område</a><a class="knapp" href="#tilbud">Få tilbud</a></nav></div></header>
<div class="wrap hero"><div><span class="kicker">{E(inn['kicker'].format(sted=sted))}</span><h1>{E(tagline)}</h1>
<p class="ingress">{E(inn['ingress'])}</p>
<div class="handling"><a class="knapp" href="#tilbud">Få gratis tilbud</a>{f'<a class="knapp lys" href="{tlf_lenke}">Ring {E(tlf)}</a>' if tlf else ''}</div>
<ul class="tillit">{tillit}</ul></div>
<div class="collage">{_bilde(b[0], "a")}{_bilde(b[1], "b")}
<div class="merke"><span class="ik">{ikon('skjold', 30)}</span><div><b>Gratis befaring</b>Svar innen 24 timer</div></div></div></div>
<div class="band" aria-hidden="true"><div>{band}</div></div>
<section id="tjenester" class="flate"><div class="wrap"><div class="topp"><div><span class="kicker">Tjenester</span><h2>Dette hjelper vi deg med</h2></div>
<p>Små og store oppdrag for privatkunder, borettslag og bedrifter i {E(sted)} og omegn.</p></div><div class="tjgrid">{tjenester}</div></div></section>
<section id="slik"><div class="wrap"><span class="kicker">Slik jobber vi</span><h2>Enkelt fra første telefon til ferdig jobb</h2><div class="prosess">{steg_html}</div></div></section>
<section class="flate" style="padding-top:0;padding-bottom:0;background:none"><div class="wrap galleri">{_bilde(b[2])}{_bilde(b[3])}{_bilde(b[4])}</div></section>
<section id="omrade"><div class="wrap omrade"><div><span class="kicker">Område</span><h2>Vi dekker hele Bergen</h2>
<p style="color:var(--dempet)">Vi holder til i {E(adresse or sted)} og tar oppdrag i hele Bergensområdet.</p><div class="chips">{omrade}</div></div>
<div class="kart"><iframe loading="lazy" src="{E(kart)}" title="Kart"></iframe></div></div></section>
<section id="tilbud" class="flate"><div class="wrap tilbud"><div><span class="kicker">Kontakt</span><h2>Få et uforpliktende tilbud</h2>
<div class="kontakt">{f'<p><span>Telefon</span><a href="{tlf_lenke}">{E(tlf)}</a></p>' if tlf else ''}{f'<p><span>E-post</span><a href="mailto:{E(epost)}">{E(epost)}</a></p>' if epost else ''}
{f'<p><span>Adresse</span>{E(adresse)}</p>' if adresse else ''}<p><span>Åpningstider</span>Man–fre 07–16 (eksempel)</p></div></div>
<form onsubmit="event.preventDefault();var f=this;location.href='mailto:{E(skjema_til)}?subject='+encodeURIComponent('Forespørsel fra nettsiden')+'&body='+encodeURIComponent('Navn: '+f.n.value+'\\nTelefon: '+f.t.value+'\\n\\n'+f.m.value)">
<label>Navn<input name="n" required autocomplete="name"></label><label>Telefon<input name="t" type="tel" required autocomplete="tel"></label>
<label>Hva gjelder det?<textarea name="m" placeholder="Fortell kort om jobben – gjerne med adresse"></textarea></label>
<button class="knapp" type="submit">Send forespørsel</button><small>Forespørselen går rett til {E(navn)} på e-post.</small></form></div></section>
<footer><div class="wrap">© {E(navn)} · Org.nr. {E(k['orgnr'])}{kreditt_html}</div></footer>
<a class="knapp mobilring" href="{tlf_lenke}">{'Ring ' + E(tlf) if tlf else 'Få tilbud'}</a>
</body></html>"""
