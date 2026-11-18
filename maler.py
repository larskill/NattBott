"""HTML-maler: demo-nettsider, salgsutkast og morgenrapport."""
import html
import urllib.parse

import salong

E = html.escape

# ---------------- innhold per bransje ----------------
# {navn} og {sted} fylles inn. Hold tekstene korte og troverdige.
INNHOLD = {
    "sykkel": {
        "tagline": "Sykkelen din i toppform – hele året",
        "ingress": "Service, reparasjon og vinterklargjøring i {sted}. Rask levering og ærlige priser, enten du sykler til jobb eller til fjells.",
        "usp": ["Fast pris på service", "Piggdekk og vinterpakke", "El-sykkel-kompetanse"],
        "tjenester": [
            ("Service", "Full gjennomgang av gir, bremser, kjede og hjul – fast pris, ferdig på dagen når det er mulig."),
            ("Vinterklargjøring", "Piggdekk, lys og rustbeskyttelse, så du kommer trygt gjennom Bergensvinteren."),
            ("El-sykkel", "Feilsøking, batterisjekk og service på de vanligste merkene."),
            ("Reparasjon", "Punktering, eikebrudd, nye wirer eller bremseklosser – stikk innom."),
        ],
        "om": "{navn} holder til i {sted} og tar imot alt fra barnesykler til terreng- og el-sykler. Vi forklarer hva som må gjøres, og hva som kan vente.",
        "cta": "Bestill service",
        "palett": ("#F4F1EA", "#1B2A2F", "#D9481F", "#FFFFFF"),
        "font": "grotesk",
        "motiv": "sykkel",
    },
    "musikk": {
        "tagline": "Lær å spille – i ditt eget tempo",
        "ingress": "Musikkundervisning for barn, ungdom og voksne i {sted}. Enkelttimer og små grupper, fra første tone til scenen.",
        "usp": ["Alle nivåer", "Gratis prøvetime", "Barn og voksne"],
        "tjenester": [
            ("Enkelttimer", "Undervisning tilpasset deg – mål, musikksmak og tempo bestemmer du selv."),
            ("Barn og unge", "Lekent og motiverende opplegg som bygger gode vaner fra start."),
            ("Voksne nybegynnere", "Aldri for sent å begynne. Vi starter med låtene du har lyst til å spille."),
            ("Konsert og fremføring", "Felles elevkonserter gir noe å øve mot – og mestringsfølelse."),
        ],
        "om": "{navn} tilbyr musikkundervisning i {sted}. Målet er at elevene skal få det gøy med musikken og utvikle seg trygt.",
        "cta": "Book prøvetime",
        "palett": ("#F6F1EC", "#231A2B", "#8C2F39", "#FFFFFF"),
        "font": "serif",
        "motiv": "musikk",
    },
    "frisor": {
        "tagline": "Hår som passer deg og hverdagen din",
        "ingress": "Klipp, farge og styling i {sted}. Vi tar oss tid til å lytte – og gir deg en frisyre som er lett å stelle selv.",
        "usp": ["Dame, herre og barn", "Farge og striper", "Enkel timebestilling"],
        "tjenester": [
            ("Klipp", "Dame, herre og barn – tilpasset ansiktsform, hårtype og hvordan du faktisk vil style det."),
            ("Farge og striper", "Helfarge, balayage og striper med skånsomme produkter."),
            ("Styling", "Oppsett og styling til bryllup, konfirmasjon og fest."),
            ("Skjegg og trim", "Konturklipp og skjeggstell for et ryddig uttrykk."),
        ],
        "om": "{navn} er en frisørsalong i {sted}. Vi vil at du skal gå ut døra og føle deg som deg selv – bare litt bedre.",
        "cta": "Bestill time",
        "palett": ("#F8F2EF", "#2B2024", "#9E5A68", "#FFFFFF"),
        "font": "serif",
        "motiv": "frisor",
    },
    "rorlegger": {
        "tagline": "Rørlegger du kan stole på",
        "ingress": "Bad, lekkasjer og varmtvann i {sted} og omegn. Vi kommer når vi sier vi skal komme, og rydder etter oss.",
        "usp": ["Godkjent våtromsarbeid", "Rask hjelp ved lekkasje", "Fastpris på oppdrag"],
        "tjenester": [
            ("Bad og våtrom", "Totalrenovering eller utskifting av sluk, servant og dusj – dokumentert og etter forskriftene."),
            ("Lekkasje og akutt", "Lekker det? Ring – vi prioriterer akutte oppdrag."),
            ("Varmtvann", "Bytte av varmtvannsbereder, varmekabler og vannbåren varme."),
            ("Sluk og avløp", "Tette rør, lukt eller dårlig avrenning – vi finner årsaken."),
        ],
        "om": "{navn} utfører rørleggerarbeid for privatkunder og bedrifter i {sted}. Ryddig dokumentasjon og tydelige priser.",
        "cta": "Få tilbud",
        "palett": ("#EEF3F6", "#12263A", "#1F6F8B", "#FFFFFF"),
        "font": "grotesk",
        "motiv": "hus",
    },
    "elektriker": {
        "tagline": "Trygg strøm, gjort riktig",
        "ingress": "Elektrikertjenester i {sted}: sikringsskap, elbillader, smarthus og feilsøking – med samsvarserklæring på alt.",
        "usp": ["Samsvarserklæring", "Elbillader", "Rask feilsøking"],
        "tjenester": [
            ("Sikringsskap", "Oppgradering til moderne skap med jordfeilbrytere og overspenningsvern."),
            ("Elbillader", "Montering av lader – vi hjelper med valg av løsning og eventuelle støtteordninger."),
            ("Smarthus", "Styr lys og varme fra mobilen og spar strøm."),
            ("Feilsøking", "Går sikringen? Vi finner feilen før den blir et problem."),
        ],
        "om": "{navn} er elektriker i {sted}. Vi gjør jobben trygt, ryddig og etter gjeldende regler.",
        "cta": "Få tilbud",
        "palett": ("#F5F4EF", "#1A1A1A", "#F2B705", "#1A1A1A"),
        "font": "grotesk",
        "motiv": "hus",
    },
    "maler": {
        "tagline": "Farger som tåler Bergensværet",
        "ingress": "Maling innvendig og utvendig i {sted}. Grundig forarbeid gir et resultat som varer.",
        "usp": ["Inne og ute", "Grundig forarbeid", "Gratis befaring"],
        "tjenester": [
            ("Utvendig maling", "Vask, skraping og maling av kledning, vinduer og gjerder – med produkter for vestlandsklima."),
            ("Innvendig maling", "Vegger, tak og listverk med rene linjer og skjermet møblement."),
            ("Tapetsering", "Fra fototapet til klassisk mønster, satt opp med presisjon."),
            ("Sparkling", "Jevne flater før maling – det er her kvaliteten avgjøres."),
        ],
        "om": "{navn} er malerbedrift i {sted}. Vi gir deg en tydelig pris etter befaring og holder avtalt tidsplan.",
        "cta": "Bestill befaring",
        "palett": ("#F5F1EA", "#26323B", "#C2533A", "#FFFFFF"),
        "font": "grotesk",
        "motiv": "hus",
    },
    "snekker": {
        "tagline": "Solid håndverk, fra plan til ferdig",
        "ingress": "Snekker i {sted} for oppussing, tilbygg, terrasser og innredning. Vi tar hele jobben – eller den delen du trenger hjelp til.",
        "usp": ["Fastpris eller timepris", "Gratis befaring", "Ryddig byggeplass"],
        "tjenester": [
            ("Oppussing", "Nye gulv, vegger og himlinger – vi koordinerer gjerne andre fag."),
            ("Kjøkken og innredning", "Montering av kjøkken, garderober og skreddersydde løsninger."),
            ("Terrasse og uteområde", "Terrasser, levegger og boder som tåler vær og vind."),
            ("Vinduer og dører", "Utskifting som gir bedre isolasjon og lavere strømregning."),
        ],
        "om": "{navn} utfører snekker- og tømrerarbeid i {sted}. Vi er opptatt av gode løsninger, tydelig kommunikasjon og et resultat som varer.",
        "cta": "Bestill befaring",
        "palett": ("#F3EEE6", "#2A2118", "#9A5B26", "#FFFFFF"),
        "font": "serif",
        "motiv": "hus",
    },
}

