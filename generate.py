#!/usr/bin/env python3
"""Generator: baut aus werke.json + seite/inhalte.json die statische Galerie
nach public/. Design: Dunkel als Standard, Hell/Dunkel-Umschalter, Lichthof
beim Überfahren, Übersicht (Raster) für 'Alle', Rundgang je Kategorie."""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")

with open(os.path.join(HERE, "werke.json")) as f:
    daten = json.load(f)
werke = daten["werke"]
with open(os.path.join(HERE, "seite", "inhalte.json")) as f:
    inhalte = json.load(f)

# Kategorien in Album-Reihenfolge (aus alben.json via sync.py);
# nur Kategorien mit mindestens einem Werk erscheinen in der Navigation.
vorgabe = daten.get("kategorien") or []
vorhandene_kats = {w["kategorie"] for w in werke}
kategorien = [k for k in vorgabe if k in vorhandene_kats]
for w in werke:
    if w["kategorie"] not in kategorien:
        kategorien.append(w["kategorie"])

works_js = json.dumps([
    {"src": f"bilder/{w['datei']}", "title": w["titel"], "cat": w["kategorie"],
     "w": w["breite"], "h": w["hoehe"]}
    for w in werke
], ensure_ascii=False)

CSS = """
:root{
  --bg:#faf8f4;--ink:#2a2723;--muted:#8a8378;--line:#e6e0d6;--chip:#efe9df;
  --lbbg:rgba(20,17,14,.93);--shadow:rgba(60,50,40,.16);--accent:#8c5a3c;
}
body[data-theme="dunkel"]{
  --bg:#201d1b;--ink:#e9e3d9;--muted:#9a938a;--line:#38332f;--chip:#332f2b;
  --lbbg:rgba(10,8,7,.95);--shadow:rgba(0,0,0,.55);
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:Georgia,'Times New Roman',serif;
  -webkit-font-smoothing:antialiased;transition:background .3s,color .3s}
#kopf{position:sticky;top:0;z-index:40;background:var(--bg);
  border-bottom:1px solid var(--line);transition:background .3s}
header{text-align:center;padding:34px 24px 4px}
h1{font-weight:normal;font-size:clamp(28px,5vw,44px);letter-spacing:.06em}
.sub{color:var(--muted);font-style:italic;margin-top:8px;font-size:17px}
nav{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;padding:18px 16px 14px}
nav button{background:none;border:none;font:inherit;font-size:15px;color:var(--muted);
  padding:8px 14px;cursor:pointer;border-radius:20px;transition:.2s}
nav button:hover{color:var(--ink)}
nav .on{color:var(--ink);background:var(--chip)}
nav .sep{color:var(--line);align-self:center}
footer{text-align:center;color:var(--muted);font-size:13px;padding:56px 16px 40px;
  border-top:1px solid var(--line);margin-top:72px}
footer a{color:var(--muted)}
#grid.uebersicht{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:56px 40px;max-width:1200px;margin:48px auto 0;padding:0 32px}
.uebersicht .card{cursor:pointer;text-align:center}
.uebersicht .frame{height:280px;display:flex;align-items:center;justify-content:center}
.uebersicht img{max-width:100%;max-height:280px;width:auto;height:auto;
  box-shadow:0 2px 14px var(--shadow);transition:transform .25s}
.uebersicht .card:hover img{transform:scale(1.015)}
.card .t{margin-top:16px;font-size:17px;font-style:italic}
.card .c{color:var(--muted);font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;margin-top:4px}
#grid.rundgang{max-width:1000px;margin:24px auto 0;padding:0 24px;display:block}
.rundgang .card{cursor:pointer;text-align:center;padding:72px 0;border-bottom:1px solid var(--line)}
.rundgang .card:last-child{border-bottom:none}
.rundgang img{max-width:100%;max-height:76vh;width:auto;height:auto;
  box-shadow:0 6px 30px var(--shadow);transition:transform .3s}
.rundgang .card:hover img{transform:scale(1.008)}
.rundgang .t{margin-top:24px;font-size:21px}
@media(max-width:600px){
  #grid.uebersicht{gap:44px 24px;padding:0 20px}
  .uebersicht .frame{height:220px}.uebersicht img{max-height:220px}
  .rundgang .card{padding:48px 0}
  header{transition:padding .25s}h1{transition:font-size .25s}nav{transition:padding .25s}
  #kopf.mini header{padding:10px 24px 0}
  #kopf.mini h1{font-size:20px}
  #kopf.mini .sub{display:none}
  #kopf.mini nav{padding:6px 16px 10px}}
body[data-theme="dunkel"] #grid img{
  transition:transform .25s,box-shadow .35s ease;
  box-shadow:0 26px 60px rgba(0,0,0,.9),0 0 0 1px rgba(255,255,255,.10)}
body[data-theme="dunkel"] #grid .card:hover img{
  box-shadow:0 26px 60px rgba(0,0,0,.9),
             0 0 26px 7px rgba(255,236,205,.32),
             0 0 0 1px rgba(255,255,255,.12)}
#ueber{max-width:820px;margin:56px auto 0;padding:0 28px;display:none}
#ueber .kopf{display:flex;gap:40px;align-items:flex-start;flex-wrap:wrap}
#ueber .foto{width:240px;flex-shrink:0}
#ueber .foto img{width:100%;display:block;box-shadow:0 4px 20px var(--shadow)}
#ueber .bio{flex:1;min-width:260px;line-height:1.75;font-size:16.5px}
#ueber h2{font-weight:normal;font-size:26px;margin-bottom:18px}
#ueber .daten{margin-top:36px;line-height:2;font-size:15.5px}
#ueber .daten .jahr{display:inline-block;width:120px;color:var(--muted);white-space:nowrap}
.textseite{max-width:720px;margin:56px auto 0;padding:0 28px;display:none;line-height:1.8;font-size:15.5px}
.textseite h2{font-weight:normal;font-size:26px;margin-bottom:24px}
.textseite h3{font-weight:normal;font-size:18px;margin:28px 0 8px}
.textseite p{margin-bottom:14px}
.lb{position:fixed;inset:0;background:var(--lbbg);display:none;z-index:50;
  align-items:center;justify-content:center;flex-direction:column;padding:24px}
.lb.open{display:flex}
.lb img{max-width:92vw;max-height:78vh;box-shadow:0 12px 60px rgba(0,0,0,.5)}
.lb .cap{color:#e8e2d8;font-style:italic;margin-top:18px;font-size:18px;text-align:center}
.lb .cat{color:#9a938a;font-size:13px;margin-top:4px;letter-spacing:.08em;text-transform:uppercase}
.lb button{position:absolute;background:none;border:none;color:#cfc8bd;font-size:34px;cursor:pointer;padding:16px;line-height:1}
.lb button:hover{color:#fff}
.lb .x{top:10px;right:14px}.lb .prev{left:6px;top:50%;transform:translateY(-50%)}
.lb .next{right:6px;top:50%;transform:translateY(-50%)}
@media(max-width:600px){.lb .prev,.lb .next{top:auto;bottom:8px;transform:none}
 .lb .prev{left:24vw}.lb .next{right:24vw}}
#themes{position:fixed;bottom:14px;right:14px;background:var(--chip);border:1px solid var(--line);
  border-radius:24px;padding:6px 10px;display:flex;gap:4px;align-items:center;font-size:12px;z-index:60}
#themes span{color:var(--muted);margin-right:4px;font-style:italic}
#themes button{background:none;border:none;font:inherit;color:var(--muted);cursor:pointer;padding:4px 8px;border-radius:14px}
#themes button.on{background:var(--bg);color:var(--ink)}
"""

