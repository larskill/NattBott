"""HTML-maler: demo-nettsider, salgsutkast og morgenrapport."""
import html
import urllib.parse

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

def utkast(k, cfg):
    s, p = cfg["selger"], cfg["pris"]
    if k.get("epost_lov"):
        emne = f"Forslag til nettside for {k['navn']}"
        tekst = (
            f"Hei!\n\n"
            f"Jeg heter {s['navn']} og lager enkle nettsider for små bedrifter i Bergen. "
            f"Jeg fant ingen nettside for {k['navn']}, så jeg tok meg friheten å lage et forslag:\n\n"
            f"{k['demo_url']}\n\n"
            f"Siden kan tilpasses med deres egne bilder, åpningstider og tekster. "
            f"Pris: {p['oppstart']} kr i oppstart og {p['per_mnd']} kr/mnd for drift, domene og små endringer. Ingen binding.\n\n"
            f"Passer det med en kort prat? Svar på denne e-posten eller ring meg på {s['telefon']}.\n\n"
            f"Vennlig hilsen\n{s['navn']}\n\n"
            f"Ønsker dere ikke slike henvendelser, holder det å svare «nei takk» – da sletter jeg forslaget."
        )
        mailto = "mailto:{}?subject={}&body={}".format(
            k["epost"], urllib.parse.quote(emne), urllib.parse.quote(tekst))
        return {"type": "epost", "emne": emne, "tekst": tekst, "lenke": mailto}
    tekst = (
        f"«Hei, jeg heter {s['navn']}. Jeg lager nettsider for små bedrifter her i Bergen, "
        f"og så at {k['navn']} ikke har en egen side. Jeg har faktisk laget et forslag til dere allerede – "
        f"kan jeg sende deg lenken på SMS eller e-post, så kan du se på det når det passer?»\n\n"
        f"Hvis ja: be om samtykke og send {k.get('demo_url', '')}\n"
        f"Pris hvis de spør: {p['oppstart']} kr oppstart + {p['per_mnd']} kr/mnd, ingen binding."
    )
    lenke = "tel:+47" + k["telefon"].replace(" ", "") if k.get("telefon") else ""
    return {"type": "ring", "emne": "Ringemanus", "tekst": tekst, "lenke": lenke}


# ---------------- morgenrapport ----------------

