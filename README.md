# renate-landt.de — Galerie-Webseite

Statische Galerie, die sich automatisch aus geteilten iCloud-Alben speist.
Renate pflegt nur ihre Alben in der Fotos-App — diese Seite baut sich selbst.

## Wie es funktioniert

1. `sync.py` liest für jedes Album in `alben.json` den öffentlichen iCloud-Feed,
   lädt neue Bilder nach `bilder/` und schreibt `werke.json`.
   Titel = Text beim Einstellen ins Album („Sag etwas dazu …"),
   Kategorie = Albumname (oder `kategorie` in `alben.json`).
2. `generate.py` baut daraus die fertige Seite nach `public/`.
3. Der GitHub-Actions-Workflow (`.github/workflows/sync.yml`) führt beides
   täglich um 03:00 UTC aus (und bei jedem Push, oder manuell über den
   Actions-Tab) und veröffentlicht `public/` auf GitHub Pages.

Fällt der iCloud-Feed aus (undokumentierte Schnittstelle), schlägt der Sync
laut fehl und die zuletzt gebaute Seite bleibt einfach stehen — die Bilder
liegen als Kopie im Repository.

## Neues Album aufnehmen

1. In der Fotos-App: geteiltes Album anlegen, „Öffentliche Website" aktivieren.
2. Link kopieren — der Teil hinter `#` ist der Token
   (z. B. `https://www.icloud.com/sharedalbum/#B2TJtdOXmGis7EV` → `B2TJtdOXmGis7EV`).
3. Token als neuen Eintrag in `alben.json` ergänzen. Reihenfolge dort
   = Reihenfolge in der Navigation.

## Inhalte pflegen

- Texte (Über-Seite, Impressum, Datenschutz): `seite/inhalte.json`
- Porträtfoto: `seite/portrait.jpg`
- Eigene Domain: Datei `CNAME` (enthält den Domainnamen)

## Lokal testen

```
python3 sync.py       # braucht Internet
python3 generate.py
# public/index.html im Browser öffnen
```

## Einmalige Einrichtung (bereits erledigt / To-do)

- [ ] GitHub-Repository anlegen, diese Dateien pushen
- [ ] Repo → Settings → Pages → Source: „GitHub Actions"
- [ ] `CNAME`-Datei mit `renate-landt.de` anlegen
- [ ] IONOS-DNS: `www` als CNAME auf `<benutzer>.github.io`,
      Apex (`renate-landt.de`) als A-Records auf die GitHub-Pages-IPs
- [ ] In Repo-Settings → Pages die Domain eintragen und „Enforce HTTPS" aktivieren
- [ ] `seite/inhalte.json`: Anschrift, E-Mail, Stand-Datum ergänzen