FONTER = {
    "serif": ("Fraunces:opsz,wght@9..144,500;9..144,700", "'Fraunces', 'Iowan Old Style', Georgia, serif"),
    "grotesk": ("Space+Grotesk:wght@500;700", "'Space Grotesk', 'Avenir Next', 'Segoe UI', sans-serif"),
}


def motiv_svg(motiv, aksent, blekk):
    """Enkle, dekorative SVG-motiver (ingen bilder trengs)."""
    if motiv == "sykkel":
        return f"""<svg viewBox="0 0 400 300" aria-hidden="true"><g fill="none" stroke="{blekk}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
<circle cx="105" cy="200" r="70"/><circle cx="295" cy="200" r="70"/>
<path d="M105 200 L170 95 L270 95 M170 95 L200 200 L105 200 M200 200 L270 95 L295 200 M150 80 h45 M255 70 l15 25 h25"/></g>
<circle cx="200" cy="200" r="14" fill="{aksent}"/><circle cx="105" cy="200" r="9" fill="{aksent}"/><circle cx="295" cy="200" r="9" fill="{aksent}"/></svg>"""
    if motiv == "musikk":
        linjer = "".join(f'<line x1="20" x2="380" y1="{y}" y2="{y}" stroke="{blekk}" stroke-width="3" opacity=".35"/>' for y in (90, 120, 150, 180, 210))
        return f"""<svg viewBox="0 0 400 300" aria-hidden="true">{linjer}
<g fill="{blekk}"><ellipse cx="110" cy="210" rx="26" ry="19" transform="rotate(-20 110 210)"/><rect x="130" y="90" width="7" height="122"/>
<ellipse cx="230" cy="180" rx="26" ry="19" transform="rotate(-20 230 180)"/><ellipse cx="320" cy="150" rx="26" ry="19" transform="rotate(-20 320 150)"/>
<rect x="250" y="62" width="7" height="120"/><rect x="340" y="32" width="7" height="120"/></g>
<path d="M250 62 L347 32 L347 52 L250 82 Z" fill="{aksent}"/></svg>"""
    if motiv == "frisor":
        return f"""<svg viewBox="0 0 400 300" aria-hidden="true"><g fill="none" stroke="{blekk}" stroke-width="10" stroke-linecap="round">
<circle cx="120" cy="215" r="38"/><circle cx="220" cy="225" r="38"/><path d="M145 185 L300 40 M195 195 L330 70"/></g>
<circle cx="268" cy="118" r="10" fill="{aksent}"/>
<path d="M40 70 q40 -40 80 0 t80 0" fill="none" stroke="{aksent}" stroke-width="8" stroke-linecap="round"/></svg>"""
    # hus (håndverk)
    return f"""<svg viewBox="0 0 400 300" aria-hidden="true"><g fill="none" stroke="{blekk}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round">
<path d="M60 150 L200 40 L340 150"/><path d="M90 130 V260 H310 V130"/><rect x="170" y="180" width="60" height="80"/></g>
<rect x="115" y="160" width="40" height="40" fill="{aksent}"/><rect x="245" y="160" width="40" height="40" fill="{aksent}"/>
<path d="M270 80 V40 h30 v62" fill="none" stroke="{blekk}" stroke-width="10" stroke-linejoin="round"/></svg>"""