nav_cats = "".join(f'<button data-cat="{k}">{k}</button>' for k in kategorien)
lebenslauf = "".join(
    f'<div><span class="jahr">{jahr}</span> {text}</div>'
    for jahr, text in inhalte["lebenslauf"])
imp = inhalte["impressum"]
ds = inhalte["datenschutz"]

HTML = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{inhalte['titel']} — {inhalte['untertitel']}. Galerie.">
<title>{inhalte['titel']} — {inhalte['untertitel']}</title>
<style>{CSS}</style>
</head>
<body data-theme="dunkel">
<div id="kopf">
<header>
  <h1>{inhalte['titel']}</h1>
  <div class="sub">{inhalte['untertitel']}</div>
</header>
<nav>
  <button data-cat="Alle" class="on">Alle</button>
  {nav_cats}
  <span class="sep">·</span>
  <button id="nav-ueber">Über die Künstlerin</button>
</nav>
</div>

<div id="grid" class="uebersicht"></div>

<section id="ueber">
  <div class="kopf">
    <div class="foto"><img src="portrait.jpg" alt="{inhalte['titel']}"></div>
    <div class="bio">
      <h2>Über die Künstlerin</h2>
      <p>{inhalte['ueber_absatz']}</p>
    </div>
  </div>
  <div class="daten">{lebenslauf}</div>
