# Nattmaskin

Finner bedrifter i Bergen som mangler nettside (via Brønnøysundregistrenes åpne data), lager en ferdig demo-side til hver av dem, og legger frem e-post- eller ringeutkast i en privat morgenrapport.

- `config.json`: selgerinfo, pris, bransjer og antall per natt
- `nattmaskin.py`: henting, filtrering, bygging og sletting
- `maler.py`: demo-sider, salgsutkast og morgenrapport
- `docs/demo/<bedrift>/`: publiseres via GitHub Pages (Settings → Pages → Branch `main`, mappe `/docs`)

Demo-sidene er merket tydelig som forslag. De har `noindex`, og `robots.txt` stenger for søkemotorer, så de vises bare for den som får lenken.

## Oppsett (én gang)
1. **Pages:** Settings → Pages → *Build and deployment* → Source: **GitHub Actions**.
2. **Passord til rapportsiden:** Settings → Secrets and variables → Actions → *New repository secret*: `RAPPORT_PASSORD` = et passord du finner på selv.
3. **Første kjøring:** Actions → *Nattmaskin* → **Run workflow**. Etter det går den av seg selv hver natt ca. kl. 03:17.

## Daglig bruk
- Morgenrapporten ligger på https://larskill.github.io/NattBott/rapport/ (kryptert, åpnes med RAPPORT_PASSORD). Trykk «Send e-post» eller «Ring» for hver bedrift.
- Mangler en rapport: Actions → *Lag rapporten på nytt*.
- Sier en bedrift nei: Actions → *Slett demo* → Run workflow → skriv inn orgnr.
- Pris, tekster og bransjer endres i `config.json` og `maler.py`.