def initialer(navn):
    ord_ = [w for w in navn.split() if w[:1].isalnum() and not w.islower()]
    return "".join(w[0] for w in ord_[:2]).upper() or "•"


def demo_side(k, cfg):
    if k["mal"] in salong.INNHOLD:
        return salong.demo(k, cfg)
    inn = INNHOLD[k["mal"]]
    bg, blekk, aksent, aksent_tekst = inn["palett"]
    font_url, font_familie = FONTER[inn["font"]]
    sted = k["poststed"] or "Bergen"
    navn = k["navn"]
    fyll = lambda s: s.format(navn=navn, sted=sted)  # noqa: E731
    selger = cfg["selger"]
    tlf = k.get("telefon", "")
    tlf_lenke = "tel:+47" + tlf.replace(" ", "") if tlf else ""
    epost = k.get("epost", "")
    adresse = ", ".join(x for x in (k.get("adresse"), f"{k.get('postnummer', '')} {sted}".strip()) if x)
    kart = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{navn}, {adresse}")
    tjenester = "".join(
        f'<article class="kort"><span class="nr">0{i + 1}</span><h3>{E(t)}</h3><p>{E(fyll(b))}</p></article>'
        for i, (t, b) in enumerate(inn["tjenester"])
    )
    usp = "".join(f"<li>{E(u)}</li>" for u in inn["usp"])
    knapp_primar = (f'<a class="knapp" href="{tlf_lenke}">{E(inn["cta"])} · {E(tlf)}</a>' if tlf
                    else f'<a class="knapp" href="#kontakt">{E(inn["cta"])}</a>')
    kontakt_linjer = []
    if tlf:
        kontakt_linjer.append(f'<p><span>Telefon</span><a href="{tlf_lenke}">{E(tlf)}</a></p>')
    if epost:
        kontakt_linjer.append(f'<p><span>E-post</span><a href="mailto:{E(epost)}">{E(epost)}</a></p>')
    if adresse:
        kontakt_linjer.append(f'<p><span>Adresse</span><a href="{E(kart)}" target="_blank" rel="noopener">{E(adresse)}</a></p>')
    kontakt_linjer.append('<p><span>Åpningstider</span>Man–fre 08–16 <em>(eksempel – fylles inn)</em></p>')

    return f"""<!doctype html>
<html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{E(navn)} – {E(inn['tagline'])} (forslag)</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={font_url}&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:{bg};--blekk:{blekk};--aksent:{aksent};--aksent-tekst:{aksent_tekst};--display:{font_familie};}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--blekk);font:17px/1.6 'Source Sans 3',system-ui,sans-serif}}
a{{color:inherit}}
.demo{{background:var(--blekk);color:var(--bg);font-size:14px;padding:10px 20px;text-align:center}}
.demo a{{color:var(--bg);font-weight:600}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 24px}}
header{{display:flex;align-items:center;justify-content:space-between;padding:22px 0}}
.logo{{display:flex;align-items:center;gap:12px;font-family:var(--display);font-weight:700;font-size:20px;text-decoration:none}}
.merke{{width:42px;height:42px;border-radius:50%;background:var(--aksent);color:var(--aksent-tekst);display:grid;place-items:center;font-size:16px;letter-spacing:.5px}}
nav a{{margin-left:26px;text-decoration:none;font-weight:600;font-size:15px;opacity:.8}}
nav a:hover{{opacity:1}}
.hero{{display:grid;grid-template-columns:1.1fr .9fr;gap:48px;align-items:center;padding:56px 0 72px}}
h1{{font-family:var(--display);font-size:clamp(38px,5.4vw,66px);line-height:1.04;letter-spacing:-.02em}}
.ingress{{font-size:20px;margin:22px 0 32px;max-width:34ch;opacity:.85}}
.knapp{{display:inline-block;background:var(--aksent);color:var(--aksent-tekst);padding:15px 26px;border-radius:999px;font-weight:600;text-decoration:none;transition:transform .15s}}
.knapp:hover{{transform:translateY(-2px)}}
.knapp.lys{{background:transparent;color:var(--blekk);border:2px solid var(--blekk);margin-left:10px}}
.motiv svg{{width:100%;height:auto}}
.usp{{display:flex;flex-wrap:wrap;gap:12px;list-style:none;padding:0;margin-top:34px}}
.usp li{{border:1.5px solid color-mix(in srgb,var(--blekk) 25%,transparent);border-radius:999px;padding:6px 14px;font-size:14px;font-weight:600}}
section{{padding:80px 0}}
h2{{font-family:var(--display);font-size:clamp(30px,3.6vw,44px);letter-spacing:-.01em;margin-bottom:36px}}
.tjenester{{background:color-mix(in srgb,var(--blekk) 5%,var(--bg))}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}
.kort{{background:var(--bg);border-radius:18px;padding:28px;border:1px solid color-mix(in srgb,var(--blekk) 10%,transparent)}}
.kort .nr{{font-family:var(--display);color:var(--aksent);font-weight:700;font-size:15px}}
.kort h3{{font-family:var(--display);font-size:22px;margin:10px 0 8px}}
.kort p{{font-size:16px;opacity:.8}}
.om{{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}}
.om h2{{line-height:1.15}}.om p{{font-size:20px}}
.kontakt{{background:var(--blekk);color:var(--bg)}}
.kontakt .rad{{display:grid;grid-template-columns:1fr 1fr;gap:48px}}
.kontakt p{{display:flex;flex-direction:column;padding:14px 0;border-bottom:1px solid color-mix(in srgb,var(--bg) 20%,transparent);font-size:19px}}
.kontakt p span{{font-size:13px;text-transform:uppercase;letter-spacing:.1em;opacity:.6}}
.kontakt .knapp{{margin-top:8px}}
footer{{padding:28px 0;font-size:14px;opacity:.7}}
@media(max-width:860px){{.hero,.om,.kontakt .rad{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr 1fr}}nav{{display:none}}.motiv{{max-width:360px}}}}
@media(max-width:520px){{.grid{{grid-template-columns:1fr}}.knapp.lys{{margin:12px 0 0}}}}
</style></head>
<body>
<div class="demo">Dette er et <strong>forslag</strong> til nettside for {E(navn)}, laget av {E(selger['navn'])} – ikke bedriftens offisielle side.
Interessert? <a href="tel:{E(selger['telefon'].replace(' ', ''))}">{E(selger['telefon'])}</a> · <a href="mailto:{E(selger['epost'])}">{E(selger['epost'])}</a></div>
<div class="wrap">
<header><a class="logo" href="#"><span class="merke">{E(initialer(navn))}</span>{E(navn)}</a>
<nav><a href="#tjenester">Tjenester</a><a href="#om">Om oss</a><a href="#kontakt">Kontakt</a></nav></header>
<div class="hero"><div><h1>{E(inn['tagline'])}</h1><p class="ingress">{E(fyll(inn['ingress']))}</p>
{knapp_primar}<a class="knapp lys" href="#tjenester">Se tjenester</a><ul class="usp">{usp}</ul></div>
<div class="motiv">{motiv_svg(inn['motiv'], aksent, blekk)}</div></div></div>
<section class="tjenester" id="tjenester"><div class="wrap"><h2>Dette hjelper vi deg med</h2><div class="grid">{tjenester}</div></div></section>
<section id="om"><div class="wrap om"><h2>Om {E(navn)}</h2><p>{E(fyll(inn['om']))}</p></div></section>
<section class="kontakt" id="kontakt"><div class="wrap rad"><div><h2>Ta kontakt</h2>{knapp_primar}</div><div>{''.join(kontakt_linjer)}</div></div></section>
<footer class="wrap">© {E(navn)} · Org.nr. {E(k['orgnr'])}</footer>
</body></html>"""