</section>

<section id="impressum" class="textseite">
  <h2>Impressum</h2>
  <h3>Angaben gemäß § 5 DDG</h3>
  <p>{imp['name']}<br>{imp['strasse']}<br>{imp['plz_ort']}<br>E-Mail: {imp['email']}</p>
  <h3>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h3>
  <p>{imp['name']}, Anschrift wie oben.</p>
  <h3>Art des Angebots</h3>
  <p>Diese Website ist ein privates, nicht-kommerzielles Angebot. Es werden keine
  Waren oder Dienstleistungen angeboten.</p>
  <h3>Urheberrecht</h3>
  <p>Alle abgebildeten Werke und Fotografien: © {imp.get('urheberin', imp['name'])}. Jede Vervielfältigung,
  Bearbeitung oder anderweitige Nutzung — auch auszugsweise — bedarf der vorherigen
  ausdrücklichen Zustimmung.</p>
</section>

<section id="datenschutz" class="textseite">
  <h2>Datenschutzerklärung</h2>
  <h3>Verantwortlicher</h3>
  <p>{imp['name']}, {imp['strasse']}, {imp['plz_ort']}, E-Mail: {imp['email']}</p>
  <h3>Grundsatz</h3>
  <p>Diese Website dient ausschließlich der Präsentation künstlerischer Arbeiten.
  Sie verwendet keine Cookies, keine Analyse- oder Tracking-Dienste, keine
  Kontaktformulare und keine Einbindungen von Drittanbietern (etwa Schriften oder
  Karten von fremden Servern). Es werden von uns keine personenbezogenen Daten
  erhoben, gespeichert oder weitergegeben.</p>
  <h3>Server-Logdateien</h3>
  <p>Beim Aufruf der Website verarbeitet der Hosting-Anbieter {ds['hoster']}
  automatisch technische Zugriffsdaten (u.&#8201;a. IP-Adresse, Datum und Uhrzeit des
  Abrufs, aufgerufene Seite, Browsertyp). Diese Verarbeitung ist für den technischen
  Betrieb und die Sicherheit der Website erforderlich (Art. 6 Abs. 1 lit. f DSGVO).
  Die Daten werden nicht mit anderen Datenquellen zusammengeführt.</p>
  <h3>Ihre Rechte</h3>
  <p>Sie haben nach der DSGVO das Recht auf Auskunft, Berichtigung, Löschung,
  Einschränkung der Verarbeitung und Widerspruch sowie das Recht auf Beschwerde bei
  einer Aufsichtsbehörde — zuständig ist die Berliner Beauftragte für Datenschutz
  und Informationsfreiheit.</p>
  <p>Stand: {ds['stand']}</p>
</section>

<div class="lb" id="lb">
  <button class="x" aria-label="Schließen">&times;</button>
  <button class="prev" aria-label="Vorheriges">&#8249;</button>
  <img alt="">
  <div class="cap"></div><div class="cat"></div>
  <button class="next" aria-label="Nächstes">&#8250;</button>
</div>

<div id="themes"><span>Ansicht:</span>
  <button data-t="dunkel" class="on">Dunkel</button>
  <button data-t="warm">Hell</button>
</div>

<footer>
  <a href="#" id="link-impressum">Impressum</a> &nbsp;·&nbsp;
  <a href="#" id="link-datenschutz">Datenschutz</a>
</footer>

<script>
const WORKS = {works_js};
let current = "Alle", visible = [], idx = 0;
const grid = document.getElementById('grid');
const ueber = document.getElementById('ueber');
const lb = document.getElementById('lb');
const lbImg = lb.querySelector('img'), lbCap = lb.querySelector('.cap'), lbCat = lb.querySelector('.cat');

function itemUebersicht(w,vi){{return `<div class="card" data-vi="${{vi}}">
  <div class="frame"><img src="${{w.src}}" width="${{w.w}}" height="${{w.h}}" alt="${{w.title}}" loading="lazy"></div>
  <div class="t">${{w.title}}</div><div class="c">${{w.cat}}</div></div>`}}