def morgenrapport(leads, utelat, logg, cfg, dato):
    kort = []
    for k in leads:
        u = k["utkast"]
        sok = "https://www.google.com/search?q=" + urllib.parse.quote(f"{k['navn']} {k['poststed'] or 'Bergen'}")
        brreg = f"https://virksomhet.brreg.no/nb/oppslag/enheter/{k['orgnr']}"
        if u["type"] == "epost":
            hoved = f'<a class="btn primar" href="{E(u["lenke"])}">Send e-post</a>'
        elif u["lenke"]:
            hoved = f'<a class="btn primar" href="{E(u["lenke"])}">Ring {E(k["telefon"])}</a>'
        else:
            hoved = '<span class="btn av">Finn kontaktinfo</span>'
        flagg = "".join(f'<li>{E(f)}</li>' for f in k["flagg"])
        grunner = "".join(f'<span class="chip">{E(g)}</span>' for g in k["grunner"])
        kort.append(f"""<article class="lead">
<div class="topp"><div><h3>{E(k['navn'])} <small>{E(k['form'])}</small></h3>
<p class="meta">{E(k['bransje_navn'])} · {E(k['poststed'])} · poeng {k['poeng']}</p></div>
<span class="kanal {u['type']}">{'E-post' if u['type'] == 'epost' else 'Ring'}</span></div>
<div class="chips">{grunner}</div>
{f'<ul class="flagg">{flagg}</ul>' if flagg else ''}
<div class="knapper">{hoved}<a class="btn" href="{E(k['demo_url'])}" target="_blank" rel="noopener">Se demo</a>
<a class="btn" href="{E(sok)}" target="_blank" rel="noopener">Google-sjekk</a><a class="btn" href="{E(brreg)}" target="_blank" rel="noopener">Brreg</a></div>
<details><summary>{E(u['emne'])}</summary><pre>{E(u['tekst'])}</pre></details>
</article>""")
    n_epost = sum(1 for k in leads if k["utkast"]["type"] == "epost")
    utelat_html = "".join(f"<li>{E(onr)}: {E(grunn)}</li>" for onr, grunn in utelat.items())
    logg_html = "".join(f"<li>{E(l)}</li>" for l in logg)
    tom = '<p class="tom">Ingen nye demoer i natt.</p>' if not leads else ""
    return f"""<!doctype html><html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morgenrapport {dato}</title><style>
:root{{--bg:#FAF8F4;--kort:#fff;--blekk:#1C2321;--dempet:#5E6A66;--linje:#E4E0D8;--aksent:#1F6F5C;--varsel:#9A5B00;--varselbg:#FFF4E0}}
@media(prefers-color-scheme:dark){{:root{{--bg:#151917;--kort:#1E2321;--blekk:#ECEFEC;--dempet:#9AA6A1;--linje:#2E3532;--aksent:#5CC2A6;--varsel:#F0B45C;--varselbg:#2E2614}}}}
*{{box-sizing:border-box;margin:0}}body{{background:var(--bg);color:var(--blekk);font:16px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif;padding:28px 18px}}
.wrap{{max-width:860px;margin:0 auto}}h1{{font-size:28px;letter-spacing:-.01em}}
.sum{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 26px}}.tall{{background:var(--kort);border:1px solid var(--linje);border-radius:12px;padding:12px 18px}}
.tall b{{display:block;font-size:26px}}.tall span{{color:var(--dempet);font-size:14px}}
.lead{{background:var(--kort);border:1px solid var(--linje);border-radius:14px;padding:18px 20px;margin-bottom:14px}}
.topp{{display:flex;justify-content:space-between;gap:12px}}h3{{font-size:19px}}h3 small{{color:var(--dempet);font-weight:500;font-size:13px}}
.meta{{color:var(--dempet);font-size:14px}}.kanal{{font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px;height:fit-content;border:1px solid var(--linje)}}
.kanal.epost{{color:var(--aksent)}}.chips{{margin:10px 0 4px}}.chip{{display:inline-block;font-size:12px;color:var(--dempet);border:1px solid var(--linje);border-radius:999px;padding:2px 9px;margin:0 6px 6px 0}}
.flagg{{background:var(--varselbg);color:var(--varsel);border-radius:8px;padding:8px 12px 8px 28px;font-size:14px;margin:6px 0}}
.knapper{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 6px}}.btn{{font-size:14px;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid var(--linje);text-decoration:none;color:var(--blekk)}}
.btn.primar{{background:var(--aksent);border-color:var(--aksent);color:var(--bg)}}.btn.av{{color:var(--dempet)}}
details summary{{cursor:pointer;font-size:14px;color:var(--dempet);margin-top:4px}}pre{{white-space:pre-wrap;font:14px/1.5 ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--linje);border-radius:8px;padding:12px;margin-top:8px;user-select:all}}
.tom{{color:var(--dempet)}}.fot{{margin-top:28px;color:var(--dempet);font-size:13px}}.fot ul{{padding-left:18px}}
</style></head><body><div class="wrap">
<h1>Morgenrapport · {dato}</h1>
<div class="sum"><div class="tall"><b>{len(leads)}</b><span>nye demoer</span></div><div class="tall"><b>{n_epost}</b><span>klare for e-post</span></div>
<div class="tall"><b>{len(leads) - n_epost}</b><span>ring / stikk innom</span></div><div class="tall"><b>{len(utelat)}</b><span>utelatt (har nettside e.l.)</span></div></div>
<p class="meta" style="margin-bottom:18px">E-post sendes bare til AS og andre selskaper. Enkeltpersonforetak er fysiske personer og må ha samtykke før e-post/SMS (markedsføringsloven § 15), så dem ringer du.</p>
{tom}{''.join(kort)}
<div class="fot"><details><summary>Utelatt i natt ({len(utelat)})</summary><ul>{utelat_html}</ul></details>
<details><summary>Logg</summary><ul>{logg_html}</ul></details></div>
</div></body></html>"""