# ---------------- salgsutkast ----------------

def _oppgradering_utkast(k, cfg):
    s, p = cfg["selger"], cfg["pris"]
    dom = k.get("nettside", "")
    punkter = "\n".join(f"– {x}" for x in (k.get("problemer") or [])[:4])
    if k.get("epost_lov"):
        emne = f"Forslag til ny nettside for {k['navn']}"
        tekst = (
            f"Hei!\n\n"
            f"Jeg heter {s['navn']} og lager nettsider for små bedrifter i Bergen. "
            + (f"Jeg så på nettsiden deres ({dom}) og la merke til et par ting:\n\n{punkter}\n\n"
               f"Derfor har jeg laget et forslag til en ny og mer moderne side:\n\n{k['demo_url']}\n\n"
               if punkter else
               f"Jeg så på nettsiden deres ({dom}) og laget et forslag til et nytt og mer moderne design:\n\n"
               f"{k['demo_url']}\n\n")
            + 
            f"Dere beholder domenet {dom}, og jeg flytter innholdet over. "
            f"Pris: {p['oppstart']} kr i oppstart og {p['per_mnd']} kr/mnd for drift og små endringer. Ingen binding. "
            f"Betaler dere mer enn dette for nettsiden i dag, sparer dere penger samtidig.\n\n"
            f"Passer det med en kort prat? Svar på denne e-posten eller ring meg på {s['telefon']}.\n\n"
            f"Vennlig hilsen\n{s['navn']}\n\n"
            f"Ønsker dere ikke slike henvendelser, holder det å svare «nei takk» – da sletter jeg forslaget."
        )
        mailto = "mailto:{}?subject={}&body={}".format(k["epost"], urllib.parse.quote(emne), urllib.parse.quote(tekst))
        oppf_tekst = (f"Hei igjen!\n\nVille bare høre om dere fikk sett forslaget til ny nettside for {k['navn']}:\n"
                      f"{k['demo_url']}\n\nJeg viser gjerne hvordan den ser ut på mobil, og tilpasser farger og "
                      f"innhold før dere bestemmer dere. Et kort ja eller nei holder.\n\nVennlig hilsen\n{s['navn']}\n{s['telefon']}")
        oppf = "mailto:{}?subject={}&body={}".format(k["epost"], urllib.parse.quote("Re: " + emne), urllib.parse.quote(oppf_tekst))
        return {"type": "epost", "emne": emne, "tekst": tekst, "lenke": mailto, "oppf_tekst": oppf_tekst, "oppf_lenke": oppf}
    funn = (f"og la merke til et par ting – blant annet: {k['problemer'][0].lower()}. " if k.get("problemer")
            else "og synes designet kan moderniseres. ")
    tekst = (
        f"«Hei, jeg heter {s['navn']}. Jeg lager nettsider for små bedrifter i Bergen. "
        f"Jeg så på nettsiden deres, {dom}, {funn}"
        f"Jeg har laget et forslag til en ny versjon – kan jeg sende deg lenken på SMS eller e-post?»\n\n"
        + (f"Svakheter du kan nevne:\n{punkter}\n\n" if punkter else "")
        + f"Hvis ja: be om samtykke og send {k.get('demo_url', '')}\n"
        f"Pris: {p['oppstart']} kr oppstart + {p['per_mnd']} kr/mnd, ingen binding. De beholder domenet."
    )
    lenke = "tel:+47" + k["telefon"].replace(" ", "") if k.get("telefon") else ""
    return {"type": "ring", "emne": "Ringemanus", "tekst": tekst, "lenke": lenke,
            "oppf_tekst": "Ring igjen om noen dager hvis du ikke fikk svar.", "oppf_lenke": lenke}