function itemRundgang(w,vi){{return `<div class="card" data-vi="${{vi}}">
  <img src="${{w.src}}" width="${{w.w}}" height="${{w.h}}" alt="${{w.title}}" loading="lazy">
  <div class="t">${{w.title}}</div><div class="c">${{w.cat}}</div></div>`}}

function hideSections(){{
  ueber.style.display='none';
  document.getElementById('impressum').style.display='none';
  document.getElementById('datenschutz').style.display='none';
}}
function render(){{
  hideSections(); grid.style.display='';
  const uebersicht = current==='Alle';
  grid.className = uebersicht ? 'uebersicht' : 'rundgang';
  visible = WORKS.map((w,i)=>({{...w,i}})).filter(w=>uebersicht||w.cat===current);
  const fn = uebersicht ? itemUebersicht : itemRundgang;
  grid.innerHTML = visible.map((w,vi)=>fn(w,vi)).join('');
  grid.querySelectorAll('[data-vi]').forEach(el=>{{
    el.addEventListener('click',()=>open(parseInt(el.dataset.vi)));
  }});
  window.scrollTo({{top:0}});
}}
function open(vi){{ idx=vi; show(); lb.classList.add('open'); document.body.style.overflow='hidden'; }}
function close(){{ lb.classList.remove('open'); document.body.style.overflow=''; }}
function show(){{ const w=visible[idx]; lbImg.src=w.src; lbCap.textContent=w.title; lbCat.textContent=w.cat; }}
function step(d){{ idx=(idx+d+visible.length)%visible.length; show(); }}
lb.querySelector('.x').onclick=close;
lb.querySelector('.prev').onclick=e=>{{e.stopPropagation();step(-1)}};
lb.querySelector('.next').onclick=e=>{{e.stopPropagation();step(1)}};
lb.onclick=e=>{{ if(e.target===lb) close(); }};
document.addEventListener('keydown',e=>{{
  if(!lb.classList.contains('open'))return;
  if(e.key==='Escape')close(); if(e.key==='ArrowLeft')step(-1); if(e.key==='ArrowRight')step(1);
}});
document.querySelectorAll('nav [data-cat]').forEach(b=>{{
  b.onclick=()=>{{ current=b.dataset.cat; setActive(b); render(); }};
}});
document.getElementById('nav-ueber').onclick=function(){{
  setActive(this); grid.style.display='none'; hideSections();
  ueber.style.display='block'; window.scrollTo({{top:0}});
}};
['impressum','datenschutz'].forEach(id=>{{
  document.getElementById('link-'+id).onclick=e=>{{
    e.preventDefault(); grid.style.display='none'; hideSections();
    document.getElementById(id).style.display='block';
    setActive(null); window.scrollTo({{top:0}});
  }};
}});
function setActive(b){{ document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('on',x===b)); }}
document.querySelectorAll('#themes button[data-t]').forEach(b=>{{
  b.onclick=()=>{{ document.body.dataset.theme=b.dataset.t;
    document.querySelectorAll('#themes button[data-t]').forEach(x=>x.classList.toggle('on',x===b)); }};
}});
addEventListener('scroll',()=>{{
  document.getElementById('kopf').classList.toggle('mini', scrollY>40);
}},{{passive:true}});
render();
</script>
</body>
</html>"""


def main():
    if os.path.isdir(PUBLIC):
        shutil.rmtree(PUBLIC)
    os.makedirs(os.path.join(PUBLIC, "bilder"))
    for w in werke:
        shutil.copy2(os.path.join(HERE, "bilder", w["datei"]),
                     os.path.join(PUBLIC, "bilder", w["datei"]))
    portrait = os.path.join(HERE, "seite", "portrait.jpg")
    if os.path.exists(portrait):
        shutil.copy2(portrait, os.path.join(PUBLIC, "portrait.jpg"))
    with open(os.path.join(PUBLIC, "index.html"), "w") as f:
        f.write(HTML)
    # Eigene Domain für GitHub Pages
    cname = os.path.join(HERE, "CNAME")
    if os.path.exists(cname):
        shutil.copy2(cname, os.path.join(PUBLIC, "CNAME"))
    print(f"public/ gebaut: {len(werke)} Werke, {len(kategorien)} Kategorien")


if __name__ == "__main__":
    main()
