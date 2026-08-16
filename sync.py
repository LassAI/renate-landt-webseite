#!/usr/bin/env python3
"""Sync: liest die geteilten iCloud-Alben aus alben.json, lädt neue Bilder nach
bilder/ und schreibt werke.json (Metadaten für den Generator).

Nur Python-Standardbibliothek, keine Abhängigkeiten.
Undokumentierte Apple-Schnittstelle — bei Änderungen bricht der Sync mit
Fehlermeldung ab; die zuletzt gebaute Seite bleibt davon unberührt.
"""
import json
import os
import sys
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
BILDER = os.path.join(HERE, "bilder")
WERKE_JSON = os.path.join(HERE, "werke.json")
UA = "Mozilla/5.0 (renate-landt.de Galerie-Sync)"


def base62(c: str) -> int:
    if c.isdigit():
        return int(c)
    if c.isupper():
        return ord(c) - ord("A") + 10
    return ord(c) - ord("a") + 36


def post(host: str, token: str, path: str, body: dict):
    url = f"https://{host}/{token}/sharedstreams/{path}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "text/plain", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None


def fetch_album(token: str):
    """Webstream + Asset-URLs eines Albums holen. Folgt dem 330-Redirect."""
    host = f"p{base62(token[0]):02d}-sharedstreams.icloud.com"
    status, data = post(host, token, "webstream", {"streamCtag": None})
    if status == 330 and data and "X-Apple-MMe-Host" in data:
        host = data["X-Apple-MMe-Host"]
        status, data = post(host, token, "webstream", {"streamCtag": None})
    if status != 200 or not data or "photos" not in data:
        raise RuntimeError(f"Album {token}: webstream fehlgeschlagen (HTTP {status})")

    photos = data["photos"]
    guids = [p["photoGuid"] for p in photos]
    items = {}
    # Asset-URLs in Häppchen holen (Apple begrenzt die Anfragegröße)
    for i in range(0, len(guids), 25):
        status, assets = post(host, token, "webasseturls", {"photoGuids": guids[i:i + 25]})
        if status != 200 or not assets:
            raise RuntimeError(f"Album {token}: webasseturls fehlgeschlagen (HTTP {status})")
        items.update(assets.get("items", {}))
    return data.get("streamName") or token, photos, items


def best_derivative(photo: dict):
    """Größtes Bild-Derivat (Videos: Poster wäre möglich, wird hier übersprungen)."""
    best = None
    for deriv in photo.get("derivatives", {}).values():
        try:
            w = int(deriv.get("width") or 0)
        except (TypeError, ValueError):
            continue
        if best is None or w > best[0]:
            best = (w, deriv)
    return best[1] if best else None


def main():
    with open(os.path.join(HERE, "alben.json")) as f:
        config = json.load(f)

    os.makedirs(BILDER, exist_ok=True)
    vorhandene = set(os.listdir(BILDER))
    werke = []
    kategorien = []  # Reihenfolge = Reihenfolge in alben.json
    aktuelle_dateien = set()
    fehler = []

    for album in config["alben"]:
        token = album["token"]
        try:
            name, photos, items = fetch_album(token)
        except RuntimeError as e:
            fehler.append(str(e))
            continue
        kategorie = album.get("kategorie") or name
        if kategorie not in kategorien:
            kategorien.append(kategorie)
        print(f"Album '{name}' ({token}): {len(photos)} Fotos, Kategorie '{kategorie}'")

        for p in photos:
            deriv = best_derivative(p)
            if not deriv:
                continue
            checksum = deriv.get("checksum")
            asset = items.get(checksum)
            guid = p["photoGuid"]
            fname = f"{guid}.jpg"
            aktuelle_dateien.add(fname)
            if fname not in vorhandene:
                if not asset:
                    fehler.append(f"{guid}: keine Asset-URL")
                    continue
                url = f"https://{asset['url_location']}{asset['url_path']}"
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as r:
                    blob = r.read()
                with open(os.path.join(BILDER, fname), "wb") as f:
                    f.write(blob)
                print(f"  neu geladen: {fname} ({len(blob)//1024} KB)")
            werke.append({
                "datei": fname,
                "titel": (p.get("caption") or "").strip() or "Ohne Titel",
                "kategorie": kategorie,
                "aufgenommen": p.get("dateCreated"),
                "eingestellt": p.get("batchDateCreated"),
                "breite": int(deriv.get("width") or 0),
                "hoehe": int(deriv.get("height") or 0),
            })

    if not werke and fehler:
        # Kompletter Fehlschlag: nichts anfassen, laut scheitern.
        print("SYNC FEHLGESCHLAGEN:\n" + "\n".join(fehler), file=sys.stderr)
        sys.exit(1)

    # Nicht mehr im Album vorhandene Bilder entfernen
    for alt in vorhandene - aktuelle_dateien:
        os.remove(os.path.join(BILDER, alt))
        print(f"  entfernt (nicht mehr im Album): {alt}")

    # Neueste zuerst innerhalb jeder Kategorie
    werke.sort(key=lambda w: (w["eingestellt"] or "", w["aufgenommen"] or ""), reverse=True)

    with open(WERKE_JSON, "w") as f:
        json.dump({"kategorien": kategorien, "werke": werke}, f, ensure_ascii=False, indent=1)
    print(f"{len(werke)} Werke -> werke.json")
    if fehler:
        print("Warnungen:\n" + "\n".join(fehler), file=sys.stderr)


if __name__ == "__main__":
    main()