def utkast(k, cfg):
    if k.get("type") == "oppgradering":
        return _oppgradering_utkast(k, cfg)
    s, p = cfg["selger"], cfg["pris"]
    salong_ = k["mal"] in salong.INNHOLD
    bilde_linje = ("Bildene på siden er eksempelbilder – sier dere ja, bytter jeg dem ut med bilder fra "
                   "deres egen Instagram, så siden blir helt deres. " if salong_ else "")
    if k.get("epost_lov"):
        emne = f"Forslag til nettside for {k['navn']}"
        tekst = (
            f"Hei!\n\n"
            f"Jeg heter {s['navn']} og lager nettsider for små bedrifter i Bergen. "
            f"Jeg fant ingen nettside for {k['navn']}, så jeg tok meg friheten å lage et forslag:\n\n"
            f"{k['demo_url']}\n\n"
            f"{bilde_linje}Tekster, priser og åpningstider tilpasses dere. "
            f"Pris: {p['oppstart']} kr i oppstart og {p['per_mnd']} kr/mnd for drift, domene og små endringer. Ingen binding.\n\n"
            f"Passer det med en kort prat? Svar på denne e-posten eller ring meg på {s['telefon']}.\n\n"
            f"Vennlig hilsen\n{s['navn']}\n\n"
            f"Ønsker dere ikke slike henvendelser, holder det å svare «nei takk» – da sletter jeg forslaget."
        )
        mailto = "mailto:{}?subject={}&body={}".format(
            k["epost"], urllib.parse.quote(emne), urllib.parse.quote(tekst))
        oppf_emne = f"Re: {emne}"
        oppf_tekst = (
            f"Hei igjen!\n\n"
            f"Ville bare høre om dere fikk sett forslaget til nettside for {k['navn']}:\n{k['demo_url']}\n\n"
            f"Jeg tilpasser gjerne farger, tekster og bilder før dere bestemmer dere – helt uforpliktende. "
            f"Et kort ja eller nei holder.\n\nVennlig hilsen\n{s['navn']}\n{s['telefon']}"
        )
        oppf = "mailto:{}?subject={}&body={}".format(
            k["epost"], urllib.parse.quote(oppf_emne), urllib.parse.quote(oppf_tekst))
        return {"type": "epost", "emne": emne, "tekst": tekst, "lenke": mailto,
                "oppf_tekst": oppf_tekst, "oppf_lenke": oppf}
    tekst = (
        f"«Hei, jeg heter {s['navn']}. Jeg lager nettsider for små bedrifter her i Bergen, "
        f"og så at {k['navn']} ikke har en egen side. Jeg har faktisk laget et forslag til dere allerede – "
        f"kan jeg sende deg lenken på SMS eller e-post, så kan du se på det når det passer?»\n\n"
        f"Hvis ja: be om samtykke og send {k.get('demo_url', '')}\n"
        + (f"Nevn gjerne: bildene byttes ut med deres egne fra Instagram.\n" if salong_ else "")
        + f"Pris hvis de spør: {p['oppstart']} kr oppstart + {p['per_mnd']} kr/mnd, ingen binding."
    )
    lenke = "tel:+47" + k["telefon"].replace(" ", "") if k.get("telefon") else ""
    return {"type": "ring", "emne": "Ringemanus", "tekst": tekst, "lenke": lenke,
            "oppf_tekst": "Ring igjen om noen dager hvis du ikke fikk svar.", "oppf_lenke": lenke}


# ---------------- morgenrapport ----------------

STATUSER = [("sendt", "Sendt"), ("ringt", "Ringt"), ("interessert", "Interessert"),
            ("kunde", "Kunde"), ("nei", "Nei")]


def morgenrapport(leads, utelat, logg, cfg, dato):
    kort = []
    for k in leads:
        u = k["utkast"]
        sok = "https://www.google.com/search?q=" + urllib.parse.quote(f"{k['navn']} {k['poststed'] or 'Bergen'}")
        brreg = f"https://virksomhet.brreg.no/nb/oppslag/enheter/{k['orgnr']}"
        if u["type"] == "epost":
            hoved = f'<a class="btn primar" data-auto="sendt" href="{E(u["lenke"])}">Send e-post</a>'
        elif u["lenke"]:
            hoved = f'<a class="btn primar" data-auto="ringt" href="{E(u["lenke"])}">Ring {E(k["telefon"])}</a>'
        else:
            hoved = '<span class="btn av">Finn kontaktinfo</span>'
        oppf = (f'<div class="oppf"><b>Tid for oppfølging.</b> '
                + (f'<a class="btn" data-auto="fulgtopp" href="{E(u["oppf_lenke"])}">Send oppfølging</a>' if u.get("oppf_lenke") else "")
                + f'<details><summary>Se tekst</summary><pre>{E(u.get("oppf_tekst", ""))}</pre></details></div>')
        flagg = "".join(f'<li>{E(f)}</li>' for f in k["flagg"])
        grunner = "".join(f'<span class="chip">{E(g)}</span>' for g in k["grunner"])
        statusknapper = "".join(f'<button type="button" data-s="{s}">{E(t)}</button>' for s, t in STATUSER)
        oppg = k.get("type") == "oppgradering"
        oppg_html = ""
        if oppg:
            svak = "".join(f"<li>{E(x)}</li>" for x in k.get("problemer") or [])
            oppg_html = (f'<div class="oppg">Dagens side: <a href="https://{E(k.get("nettside", ""))}" target="_blank" '
                         f'rel="noopener">{E(k.get("nettside", ""))}</a><ul>{svak}</ul></div>')
        kort.append(f"""<article class="lead" data-orgnr="{E(k['orgnr'])}" data-type="{u['type']}" data-art="{'oppg' if oppg else 'ny'}">
<div class="topp"><div><h3>{E(k['navn'])} <small>{E(k['form'])}</small></h3>
<p class="meta">{E(k['bransje_navn'])} · {E(k['poststed'])} · poeng {k['poeng']}</p></div>
<span><span class="art {'oppg' if oppg else ''}">{'Ny side' if not oppg else 'Oppgradering'}</span>
<span class="kanal {u['type']}">{'E-post' if u['type'] == 'epost' else 'Ring'}</span></span></div>
<p class="statuslinje"></p>
{oppg_html}
<div class="chips">{grunner}</div>
{f'<ul class="flagg">{flagg}</ul>' if flagg else ''}
{oppf}
<div class="knapper">{hoved}<a class="btn" href="{E(k['demo_url'])}" target="_blank" rel="noopener">Se demo</a>
<a class="btn" href="{E(sok)}" target="_blank" rel="noopener">Google-sjekk</a><a class="btn" href="{E(brreg)}" target="_blank" rel="noopener">Brreg</a></div>
<div class="status">{statusknapper}</div>
<p class="nei-hint">Husk å slette demoen: Actions → «Slett demo» → orgnr <b>{E(k['orgnr'])}</b></p>
<details><summary>{E(u['emne'])}</summary><pre>{E(u['tekst'])}</pre></details>
<textarea placeholder="Notat (lagres på denne enheten)"></textarea>
</article>""")
    utelat_html = "".join(f"<li>{E(onr)}: {E(grunn)}</li>" for onr, grunn in utelat.items())
    logg_html = "".join(f"<li>{E(l)}</li>" for l in logg)
    tom = '<p class="tom">Ingen nye demoer i natt.</p>' if not leads else ""
    return f"""<!doctype html><html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morgenrapport {dato}</title><style>
:root{{--bg:#FAF8F4;--kort:#fff;--blekk:#1C2321;--dempet:#5E6A66;--linje:#E4E0D8;--aksent:#1F6F5C;--varsel:#9A5B00;--varselbg:#FFF4E0;--blaa:#2F5DA8;--blaabg:#EAF0FA}}
@media(prefers-color-scheme:dark){{:root{{--bg:#151917;--kort:#1E2321;--blekk:#ECEFEC;--dempet:#9AA6A1;--linje:#2E3532;--aksent:#5CC2A6;--varsel:#F0B45C;--varselbg:#2E2614;--blaa:#8FB3F0;--blaabg:#1C2638}}}}
*{{box-sizing:border-box;margin:0}}body{{background:var(--bg);color:var(--blekk);font:16px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif;padding:28px 18px}}
.wrap{{max-width:860px;margin:0 auto}}h1{{font-size:28px;letter-spacing:-.01em}}
.sum{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 14px}}.tall{{background:var(--kort);border:1px solid var(--linje);border-radius:12px;padding:10px 16px;min-width:110px}}
.tall b{{display:block;font-size:24px}}.tall span{{color:var(--dempet);font-size:13px}}
.filter{{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 18px}}.filter button{{font:inherit;font-size:14px;padding:6px 12px;border-radius:999px;border:1px solid var(--linje);background:var(--kort);color:var(--blekk);cursor:pointer}}
.filter button.på{{background:var(--blekk);color:var(--bg);border-color:var(--blekk)}}
.lead{{background:var(--kort);border:1px solid var(--linje);border-radius:14px;padding:18px 20px;margin-bottom:14px}}
.lead.ferdig{{opacity:.55}}
.topp{{display:flex;justify-content:space-between;gap:12px}}h3{{font-size:19px}}h3 small{{color:var(--dempet);font-weight:500;font-size:13px}}
.meta{{color:var(--dempet);font-size:14px}}.kanal{{font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px;height:fit-content;border:1px solid var(--linje)}}
.kanal.epost{{color:var(--aksent)}}.art{{font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px;margin-right:6px;background:var(--bg);color:var(--dempet)}}
.art.oppg{{background:#F3E8FF;color:#6B3FA0}}@media(prefers-color-scheme:dark){{.art.oppg{{background:#2C2140;color:#C9A8F0}}}}
.oppg{{font-size:14px;margin:8px 0;padding:10px 12px;border-radius:8px;border:1px solid var(--linje)}}.oppg ul{{margin:6px 0 0;padding-left:18px;color:var(--dempet)}}.statuslinje{{font-size:14px;font-weight:600;color:var(--blaa);margin-top:4px}}.statuslinje:empty{{display:none}}
.chips{{margin:10px 0 4px}}.chip{{display:inline-block;font-size:12px;color:var(--dempet);border:1px solid var(--linje);border-radius:999px;padding:2px 9px;margin:0 6px 6px 0}}
.flagg{{background:var(--varselbg);color:var(--varsel);border-radius:8px;padding:8px 12px 8px 28px;font-size:14px;margin:6px 0}}
.oppf{{display:none;background:var(--blaabg);color:var(--blaa);border-radius:8px;padding:10px 12px;font-size:14px;margin:8px 0}}
.lead.folgopp .oppf{{display:block}}.oppf .btn{{margin-left:8px;color:var(--blaa);border-color:var(--blaa)}}
.knapper{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 8px}}.btn{{font-size:14px;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid var(--linje);text-decoration:none;color:var(--blekk);display:inline-block}}
.btn.primar{{background:var(--aksent);border-color:var(--aksent);color:var(--bg)}}.btn.av{{color:var(--dempet)}}
.status{{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 6px}}.status button{{font:inherit;font-size:13px;padding:4px 10px;border-radius:6px;border:1px dashed var(--linje);background:none;color:var(--dempet);cursor:pointer}}
.status button.på{{border-style:solid;border-color:var(--blaa);color:var(--blaa);font-weight:600}}
.nei-hint{{display:none;font-size:13px;color:var(--varsel);margin:4px 0}}.lead[data-status=nei] .nei-hint{{display:block}}
details summary{{cursor:pointer;font-size:14px;color:var(--dempet);margin-top:4px}}pre{{white-space:pre-wrap;font:14px/1.5 ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--linje);border-radius:8px;padding:12px;margin-top:8px;user-select:all}}
textarea{{width:100%;margin-top:8px;font-size:14px;font-family:inherit;line-height:1.4;padding:8px 10px;border:1px solid var(--linje);border-radius:8px;background:var(--bg);color:var(--blekk);min-height:38px;resize:vertical}}
.tom{{color:var(--dempet)}}.fot{{margin-top:28px;color:var(--dempet);font-size:13px}}.fot ul{{padding-left:18px}}
.info{{font-size:13px;color:var(--dempet);margin-bottom:16px}}
</style></head><body><div class="wrap">
<h1>Morgenrapport · {dato}</h1>
<div class="sum"><div class="tall"><b id="n-alle">{len(leads)}</b><span>demoer</span></div><div class="tall"><b id="n-ny">–</b><span>ikke kontaktet</span></div>
<div class="tall"><b id="n-oppf">–</b><span>følg opp</span></div><div class="tall"><b id="n-int">–</b><span>interessert</span></div><div class="tall"><b id="n-kunde">–</b><span>kunder</span></div></div>
<div class="filter"><button data-f="alle" class="på">Alle</button><button data-f="ny">Ikke kontaktet</button><button data-f="oppf">Følg opp</button>
<button data-f="oppgradering">Oppgradering</button><button data-f="aktiv">Sendt/ringt</button><button data-f="int">Interessert</button><button data-f="ferdig">Kunde/nei</button></div>
<p class="info">Status lagres i nettleseren på denne enheten. «Send e-post» og «Ring» merker automatisk. E-post uten svar etter 4 dager havner under «Følg opp».
E-post går bare til AS og andre selskaper – enkeltpersonforetak ringer du (markedsføringsloven § 15).</p>
{tom}{''.join(kort)}
<div class="fot"><details><summary>Utelatt ({len(utelat)})</summary><ul>{utelat_html}</ul></details>
<details><summary>Logg</summary><ul>{logg_html}</ul></details></div>
</div>
<script>
(function(){{
const NØKKEL="nb_status_v1", DAG=864e5, OPPF_DAGER=4;
let db={{}};try{{db=JSON.parse(localStorage.getItem(NØKKEL)||"{{}}")}}catch(e){{}}
const lagre=()=>{{try{{localStorage.setItem(NØKKEL,JSON.stringify(db))}}catch(e){{}}}};
const navn={{sendt:"E-post sendt",ringt:"Ringt",interessert:"Interessert",kunde:"Kunde",nei:"Takket nei",fulgtopp:"Fulgt opp"}};
const fmt=t=>new Date(t).toLocaleDateString("no-NO",{{day:"numeric",month:"short"}});
function tegn(){{
  const n={{ny:0,oppf:0,int:0,kunde:0}};
  document.querySelectorAll(".lead").forEach(el=>{{
    const r=db[el.dataset.orgnr]||{{}}, s=r.s||"";
    el.dataset.status=s;
    el.querySelectorAll(".status button").forEach(b=>b.classList.toggle("på",b.dataset.s===s||(s==="fulgtopp"&&b.dataset.s==="sendt")));
    const linje=el.querySelector(".statuslinje");
    linje.textContent=s?navn[s]+" "+fmt(r.t)+(r.oppf?" · fulgt opp "+fmt(r.oppf):""):"";
    const folgopp=(s==="sendt"&&Date.now()-r.t>OPPF_DAGER*DAG);
    el.classList.toggle("folgopp",folgopp);el.classList.toggle("ferdig",s==="kunde"||s==="nei");
    const ta=el.querySelector("textarea");if(document.activeElement!==ta)ta.value=r.notat||"";
    if(!s)n.ny++;if(folgopp)n.oppf++;if(s==="interessert")n.int++;if(s==="kunde")n.kunde++;
    el.dataset.gruppe=!s?"ny":folgopp?"oppf":(s==="kunde"||s==="nei")?"ferdig":s==="interessert"?"int":"aktiv";
  }});
  for(const k in n){{const e=document.getElementById("n-"+k);if(e)e.textContent=n[k]}}
  filtrer();
}}
let filter="alle";
function filtrer(){{document.querySelectorAll(".lead").forEach(el=>{{
  const g=el.dataset.gruppe;el.style.display=(filter==="alle"||g===filter||(filter==="aktiv"&&g==="oppf")||
    (filter==="oppgradering"&&el.dataset.art==="oppg"))?"":"none"}})}}
function sett(orgnr,s){{const r=db[orgnr]||{{}};
  if(s==="fulgtopp"){{r.oppf=Date.now();r.s="fulgtopp";}}
  else if(r.s===s){{delete r.s;delete r.t;}} else {{r.s=s;r.t=Date.now();}}
  db[orgnr]=r;lagre();tegn();}}
document.addEventListener("click",e=>{{
  const lead=e.target.closest(".lead");
  const sb=e.target.closest(".status button");if(sb&&lead){{sett(lead.dataset.orgnr,sb.dataset.s);return;}}
  const auto=e.target.closest("[data-auto]");if(auto&&lead){{const r=db[lead.dataset.orgnr]||{{}};
    if(auto.dataset.auto==="fulgtopp"||!r.s)sett(lead.dataset.orgnr,auto.dataset.auto);}}
  const fb=e.target.closest(".filter button");if(fb){{filter=fb.dataset.f;
    document.querySelectorAll(".filter button").forEach(b=>b.classList.toggle("på",b===fb));filtrer();}}
}});
document.addEventListener("input",e=>{{if(e.target.tagName==="TEXTAREA"){{const lead=e.target.closest(".lead");
  const r=db[lead.dataset.orgnr]||{{}};r.notat=e.target.value;db[lead.dataset.orgnr]=r;lagre();}}}});
tegn();
}})();
</script>
</body></html>"""


# ---------------- låst (kryptert) rapportside ----------------

def laast_side(data_b64, dato, datoer, prefiks):
    arkiv = "".join(f'<a href="{prefiks}arkiv/{d}.html">{d}</a>' for d in datoer)
    arkiv_html = f'<p class="arkiv">Tidligere: {arkiv}</p>' if arkiv else ""
    return f"""<!doctype html><html lang="no"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Morgenrapport {dato}</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#FAF8F4;color:#1C2321;font:16px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}}
@media(prefers-color-scheme:dark){{body{{background:#151917;color:#ECEFEC}}input{{background:#1E2321;color:#ECEFEC;border-color:#2E3532}}}}
form{{width:min(360px,90vw)}}h1{{font-size:22px;margin:0 0 4px}}p{{margin:0 0 16px;opacity:.75}}
input[type=password]{{width:100%;box-sizing:border-box;font-size:17px;padding:12px 14px;border:1px solid #D9D4CA;border-radius:10px;margin-bottom:10px}}
button{{width:100%;font-size:16px;font-weight:600;padding:12px;border:0;border-radius:10px;background:#1F6F5C;color:#fff;cursor:pointer}}
label{{display:flex;gap:8px;align-items:center;font-size:14px;margin:4px 0 14px;opacity:.8}}
.feil{{color:#B3261E;min-height:22px;font-size:14px}}.arkiv{{font-size:13px;margin-top:18px}}.arkiv a{{margin-right:10px;color:inherit}}
</style></head><body>
<form id="f"><h1>Morgenrapport</h1><p>{dato} · skriv passordet ditt</p>
<input type="password" id="pw" autocomplete="current-password" autofocus placeholder="Passord">
<label><input type="checkbox" id="husk"> Husk på denne enheten</label>
<button>Åpne</button><div class="feil" id="feil"></div>{arkiv_html}</form>
<script>
const DATA="{data_b64}";
async function apne(pw){{
  const raw=Uint8Array.from(atob(DATA),c=>c.charCodeAt(0));
  if(new TextDecoder().decode(raw.slice(0,8))!=="Salted__")throw new Error("format");
  const salt=raw.slice(8,16),ct=raw.slice(16);
  const base=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveBits"]);
  const bits=new Uint8Array(await crypto.subtle.deriveBits({{name:"PBKDF2",salt,iterations:200000,hash:"SHA-256"}},base,384));
  const key=await crypto.subtle.importKey("raw",bits.slice(0,32),"AES-CBC",false,["decrypt"]);
  const html=new TextDecoder().decode(await crypto.subtle.decrypt({{name:"AES-CBC",iv:bits.slice(32,48)}},key,ct));
  if(!/^<!doctype/i.test(html.trim()))throw new Error("feil passord");
  return html;
}}
async function vis(pw,lagre){{
  try{{const html=await apne(pw);
    if(lagre){{try{{localStorage.setItem("nb_pw",pw)}}catch(e){{}}}}
    document.open();document.write(html);document.close();
  }}catch(e){{document.getElementById("feil").textContent="Feil passord – prøv igjen.";
    try{{localStorage.removeItem("nb_pw")}}catch(e){{}}}}
}}
document.getElementById("f").addEventListener("submit",ev=>{{ev.preventDefault();
  vis(document.getElementById("pw").value,document.getElementById("husk").checked);}});
try{{const lagret=localStorage.getItem("nb_pw");if(lagret)vis(lagret,false);}}catch(e){{}}
</script></body></html>"""
